# Chatbot Streamlit UI

Internal authenticated UI for Maintainer's Copilot.

Features:
- Login/register through FastAPI.
- Full chat page using `/chat`.
- Memory inspector using `/chat/memory`.
- Admin widget creation using `/widgets`.
- Generated embed snippet for host apps.

Run locally:

```bash
API_BASE_URL=http://localhost:8000 streamlit run chatbot/streamlit_app.py
```
