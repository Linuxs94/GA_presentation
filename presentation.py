from __future__ import annotations

import argparse

from apps.interactive_viewer import launch

try:
    from visualizations.build_all import main as build_assets
except ModuleNotFoundError:
    build_assets = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GA presentation runner")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="launch the Gradio + Plotly step-by-step viewer",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="host used by the interactive viewer",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="port used by the interactive viewer",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.interactive:
        launch().launch(server_name=args.host, server_port=args.port)
    else:
        if build_assets is None:
            raise ModuleNotFoundError(
                "visualizations.build_all is not available in this branch. "
                "Use --interactive to launch the app."
            )
        build_assets()
