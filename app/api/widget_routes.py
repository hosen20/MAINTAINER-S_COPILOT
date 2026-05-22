from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.api.auth_routes import get_current_user
from app.api.deps import get_session
from app.domain.auth import AuthenticatedUser
from app.domain.widget import (
    PublicWidgetConfig,
    WidgetConfigCreate,
    WidgetConfigRead,
    WidgetConfigUpdate,
)
from app.infra.settings import get_settings
from app.services.widget_service import WidgetService


router = APIRouter()


@router.post("", response_model=WidgetConfigRead)
def create_widget(
    payload: WidgetConfigCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WidgetConfigRead:
    return WidgetService(session).create(actor=current_user, payload=payload)


@router.get("/{widget_id}", response_model=WidgetConfigRead)
def get_widget_admin(
    widget_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WidgetConfigRead:
    return WidgetService(session).get_admin(actor=current_user, widget_id=widget_id)


@router.patch("/{widget_id}", response_model=WidgetConfigRead)
def update_widget(
    widget_id: str,
    payload: WidgetConfigUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WidgetConfigRead:
    return WidgetService(session).update(
        actor=current_user,
        widget_id=widget_id,
        payload=payload,
    )


@router.get("/public/{widget_id}", response_model=PublicWidgetConfig)
def get_public_widget(
    widget_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> PublicWidgetConfig:
    return WidgetService(session).get_public(widget_id)


@router.get("/asset/widget.js", include_in_schema=False)
def widget_loader() -> Response:
    settings = get_settings()

    script = f"""
(function () {{
  var script = document.currentScript;
  var widgetId = script && script.dataset.widgetId;
  var apiBaseUrl = (script && script.dataset.apiBaseUrl) || "{settings.public_api_base_url}";

  if (!widgetId) {{
    console.error("Maintainer's Copilot: missing data-widget-id");
    return;
  }}

  var frameUrl =
    apiBaseUrl.replace(/\\/$/, "") +
    "/widget-frame?widget_id=" +
    encodeURIComponent(widgetId) +
    "&api_base_url=" +
    encodeURIComponent(apiBaseUrl);

  var iframe = document.createElement("iframe");
  iframe.src = frameUrl;
  iframe.title = "Maintainer's Copilot";
  iframe.style.position = "fixed";
  iframe.style.right = "20px";
  iframe.style.bottom = "20px";
  iframe.style.width = "96px";
  iframe.style.height = "96px";
  iframe.style.border = "0";
  iframe.style.zIndex = "2147483647";
  iframe.style.background = "transparent";
  iframe.style.display = "block";
  iframe.style.overflow = "hidden";
  iframe.setAttribute("allow", "clipboard-write");

  window.addEventListener("message", function (event) {{
    var data = event.data || {{}};

    if (data.type !== "maintainers-copilot:resize") {{
      return;
    }}

    var open = Boolean(data.open);
    var requestedWidth = Number(data.width || (open ? 420 : 96));
    var requestedHeight = Number(data.height || (open ? 640 : 96));

    var maxWidth = Math.max(320, window.innerWidth - 32);
    var maxHeight = Math.max(420, window.innerHeight - 32);

    if (open) {{
      iframe.style.width = Math.min(Math.max(requestedWidth, 420), maxWidth) + "px";
      iframe.style.height = Math.min(Math.max(requestedHeight, 640), maxHeight) + "px";
    }} else {{
      iframe.style.width = "96px";
      iframe.style.height = "96px";
    }}
  }});

  document.body.appendChild(iframe);
}})();
"""

    return Response(
        content=script,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/frame", include_in_schema=False)
def widget_frame(
    widget_id: Annotated[str, Query()],
    session: Annotated[Session, Depends(get_session)],
    api_base_url: str | None = None,
) -> HTMLResponse:
    settings = get_settings()
    allowed_origins = WidgetService(session).get_allowed_origins(widget_id)

    frame_ancestors = " ".join(allowed_origins) if allowed_origins else "'none'"
    widget_url = settings.widget_app_url.rstrip("/")
    api_url = (api_base_url or settings.public_api_base_url).rstrip("/")

    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Maintainer's Copilot Widget Frame</title>
    <style>
      html,
      body {{
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        background: transparent;
        overflow: hidden;
      }}

      iframe {{
        width: 100%;
        height: 100%;
        border: 0;
        background: transparent;
        display: block;
      }}
    </style>
  </head>

  <body>
    <iframe
      src="{widget_url}?widget_id={widget_id}&api_base_url={api_url}"
      title="Maintainer's Copilot Widget"
      allow="clipboard-write"
    ></iframe>

    <script>
      window.addEventListener("message", function(event) {{
        if (event.data && event.data.type === "maintainers-copilot:resize") {{
          window.parent.postMessage(event.data, "*");
        }}
      }});
    </script>
  </body>
</html>
"""

    return HTMLResponse(
        content=html,
        headers={
            "Content-Security-Policy": f"frame-ancestors {frame_ancestors}",
            "Cache-Control": "no-store",
        },
    )
