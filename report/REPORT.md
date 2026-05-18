# GA Presentation Report

## Main Deliverable

The main teaching surface of this branch is the interactive viewer:

- [apps/interactive_viewer.py](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/apps/interactive_viewer.py)
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

![Project inputs](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/project_inputs.png)

### Random point generation modes

![Random inputs](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/random_input_modes.png)

### Winding number: input / process / output

![Winding number](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/winding_input_process_output.png)

### Winding trace snapshots

![Winding trace](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/winding_trace_snapshots.png)

### Convex hull snapshots

![Convex hull](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/convex_hull_snapshots.png)

### Fortune sweep snapshots

![Fortune sweep](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/fortune_sweep_snapshots.png)

### Final Voronoi and Delaunay outputs

![Voronoi and Delaunay](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/voronoi_and_delaunay_outputs.png)

### Delaunay derived from Voronoi duality

![Voronoi duality](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/figures/delaunay_from_voronoi_duality.png)

## Animations

- [Convex hull growth GIF](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/animations/convex_hull_growth.gif)
- [Fortune sweep GIF](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/animations/fortune_sweep.gif)
- [Voronoi edges appearing GIF](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/animations/voronoi_edges_appearing.gif)
- [Delaunay dual edges GIF](/Users/linus/Documents/master/primavera_2026/Geometric algorithms/projects/GA_presentation/report/animations/delaunay_dual_edges.gif)

## Summary

```json
{
  "uniform_point_count": 14,
  "gaussian_point_count": 18,
  "boundary_point_count": 16,
  "convex_hull_vertices": 7,
  "convex_hull_snapshots": 21,
  "fortune_snapshots": 34,
  "voronoi_segment_count": 45,
  "delaunay_edge_count": 32
}
```
