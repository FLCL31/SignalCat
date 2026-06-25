from __future__ import annotations

import os

from dashboard.app import CSS, THEME, build_app


demo = build_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
    share = os.environ.get("GRADIO_SHARE", "false").lower() in {"1", "true", "yes", "on"}
    demo.launch(server_name="0.0.0.0", server_port=port, share=share, theme=THEME, css=CSS)
