from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ga_presentation.convex_hull import HullSnapshot, monotone_chain
from ga_presentation.datasets import (
    load_repo_polygons,
    regular_polygon,
    sample_gaussian_clusters,
    sample_polygon_boundary,
    sample_uniform_points,
    star_polygon,
)
from ga_presentation.fortune import FortuneSnapshot, compute_voronoi
from ga_presentation.winding import build_winding_field, compute_bounds, polygon_edges, winding_trace


FIGURES_DIR = ROOT / "report" / "figures"
ANIMATIONS_DIR = ROOT / "report" / "animations"
SUMMARY_PATH = ROOT / "report" / "summary.json"


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ANIMATIONS_DIR.mkdir(parents=True, exist_ok=True)


def bounds_from_points(points: list[tuple[float, float]], padding: float = 1.0) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs) - padding, max(xs) + padding, min(ys) - padding, max(ys) + padding


def set_axes(ax: plt.Axes, title: str, bounds: tuple[float, float, float, float]) -> None:
    min_x, max_x, min_y, max_y = bounds
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.grid(True, alpha=0.2)


def draw_points(ax: plt.Axes, points: list[tuple[float, float]], color: str = "black", size: float = 18.0) -> None:
    if not points:
        return
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    ax.scatter(xs, ys, color=color, s=size, zorder=4)


def draw_point_labels(
    ax: plt.Axes,
    points: list[tuple[float, float]],
    prefix: str = "p",
    color: str = "#333333",
    fontsize: int = 8,
) -> None:
    for index, point in enumerate(points):
        ax.text(point[0] + 0.08, point[1] + 0.08, f"{prefix}{index}", color=color, fontsize=fontsize)


def draw_polyline(ax: plt.Axes, points: list[tuple[float, float]], color: str, linewidth: float = 2.0) -> None:
    if len(points) < 2:
        return
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    ax.plot(xs, ys, color=color, linewidth=linewidth)


def add_state_box(ax: plt.Axes, title: str, lines: list[str]) -> None:
    text = title + "\n" + "\n".join(lines)
    ax.text(
        1.02,
        0.98,
        text,
        transform=ax.transAxes,
        va="top",
        fontsize=9,
        family="monospace",
        bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.4"},
    )


def choose_snapshots(items: list[object], count: int = 4) -> list[int]:
    if not items:
        return []
    raw = [0, len(items) // 3, (2 * len(items)) // 3, len(items) - 1]
    return sorted(set(index for index in raw if 0 <= index < len(items)))[:count]


def save_random_generators_figure(
    uniform_points: list[tuple[float, float]],
    gaussian_points: list[tuple[float, float]],
    boundary_points: list[tuple[float, float]],
    boundary_polygon: list[tuple[float, float]],
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    for ax, points, title in zip(
        axes,
        [uniform_points, gaussian_points, boundary_points],
        ["Uniform random points", "Gaussian clusters", "Points sampled on polygon boundary"],
    ):
        bounds = bounds_from_points(points, padding=1.0)
        set_axes(ax, title, bounds)
        draw_points(ax, points)
        if title.endswith("boundary"):
            draw_polyline(ax, boundary_polygon + [boundary_polygon[0]], "#1f77b4")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "random_input_modes.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_winding_figure(polygon: list[tuple[float, float]]) -> None:
    bounds = compute_bounds([polygon], margin=1.0)
    query_point = (0.2, 0.25)
    continuous_closed, xs, ys = build_winding_field(polygon, bounds, resolution=220, discrete=False, closed=True)
    discrete_closed, _, _ = build_winding_field(polygon, bounds, resolution=220, discrete=True, closed=True)
    continuous_open, _, _ = build_winding_field(polygon, bounds, resolution=220, discrete=False, closed=False)
    discrete_open, _, _ = build_winding_field(polygon, bounds, resolution=220, discrete=True, closed=False)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    min_x, max_x, min_y, max_y = bounds
    for ax, field, title, cmap, closed in (
        (axes[0][0], continuous_closed, "Closed polygon\nContinuous winding field", "coolwarm", True),
        (axes[0][1], discrete_closed, "Closed polygon\nInside / outside grid", "Greys", True),
        (axes[1][0], continuous_open, "Open polygon\nContinuous winding field", "coolwarm", False),
        (axes[1][1], discrete_open, "Open polygon\nInside / outside grid", "Greys", False),
    ):
        ax.imshow(field, origin="lower", extent=[xs[0], xs[-1], ys[0], ys[-1]], cmap=cmap, interpolation="nearest")
        set_axes(ax, title, bounds)
        path = polygon + [polygon[0]] if closed else polygon
        draw_polyline(ax, path, "black")
        draw_point_labels(ax, polygon, prefix="v")
        draw_points(ax, [query_point], color="#ff9f1c", size=28.0)
        add_state_box(
            ax,
            "Input / Process / Output",
            [
                f"mode = {'closed' if closed else 'open'}",
                f"query = ({query_point[0]:.1f}, {query_point[1]:.1f})",
                "process = sum signed angles",
                "output = field values",
            ],
        )
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "winding_input_process_output.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    trace_steps = winding_trace(query_point, polygon, closed=True)
    indices = choose_snapshots(trace_steps)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    for ax, index in zip(axes.flatten(), indices):
        step = trace_steps[index]
        set_axes(ax, f"Winding trace step {index + 1}", bounds)
        draw_polyline(ax, polygon + [polygon[0]], "black")
        draw_point_labels(ax, polygon, prefix="v")
        draw_points(ax, [query_point], color="#ff9f1c", size=32.0)
        ax.plot([query_point[0], step["start"][0]], [query_point[1], step["start"][1]], color="#ef476f", linewidth=1.6)
        ax.plot([query_point[0], step["end"][0]], [query_point[1], step["end"][1]], color="#118ab2", linewidth=1.6)
        ax.plot([step["start"][0], step["end"][0]], [step["start"][1], step["end"][1]], color="#06d6a0", linewidth=2.2)
        add_state_box(
            ax,
            "Current State",
            [
                f"edge = e{step['edge_index']}",
                f"angle += {step['angle']:.3f}",
                f"winding = {step['winding']:.3f}",
                "phase = accumulate edge contribution",
            ],
        )
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "winding_trace_snapshots.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def render_hull_snapshot(ax: plt.Axes, points: list[tuple[float, float]], snapshot: HullSnapshot, bounds: tuple[float, float, float, float]) -> None:
    ax.clear()
    set_axes(ax, f"Graham scan: {snapshot.action}", bounds)
    draw_points(ax, points)
    draw_point_labels(ax, points)
    if snapshot.stack:
        draw_polyline(ax, snapshot.stack, "#d62728", linewidth=2.4)
    draw_points(ax, [snapshot.candidate], color="#ff9f1c", size=36.0)
    point_names = {point: f"p{index}" for index, point in enumerate(points)}
    add_state_box(
        ax,
        "Current State",
        [
            f"candidate = {point_names.get(snapshot.candidate, '?')}",
            f"action = {snapshot.action}",
            "stack = [" + ", ".join(point_names.get(point, "?") for point in snapshot.stack) + "]",
            "phase = compare / push / pop",
        ],
    )


def save_convex_hull_assets(points: list[tuple[float, float]]) -> tuple[list[tuple[float, float]], list[HullSnapshot]]:
    hull, snapshots = monotone_chain(points)
    bounds = bounds_from_points(points, padding=1.0)
    indices = choose_snapshots(snapshots)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for ax, index in zip(axes.flatten(), indices):
        render_hull_snapshot(ax, points, snapshots[index], bounds)
    if hull:
        draw_polyline(axes.flatten()[-1], hull + [hull[0]], "#1b998b", linewidth=2.8)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "convex_hull_snapshots.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame_index: int) -> None:
        render_hull_snapshot(ax, points, snapshots[frame_index], bounds)
        if frame_index == len(snapshots) - 1 and hull:
            draw_polyline(ax, hull + [hull[0]], "#1b998b", linewidth=2.8)

    ani = animation.FuncAnimation(fig, update, frames=len(snapshots), interval=700, repeat_delay=1500)
    ani.save(ANIMATIONS_DIR / "convex_hull_growth.gif", writer=animation.PillowWriter(fps=2))
    plt.close(fig)
    return hull, snapshots


def render_fortune_snapshot(
    ax: plt.Axes,
    snapshot: FortuneSnapshot,
    points: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
    show_voronoi: bool = True,
    show_delaunay: bool = False,
    show_sweep: bool = True,
    show_beachline: bool = True,
) -> None:
    ax.clear()
    min_x, max_x, min_y, max_y = bounds
    title_bits = [f"Fortune sweep: {snapshot.event_kind}"]
    if snapshot.focus is not None:
        title_bits.append(f"focus=({snapshot.focus[0]:.1f}, {snapshot.focus[1]:.1f})")
    set_axes(ax, "\n".join(title_bits), bounds)
    draw_points(ax, points, color="#555555", size=18.0)
    draw_points(ax, snapshot.processed_sites, color="#1f77b4", size=20.0)

    if show_sweep:
        ax.axvline(snapshot.sweep_x, color="#d62728", linestyle="--", linewidth=1.5)
    if show_beachline:
        for polyline in snapshot.beachline:
            draw_polyline(ax, polyline, "#ff9f1c", linewidth=1.4)

    if snapshot.active_circle_center is not None and snapshot.active_circle_radius is not None:
        ax.add_patch(
            Circle(
                snapshot.active_circle_center,
                snapshot.active_circle_radius,
                fill=False,
                linestyle=":",
                linewidth=1.5,
                edgecolor="#8d99ae",
            )
        )
        draw_points(ax, snapshot.active_circle_sites, color="#8338ec", size=24.0)

    if show_voronoi:
        for start, end in snapshot.finished_segments:
            ax.plot([start[0], end[0]], [start[1], end[1]], color="#2a9d8f", linewidth=1.4)
        for start, end in snapshot.active_segments:
            ax.plot([start[0], end[0]], [start[1], end[1]], color="#52b788", linewidth=1.6, linestyle=":")

    if show_delaunay:
        for start, end in snapshot.delaunay_edges:
            ax.plot([start[0], end[0]], [start[1], end[1]], color="#264653", linewidth=1.2)
    draw_point_labels(ax, points)
    add_state_box(
        ax,
        "Current State",
        [
            f"phase = {snapshot.event_kind}",
            f"sweep_x = {snapshot.sweep_x:.2f}",
            f"processed = {len(snapshot.processed_sites)}",
            f"beach arcs = {len(snapshot.arc_sites)}",
            f"Voronoi edges = {len(snapshot.finished_segments)}",
            f"growing edges = {len(snapshot.active_segments)}",
            f"action = {snapshot.action_summary or snapshot.event_kind}",
        ],
    )


def save_fortune_assets(
    points: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
) -> tuple[list[FortuneSnapshot], FortuneSnapshot]:
    voronoi = compute_voronoi(points, bounds, capture=True)
    snapshots = voronoi.snapshots
    indices = choose_snapshots(snapshots)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, index in zip(axes.flatten(), indices):
        render_fortune_snapshot(ax, snapshots[index], points, bounds, show_voronoi=True, show_delaunay=False)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fortune_sweep_snapshots.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 7))
    ani = animation.FuncAnimation(
        fig,
        lambda frame_index: render_fortune_snapshot(ax, snapshots[frame_index], points, bounds, True, False),
        frames=len(snapshots),
        interval=450,
        repeat_delay=1500,
    )
    ani.save(ANIMATIONS_DIR / "fortune_sweep.gif", writer=animation.PillowWriter(fps=3))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 7))

    # def render_voronoi_only(frame_index: int) -> None:
    #     ax.clear()
    #     set_axes(ax, "Voronoi edges appearing", bounds)
    #     draw_points(ax, points, color="#555555", size=18.0)
    #     for start, end in snapshots[frame_index].finished_segments:
    #         ax.plot([start[0], end[0]], [start[1], end[1]], color="#2a9d8f", linewidth=1.4)
    #     for start, end in snapshots[frame_index].active_segments:
    #         ax.plot([start[0], end[0]], [start[1], end[1]], color="#52b788", linewidth=1.5, linestyle=":")

    # ani = animation.FuncAnimation(
    #     fig,
    #     render_voronoi_only,
    #     frames=len(snapshots),
    #     interval=450,
    #     repeat_delay=1500,
    # )
    # ani.save(ANIMATIONS_DIR / "voronoi_edges_appearing.gif", writer=animation.PillowWriter(fps=3))
    # plt.close(fig)

    # fig, ax = plt.subplots(figsize=(7, 7))
    # ani = animation.FuncAnimation(
    #     fig,
    #     lambda frame_index: render_fortune_snapshot(ax, snapshots[frame_index], points, bounds, False, True),
    #     frames=len(snapshots),
    #     interval=450,
    #     repeat_delay=1500,
    # )
    # ani.save(ANIMATIONS_DIR / "delaunay_dual_edges.gif", writer=animation.PillowWriter(fps=3))
    # plt.close(fig)

    final_snapshot = snapshots[-1]

    # fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    # render_fortune_snapshot(axes[0], final_snapshot, points, bounds, True, False, False, False)
    # axes[0].set_title("Output: final Voronoi edges")
    # render_fortune_snapshot(axes[1], final_snapshot, points, bounds, False, True, False, False)
    # axes[1].set_title("Output: Delaunay dual edges")
    # plt.tight_layout()
    # plt.savefig(FIGURES_DIR / "voronoi_and_delaunay_outputs.png", dpi=220, bbox_inches="tight")
    # plt.close(fig)

    duality_pairs = sorted(
        final_snapshot.voronoi_dual_pairs,
        key=lambda pair: np.hypot(
            pair["voronoi"][1][0] - pair["voronoi"][0][0],
            pair["voronoi"][1][1] - pair["voronoi"][0][1],
        ),
        reverse=True,
    )
    pair_count = min(4, len(duality_pairs))
    if pair_count:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        for ax, pair in zip(axes.flatten(), duality_pairs[:pair_count]):
            set_axes(ax, "Voronoi edge  <->  Delaunay dual edge", bounds)
            draw_points(ax, points, color="#444444", size=18.0)
            draw_point_labels(ax, points)
            for start, end in final_snapshot.finished_segments:
                ax.plot([start[0], end[0]], [start[1], end[1]], color="#b7e4c7", linewidth=1.0, alpha=0.7)
            for start, end in final_snapshot.delaunay_edges:
                ax.plot([start[0], end[0]], [start[1], end[1]], color="#adb5bd", linewidth=0.9, alpha=0.6)
            vor_start, vor_end = pair["voronoi"]
            dual_start, dual_end = pair["dual"]
            ax.plot([vor_start[0], vor_end[0]], [vor_start[1], vor_end[1]], color="#2a9d8f", linewidth=2.6)
            ax.plot([dual_start[0], dual_end[0]], [dual_start[1], dual_end[1]], color="#d62828", linewidth=2.2)
            add_state_box(
                ax,
                "Duality Step",
                [
                    "green = Voronoi edge",
                    "red = Delaunay dual edge",
                    "lecture 9 idea:",
                    "Voronoi bisector <-> Delaunay neighbor edge",
                ],
            )
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "delaunay_from_voronoi_duality.png", dpi=220, bbox_inches="tight")
        plt.close(fig)

    return snapshots, final_snapshot


def save_project_overview(polygons: dict[str, list[tuple[float, float]]]) -> None:
    square = regular_polygon((0.0, 0.0), 4.0, 4, angle_offset=np.pi / 4.0)
    star = star_polygon((0.0, 0.0), 2.1, 5.0, 5)
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))

    for ax, polygon, title in (
        (axes[0][0], square, "Static primitive input"),
        (axes[0][1], star, "Shape used for winding-number explanation"),
        (axes[1][0], polygons["p1"], "Repository polygon p1"),
        (axes[1][1], polygons["p2"], "Repository polygon p2"),
    ):
        bounds = bounds_from_points(polygon, padding=1.5 if title.startswith("Static") or title.startswith("Shape") else 30.0)
        set_axes(ax, title, bounds)
        draw_polyline(ax, polygon + [polygon[0]], "#1f77b4")
        draw_points(ax, polygon)
        draw_point_labels(ax, polygon, prefix="v")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "project_inputs.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_report(summary: dict[str, object]) -> None:
    report_text = f"""# GA Presentation Report

## Main Deliverable

The main teaching surface of this branch is the interactive viewer:

- [apps/interactive_viewer.py]("apps" / "interactive_viewer.py".as_posix())
- run with `python presentation.py --interactive`

The static figures below are supporting material for the report and slides.

## Project Structure

- `src/ga_presentation/`: core algorithm code
- `visualizations/`: scripts that call the algorithms and generate figures and GIFs
- `report/figures/`: static visuals
- `report/animations/`: step-by-step GIF animations

## Input / Process / Output

### Winding Number
- Input: an open or closed polygon
- Process: accumulate the signed angle of every polygon edge around a query point
- Output: a continuous winding field and a thresholded inside/outside field

### Convex Hull
- Input: a set of points
- Process: Graham scan sorts points by polar angle and removes clockwise turns
- Output: the outer hull polygon

### Fortune Sweep
- Input: a random point set
- Process: move a vertical sweep line, update the beach line, and resolve site/circle events
- Output: Voronoi edges

### Delaunay Dual
- Input: the same Fortune sweep state
- Process: collect the triples induced by circle events and convert them into dual edges
- Output: the Delaunay graph associated with the Voronoi diagram

## Static Figures

### Project inputs

![Project inputs]( "report" / "figures" / "project_inputs.png").as_posix())

### Random point generation modes

![Random inputs]( "report" / "figures" / "random_input_modes.png").as_posix())

### Winding number: input / process / output

![Winding number]( "report" / "figures" / "winding_input_process_output.png").as_posix())

### Winding trace snapshots

![Winding trace]( "report" / "figures" / "winding_trace_snapshots.png").as_posix())

### Convex hull snapshots

![Convex hull]( "report" / "figures" / "convex_hull_snapshots.png").as_posix())

### Fortune sweep snapshots

![Fortune sweep]( "report" / "figures" / "fortune_sweep_snapshots.png").as_posix())

### Final Voronoi and Delaunay outputs

![Voronoi and Delaunay]( "report" / "figures" / "voronoi_and_delaunay_outputs.png").as_posix())

### Delaunay derived from Voronoi duality

![Voronoi duality]( "report" / "figures" / "delaunay_from_voronoi_duality.png").as_posix())

## Animations

- [Convex hull growth GIF]( "report" / "animations" / "convex_hull_growth.gif").as_posix())
- [Fortune sweep GIF]( "report" / "animations" / "fortune_sweep.gif").as_posix())
- [Delaunay dual edges GIF]( "report" / "animations" / "delaunay_dual_edges.gif").as_posix())

## Summary

```json
{json.dumps(summary, indent=2)}
```
"""
    (ROOT / "report" / "REPORT.md").write_text(report_text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    polygons = load_repo_polygons(ROOT)
    save_project_overview(polygons)

    uniform_points = sample_uniform_points(14, (0.0, 10.0, 0.0, 10.0), seed=4)
    gaussian_points = sample_gaussian_clusters(18, [(2.5, 2.5), (7.5, 3.0), (5.0, 8.0)], sigma=0.8, seed=9)
    boundary_points = sample_polygon_boundary(polygons["p1"], 16, seed=12)
    save_random_generators_figure(uniform_points, gaussian_points, boundary_points, polygons["p1"])

    winding_shape = star_polygon((0.0, 0.0), 2.1, 5.0, 5)
    save_winding_figure(winding_shape)

    hull, hull_steps = save_convex_hull_assets(uniform_points)
    fortune_bounds = bounds_from_points(uniform_points, padding=1.0)
    fortune_snapshots, final_fortune = save_fortune_assets(uniform_points, fortune_bounds)

    summary = {
        "uniform_point_count": len(uniform_points),
        "gaussian_point_count": len(gaussian_points),
        "boundary_point_count": len(boundary_points),
        "convex_hull_vertices": len(hull),
        "convex_hull_snapshots": len(hull_steps),
        "fortune_snapshots": len(fortune_snapshots),
        "voronoi_segment_count": len(final_fortune.finished_segments),
        "delaunay_edge_count": len(final_fortune.delaunay_edges),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(summary)


if __name__ == "__main__":
    main()
