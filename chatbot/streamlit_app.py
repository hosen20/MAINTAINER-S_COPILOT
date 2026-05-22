from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Maintainer's Copilot", page_icon="🛠️", layout="wide")


def api_request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return requests.request(
        method,
        f"{API_BASE_URL}{path}",
        headers=headers,
        json=json_body,
        params=params,
        timeout=180,
    )


def login(email: str, password: str) -> None:
    response = api_request(
        "POST",
        "/auth/login",
        json_body={"email": email, "password": password},
    )
    if response.ok:
        payload = response.json()
        st.session_state.token = payload["access_token"]
        st.session_state.user = payload["user"]
        st.rerun()

    st.error(response.text)


def register(email: str, password: str) -> None:
    response = api_request(
        "POST",
        "/auth/register",
        json_body={"email": email, "password": password},
    )
    if response.ok:
        payload = response.json()
        st.session_state.token = payload["access_token"]
        st.session_state.user = payload["user"]
        st.rerun()

    st.error(response.text)


def logout() -> None:
    for key in ["token", "user", "messages", "conversation_id"]:
        st.session_state.pop(key, None)
    st.rerun()


def require_login() -> bool:
    if "token" in st.session_state and "user" in st.session_state:
        return True

    st.title("Maintainer's Copilot")
    st.caption("Internal authenticated Streamlit UI for chat, memory, and widget administration.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login-form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            login(email, password)

    with tab_register:
        with st.form("register-form"):
            email = st.text_input("Email", key="register-email")
            password = st.text_input("Password", type="password", key="register-password")
            submitted = st.form_submit_button("Register")

        if submitted:
            register(email, password)

    return False


def render_sidebar() -> None:
    user = st.session_state["user"]

    with st.sidebar:
        st.subheader("Account")
        st.write(user["email"])
        st.caption(f"Role: {user['role']}")

        if st.button("Logout"):
            logout()

        st.divider()
        st.caption(f"API: {API_BASE_URL}")


def render_chat_page() -> None:
    st.header("Chat")

    token = st.session_state["token"]
    st.session_state.setdefault("messages", [])

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about triage, docs, resolved issues, memory, or project setup...")

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = api_request(
        "POST",
        "/chat",
        token=token,
        json_body={
            "message": prompt,
            "conversation_id": st.session_state.get("conversation_id"),
        },
    )

    if not response.ok:
        with st.chat_message("assistant"):
            st.error(response.text)
        return

    payload = response.json()
    st.session_state.conversation_id = payload["conversation_id"]

    answer = payload["answer"]

    with st.chat_message("assistant"):
        st.markdown(answer)

        if payload.get("used_tools"):
            with st.expander("Used tools"):
                st.json(payload["used_tools"])

    st.session_state.messages.append({"role": "assistant", "content": answer})


def render_memory_page() -> None:
    st.header("Memory inspector")

    token = st.session_state["token"]

    with st.form("write-memory-form"):
        memory_type = st.selectbox("Memory type", ["episodic", "semantic", "procedural"])
        content = st.text_area("Content")
        submitted = st.form_submit_button("Write memory")

    if submitted:
        response = api_request(
            "POST",
            "/chat/memory",
            token=token,
            json_body={
                "memory_type": memory_type,
                "content": content,
            },
        )

        if response.ok:
            st.success("Memory written.")
        else:
            st.error(response.text)

    response = api_request("GET", "/chat/memory", token=token, params={"limit": 50})

    if not response.ok:
        st.error(response.text)
        return

    memories = response.json()

    st.subheader("Recent memories")

    if not memories:
        st.info("No memories yet.")
        return

    for memory in memories:
        with st.container(border=True):
            st.caption(f"#{memory['id']} · {memory['memory_type']} · {memory['created_at']}")
            st.write(memory["content"])


def render_widget_admin_page() -> None:
    st.header("Widget configuration")

    token = st.session_state["token"]
    user = st.session_state["user"]

    if user["role"] != "admin":
        st.warning("Admin role required.")
        return

    with st.form("create-widget-form"):
        primary_color = st.color_picker("Primary color", value="#2563eb")
        greeting = st.text_input("Greeting", value="Hi 👋 How can I help?")
        enabled_tools_text = st.text_input(
            "Enabled tools",
            value="classifier,ner,summarizer,rag,write_memory",
        )
        allowed_origins_text = st.text_area(
            "Allowed origins, one per line",
            value="http://localhost:8080\nhttp://localhost:5173",
        )
        submitted = st.form_submit_button("Create widget")

    if submitted:
        response = api_request(
            "POST",
            "/widgets",
            token=token,
            json_body={
                "theme": {
                    "primary_color": primary_color,
                    "position": "bottom-right",
                },
                "greeting": greeting,
                "enabled_tools": [
                    x.strip()
                    for x in enabled_tools_text.split(",")
                    if x.strip()
                ],
                "allowed_origins": [
                    x.strip()
                    for x in allowed_origins_text.splitlines()
                    if x.strip()
                ],
            },
        )

        if not response.ok:
            st.error(response.text)
            return

        widget = response.json()

        st.success("Widget created.")
        st.json(widget)

        snippet = (
            f'<script src="{API_BASE_URL}/widget.js" '
            f'data-widget-id="{widget["widget_id"]}" '
            f'data-api-base-url="{API_BASE_URL}"></script>'
        )

        st.subheader("Embed snippet")
        st.code(snippet, language="html")


if require_login():
    render_sidebar()

    page = st.sidebar.radio("Navigation", ["Chat", "Memory inspector", "Widget admin"])

    if page == "Chat":
        render_chat_page()
    elif page == "Memory inspector":
        render_memory_page()
    else:
        render_widget_admin_page()
