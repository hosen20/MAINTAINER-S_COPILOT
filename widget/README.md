# Maintainer's Copilot React Widget

Embeddable React widget built with Vite.

Features:
- Collapsed bubble.
- Expandable chat panel.
- Runtime config from `/widgets/public/{widget_id}`.
- Login/register against the backend.
- Chat via `/chat`.
- `postMessage` resize events to the host.

Local dev:

```bash
cd widget
npm install
npm run dev
```

Example URL:

```text
http://localhost:5173?widget_id=YOUR_WIDGET_ID&api_base_url=http://localhost:8000
```
