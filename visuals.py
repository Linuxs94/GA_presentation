from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PolygonPatch

from algorithms import DelaunayStep, Grid, HullStep, Point, Segment, Triangle, WindingStep


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def set_axes_style(ax: plt.Axes, title: str, bounds: tuple[float, float, float, float]) -> None:
    min_x, max_x, min_y, max_y = bounds
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.grid(True, alpha=0.2)


def draw_polygon(ax: plt.Axes, polygon: list[Point], color: str, label: str | None = None) -> None:
    ax.add_patch(
        PolygonPatch(
            polygon,
            closed=True,
            facecolor=color,
            edgecolor="black",
            alpha=0.35,
            linewidth=1.5,
            label=label,
        )
    )


def draw_polyline(ax: plt.Axes, polyline: list[Point], color: str, linewidth: float = 2.0) -> None:
    xs = [point[0] for point in polyline]
    ys = [point[1] for point in polyline]
    ax.plot(xs, ys, color=color, linewidth=linewidth)


def draw_triangles(ax: plt.Axes, triangles: list[Triangle], color: str, alpha: float = 0.5) -> None:
    for triangle in triangles:
        triangle_loop = [triangle[0], triangle[1], triangle[2], triangle[0]]
        xs = [point[0] for point in triangle_loop]
        ys = [point[1] for point in triangle_loop]
        ax.plot(xs, ys, color=color, linewidth=1.0, alpha=alpha)


def save_input_overview(
    path: str | Path,
    primitive_sets: dict[str, list[Point]],
    polygon_a: list[Point],
    polygon_b: list[Point],
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))
    primitive_items = list(primitive_sets.items())

    for ax, (name, polygon) in zip(axes[0], primitive_items):
        bounds = bounds_from_points(polygon, padding=1.5)
        set_axes_style(ax, f"Primitive: {name}", bounds)
        draw_polygon(ax, polygon, "#7cc6fe")
        draw_polyline(ax, polygon + [polygon[0]], "black")

    bounds = bounds_from_points(polygon_a + polygon_b, padding=30.0)
    set_axes_style(axes[1][0], "CF input polygons", bounds)
    draw_polygon(axes[1][0], polygon_a, "#7cc6fe", "P1")
    draw_polygon(axes[1][0], polygon_b, "#a3d977", "P2")
    draw_polyline(axes[1][0], polygon_a + [polygon_a[0]], "black")
    draw_polyline(axes[1][0], polygon_b + [polygon_b[0]], "black")
    axes[1][0].legend(loc="upper right")

    axes[1][1].axis("off")
    axes[1][1].text(
        0.0,
        0.95,
        "Final project flow\n\n"
        "1. Static polygon inputs\n"
        "2. Winding-number inside/outside test\n"
        "3. Graham scan convex hull\n"
        "4. Bowyer-Watson Delaunay triangulation\n"
        "5. Triangle pruning with point-in-polygon\n"
        "6. CF-inspired boolean grids\n"
        "7. Marching squares contours\n"
        "8. Simple contour toolpath ordering",
        va="top",
        fontsize=12,
    )

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_winding_explainer(
    path: str | Path,
    polygon: list[Point],
    query_point: Point,
    steps: list[WindingStep],
    bounds: tuple[float, float, float, float],
) -> None:
    selected = [0, len(steps) // 3, (2 * len(steps)) // 3, len(steps) - 1]
    selected = sorted(set(index for index in selected if 0 <= index < len(steps)))
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))

    for ax, step_index in zip(axes.flatten(), selected):
        step = steps[step_index]
        set_axes_style(ax, f"After edge {step_index + 1}: wn={step.total_angle:.2f}", bounds)
        draw_polygon(ax, polygon, "#c5e8b7")
        draw_polyline(ax, polygon + [polygon[0]], "black")
        ax.scatter([query_point[0]], [query_point[1]], color="#d7263d", s=45, zorder=3)

        # Show vectors from the query point to the current edge endpoints.
        for endpoint in step.edge:
            ax.plot(
                [query_point[0], endpoint[0]],
                [query_point[1], endpoint[1]],
                color="#f49d37",
                linewidth=1.5,
            )

        ax.plot(
            [step.edge[0][0], step.edge[1][0]],
            [step.edge[0][1], step.edge[1][1]],
            color="#d7263d",
            linewidth=3.0,
        )

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_grid_views(
    path: str | Path,
    winding_grid: list[list[float]],
    binary_grid: Grid,
    bounds: tuple[float, float, float, float],
    polygon: list[Point],
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    min_x, max_x, min_y, max_y = bounds

    axes[0].imshow(
        winding_grid,
        origin="lower",
        extent=[min_x, max_x, min_y, max_y],
        cmap="coolwarm",
    )
    set_axes_style(axes[0], "Continuous winding-number field", bounds)
    draw_polyline(axes[0], polygon + [polygon[0]], "black")

    axes[1].imshow(
        binary_grid,
        origin="lower",
        extent=[min_x, max_x, min_y, max_y],
        cmap="Greys",
    )
    set_axes_style(axes[1], "Binary inside / outside field", bounds)
    draw_polyline(axes[1], polygon + [polygon[0]], "black")

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_convex_hull_steps(
    path: str | Path,
    points: list[Point],
    steps: list[HullStep],
    hull: list[Point],
) -> None:
    chosen_indices = [0, len(steps) // 3, (2 * len(steps)) // 3, len(steps) - 1]
    chosen_indices = sorted(set(index for index in chosen_indices if 0 <= index < len(steps)))
    bounds = bounds_from_points(points, padding=1.2)
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))

    for ax, step_index in zip(axes.flatten(), chosen_indices):
        step = steps[step_index]
        set_axes_style(ax, f"Graham scan: {step.action}", bounds)
        scatter_points(ax, points)
        draw_polyline(ax, step.stack, "#d7263d", linewidth=2.5)
        ax.scatter([step.point[0]], [step.point[1]], color="#f49d37", s=60, zorder=3)

    if len(hull) >= 2:
        draw_polyline(axes[1][1], hull + [hull[0]], "#1b998b", linewidth=2.8)

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_delaunay_steps(
    path: str | Path,
    points: list[Point],
    steps: list[DelaunayStep],
    final_triangles: list[Triangle],
) -> None:
    chosen_indices = [0, len(steps) // 3, (2 * len(steps)) // 3, len(steps) - 1]
    chosen_indices = sorted(set(index for index in chosen_indices if 0 <= index < len(steps)))
    bounds = bounds_from_points(points, padding=1.2)
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))

    for ax, step_index in zip(axes.flatten(), chosen_indices):
        step = steps[step_index]
        set_axes_style(ax, f"Insert point {step_index + 1}", bounds)
        scatter_points(ax, points)
        draw_triangles(ax, step.triangles, "#1b998b", alpha=0.55)
        draw_triangles(ax, step.bad_triangles, "#d7263d", alpha=0.9)
        ax.scatter([step.inserted_point[0]], [step.inserted_point[1]], color="#f49d37", s=60, zorder=4)

    draw_triangles(axes[1][1], final_triangles, "#2d6a4f", alpha=0.9)
    axes[1][1].set_title("Final Delaunay triangulation")

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_triangle_pruning(
    path: str | Path,
    polygon: list[Point],
    all_triangles: list[Triangle],
    kept_triangles: list[Triangle],
) -> None:
    bounds = bounds_from_points(polygon, padding=1.0)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    set_axes_style(axes[0], "All Delaunay triangles", bounds)
    draw_triangles(axes[0], all_triangles, "#4ea8de", alpha=0.8)
    draw_polyline(axes[0], polygon + [polygon[0]], "black")

    set_axes_style(axes[1], "Triangles kept inside polygon", bounds)
    draw_triangles(axes[1], kept_triangles, "#2d6a4f", alpha=0.95)
    draw_polyline(axes[1], polygon + [polygon[0]], "black")

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_boolean_views(
    path: str | Path,
    bounds: tuple[float, float, float, float],
    grid_a: Grid,
    grid_b: Grid,
    union_grid: Grid,
    intersection_grid: Grid,
    difference_grid: Grid,
) -> None:
    titles = [
        "Polygon A grid",
        "Polygon B grid",
        "Union",
        "Intersection",
        "Difference A - B",
    ]
    grids = [grid_a, grid_b, union_grid, intersection_grid, difference_grid]
    min_x, max_x, min_y, max_y = bounds

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    flat_axes = axes.flatten()
    for ax, title, grid in zip(flat_axes, titles, grids):
        ax.imshow(grid, origin="lower", extent=[min_x, max_x, min_y, max_y], cmap="Greys")
        set_axes_style(ax, title, bounds)

    flat_axes[-1].axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_marching_squares_view(
    path: str | Path,
    bounds: tuple[float, float, float, float],
    grid: Grid,
    segments: list[Segment],
    polygon_a: list[Point],
    polygon_b: list[Point],
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    min_x, max_x, min_y, max_y = bounds

    axes[0].imshow(grid, origin="lower", extent=[min_x, max_x, min_y, max_y], cmap="Greys")
    set_axes_style(axes[0], "Union grid samples", bounds)
    draw_polyline(axes[0], polygon_a + [polygon_a[0]], "#4ea8de")
    draw_polyline(axes[0], polygon_b + [polygon_b[0]], "#90be6d")

    set_axes_style(axes[1], "Marching squares contour", bounds)
    for start, end in segments:
        axes[1].plot([start[0], end[0]], [start[1], end[1]], color="#d7263d", linewidth=1.5)

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_toolpath_view(
    path: str | Path,
    bounds: tuple[float, float, float, float],
    ordered_polylines: list[list[Point]],
    travel_moves: list[Segment],
) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    set_axes_style(ax, "Simple contour toolpath ordering", bounds)

    for index, polyline in enumerate(ordered_polylines):
        draw_polyline(ax, polyline, "#1b998b", linewidth=2.2)
        ax.scatter([polyline[0][0]], [polyline[0][1]], color="#f49d37", s=40, zorder=4)
        ax.text(polyline[0][0], polyline[0][1], f"  {index + 1}", fontsize=9)

    for start, end in travel_moves:
        ax.plot([start[0], end[0]], [start[1], end[1]], color="#d7263d", linestyle="--", linewidth=1.3)

    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def scatter_points(ax: plt.Axes, points: list[Point]) -> None:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    ax.scatter(xs, ys, color="black", s=28, zorder=3)


def bounds_from_points(points: list[Point], padding: float = 1.0) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs) - padding, max(xs) + padding, min(ys) - padding, max(ys) + padding
