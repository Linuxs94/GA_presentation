from __future__ import annotations

import json
from pathlib import Path

from algorithms import (
    bowyer_watson,
    ensure_counter_clockwise,
    graham_scan,
    grid_difference,
    grid_intersection,
    grid_union,
    marching_squares,
    nearest_neighbor_path,
    polygon_bounds,
    prune_triangles_to_polygon,
    rasterize_polygon,
    stitch_segments,
    winding_steps,
)
from datasets import cf_assignment_polygons, default_primitive_datasets
from visuals import (
    ensure_output_dir,
    save_boolean_views,
    save_convex_hull_steps,
    save_delaunay_steps,
    save_grid_views,
    save_input_overview,
    save_marching_squares_view,
    save_toolpath_view,
    save_triangle_pruning,
    save_winding_explainer,
)


def build_summary() -> dict[str, object]:
    root = Path(__file__).resolve().parent
    output_dir = ensure_output_dir(root / "outputs")

    primitive_sets = default_primitive_datasets()
    polygon_a, polygon_b = cf_assignment_polygons(root)
    polygon_a = ensure_counter_clockwise(polygon_a)
    polygon_b = ensure_counter_clockwise(polygon_b)

    save_input_overview(output_dir / "01_inputs.png", primitive_sets, polygon_a, polygon_b)

    star = primitive_sets["star"]
    winding_point = (0.2, 0.3)
    winding_bounds = polygon_bounds([star], padding=1.5)
    save_winding_explainer(
        output_dir / "02_winding_steps.png",
        star,
        winding_point,
        winding_steps(winding_point, star, closed=True),
        winding_bounds,
    )

    star_binary, star_winding, _ = rasterize_polygon(star, winding_bounds, rows=60, cols=60, closed=True)
    save_grid_views(output_dir / "03_winding_grid.png", star_winding, star_binary, winding_bounds, star)

    hull_points = star + [(-5.0, 1.0), (5.5, -1.8), (0.0, 5.5), (0.4, -5.8)]
    hull, hull_steps = graham_scan(hull_points)
    save_convex_hull_steps(output_dir / "04_convex_hull.png", hull_points, hull_steps, hull)

    delaunay_points = hull_points + [(-1.5, 0.2), (2.5, 2.0), (1.8, -3.0), (-2.8, -1.8)]
    delaunay_triangles, delaunay_steps = bowyer_watson(delaunay_points)
    save_delaunay_steps(
        output_dir / "05_delaunay_steps.png",
        delaunay_points,
        delaunay_steps,
        delaunay_triangles,
    )

    pruned_triangles = prune_triangles_to_polygon(delaunay_triangles, star)
    save_triangle_pruning(
        output_dir / "06_pruned_mesh.png",
        star,
        delaunay_triangles,
        pruned_triangles,
    )

    cf_bounds = polygon_bounds([polygon_a, polygon_b], padding=25.0)
    grid_a, _, _ = rasterize_polygon(polygon_a, cf_bounds, rows=90, cols=90, closed=True)
    grid_b, _, _ = rasterize_polygon(polygon_b, cf_bounds, rows=90, cols=90, closed=True)

    union_grid = grid_union(grid_a, grid_b)
    intersection_grid = grid_intersection(grid_a, grid_b)
    difference_grid = grid_difference(grid_a, grid_b)
    save_boolean_views(
        output_dir / "07_boolean_grids.png",
        cf_bounds,
        grid_a,
        grid_b,
        union_grid,
        intersection_grid,
        difference_grid,
    )

    marching_segments, marching_cells = marching_squares(union_grid, cf_bounds)
    save_marching_squares_view(
        output_dir / "08_marching_squares.png",
        cf_bounds,
        union_grid,
        marching_segments,
        polygon_a,
        polygon_b,
    )

    contour_polylines = stitch_segments(marching_segments)
    ordered_polylines, travel_moves = nearest_neighbor_path(contour_polylines)
    save_toolpath_view(output_dir / "09_toolpath.png", cf_bounds, ordered_polylines, travel_moves)

    summary = {
        "primitive_datasets": list(primitive_sets.keys()),
        "winding_query_point": winding_point,
        "convex_hull_vertex_count": len(hull),
        "delaunay_triangle_count": len(delaunay_triangles),
        "pruned_triangle_count": len(pruned_triangles),
        "union_active_cells": sum(sum(row) for row in union_grid),
        "intersection_active_cells": sum(sum(row) for row in intersection_grid),
        "difference_active_cells": sum(sum(row) for row in difference_grid),
        "marching_segment_count": len(marching_segments),
        "marching_case_count": len(marching_cells),
        "toolpath_polyline_count": len(ordered_polylines),
        "travel_move_count": len(travel_moves),
    }

    with open(output_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    return summary


def main() -> None:
    summary = build_summary()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
