# GA Presentation Report

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
- [Voronoi edges appearing GIF]( "report" / "animations" / "voronoi_edges_appearing.gif").as_posix())
- [Delaunay dual edges GIF]( "report" / "animations" / "delaunay_dual_edges.gif").as_posix())

## Summary

```json
{
  "uniform_point_count": 14,
  "gaussian_point_count": 18,
  "boundary_point_count": 16,
  "convex_hull_vertices": 7,
  "convex_hull_snapshots": 46,
  "fortune_snapshots": 34,
  "voronoi_segment_count": 45,
  "delaunay_edge_count": 32
}
```
