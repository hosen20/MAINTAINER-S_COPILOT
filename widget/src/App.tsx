import { FormEvent, useEffect, useMemo, useState } from "react";

type WidgetConfig = { widget_id: string; theme: string; greeting: string; enabled_tools: string[]; allowed_origins: string[] };
type ChatMessage = { role: "assistant" | "user"; content: string };
function qp(name: string): string | null { return new URLSearchParams(window.location.search).get(name); }
function postResize(open: boolean) { window.parent.postMessage({ type: "maintainers-copilot:resize", open, height: open ? 640 : 96, width: open ? 420 : 96 }, "*"); }

export default function App() {
  const widgetId = qp("widget_id") || "demo";
  const apiBaseUrl = (qp("api_base_url") || window.location.origin).replace(/\/$/, "");
  const [config, setConfig] = useState<WidgetConfig | null>(null);
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const primaryColor = config?.theme || "#2563eb";
  const authed = useMemo(() => token.trim().length > 0, [token]);

  useEffect(() => { postResize(open); }, [open]);
  useEffect(() => {
    async function loadConfig() {
      try {
        const response = await fetch(`${apiBaseUrl}/widgets/public/${widgetId}`);
        if (!response.ok) throw new Error(await response.text());
        const payload = await response.json();
        setConfig(payload);
        setMessages([{ role: "assistant", content: payload.greeting || "Hi 👋 How can I help?" }]);
      } catch (err) { setError(err instanceof Error ? err.message : "Could not load widget config."); }
    }
    loadConfig();
  }, [apiBaseUrl, widgetId]);

  async function loginOrRegister(path: "/auth/login" | "/auth/register") {
    setError(""); setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: authEmail, password: authPassword }) });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setToken(payload.access_token);
    } catch (err) { setError(err instanceof Error ? err.message : "Authentication failed."); }
    finally { setLoading(false); }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput(""); setError(""); setLoading(true);
    const nextMessages = [...messages, { role: "user" as const, content: trimmed }];
    setMessages(nextMessages);
    try {
      const response = await fetch(`${apiBaseUrl}/chat`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ message: trimmed, conversation_id: conversationId }) });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setConversationId(payload.conversation_id);
      setMessages([...nextMessages, { role: "assistant", content: payload.answer }]);
    } catch (err) { setError(err instanceof Error ? err.message : "Chat failed."); }
    finally { setLoading(false); }
  }

  if (!open) return <button className="mc-bubble" style={{ backgroundColor: primaryColor }} onClick={() => setOpen(true)} aria-label="Open Maintainer's Copilot">🛠️</button>;
  return <section className="mc-panel"><header className="mc-header" style={{ backgroundColor: primaryColor }}><div><strong>Maintainer's Copilot</strong><span>Issue triage assistant</span></div><button onClick={() => setOpen(false)} aria-label="Collapse widget">×</button></header>{error && <div className="mc-error">{error}</div>}{!authed ? <main className="mc-auth"><p>Login to chat with the copilot.</p><input value={authEmail} onChange={e => setAuthEmail(e.target.value)} placeholder="Email" type="email"/><input value={authPassword} onChange={e => setAuthPassword(e.target.value)} placeholder="Password" type="password"/><div className="mc-auth-actions"><button disabled={loading} onClick={() => loginOrRegister("/auth/login")}>Login</button><button disabled={loading} onClick={() => loginOrRegister("/auth/register")}>Register</button></div></main> : <><main className="mc-messages">{messages.map((m, i) => <article key={`${m.role}-${i}`} className={`mc-message ${m.role}`}>{m.content}</article>)}{loading && <article className="mc-message assistant">Thinking...</article>}</main><form className="mc-input" onSubmit={sendMessage}><input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about this project..."/><button disabled={loading} type="submit" style={{ backgroundColor: primaryColor }}>Send</button></form></>}</section>;
}
