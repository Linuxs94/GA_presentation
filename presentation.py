from __future__ import annotations

import argparse

from apps.interactive_viewer import launch
from visualizations.build_all import main as build_assets


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
        build_assets()
