# Demo Host

Tiny static host app that embeds Maintainer's Copilot with one script tag.

Run with Docker:

```bash
docker build -f demo/host/Dockerfile.host -t maintainers-host .
docker run --rm -p 8080:80 maintainers-host
```

Open `http://localhost:8080`.

Before demo:
- Create a widget config in Streamlit.
- Put `http://localhost:8080` in `allowed_origins`.
- Replace `data-widget-id="demo"` in `index.html` with the real widget id.
