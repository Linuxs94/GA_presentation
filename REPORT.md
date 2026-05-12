# Short Project Report

## Project Idea

We take a few core **Geometrical Algorithms** ideas and apply them to a small **fabrication-oriented polygon pipeline**.

The project goal is not to build the most advanced geometry engine. The goal is to show:
- we understand the algorithms
- we can implement them cleanly ourselves
- we can apply them to a context outside the exact GA lecture examples

## Pipeline

1. Build or load polygon inputs.
2. Classify points with the winding number.
3. Compute a convex hull with Graham scan.
4. Compute a Delaunay triangulation with an incremental insertion pipeline.
5. Prune triangles by testing whether their centroids lie inside a polygon.
6. Rasterize two polygons to grids and apply boolean operations.
7. Extract a contour with marching squares.
8. Order the extracted contour as a simple fabrication-style path.

## Figures

### 1. Inputs and project flow

![Inputs](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/01_inputs.png)

### 2. Winding-number step explanation

The query point is connected to the current edge endpoints. The accumulated signed angle shows how the winding number grows while we move around the polygon.

![Winding steps](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/02_winding_steps.png)

### 3. Winding field and binary inside / outside map

This is the CF-style bridge: a continuous geometric idea becomes a discrete field that can be processed cell by cell.

![Winding grid](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/03_winding_grid.png)

### 4. Graham scan convex hull

The intermediate frames show the evolving stack. The final frame shows the hull that encloses all points.

![Convex hull](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/04_convex_hull.png)

### 5. Incremental Delaunay triangulation

The red triangles are the local region replaced after inserting a point. The final frame shows the resulting triangulation.

![Delaunay](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/05_delaunay_steps.png)

### 6. Triangle pruning

We keep only the triangles whose centroids lie inside the polygon. This is a clean example of reusing one GA test to filter a more complex structure.

![Pruned mesh](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/06_pruned_mesh.png)

### 7. Boolean operations on rasterized polygons

The two CF polygons are rasterized, then processed with direct cell-wise `union`, `intersection`, and `difference`.

![Boolean grids](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/07_boolean_grids.png)

### 8. Marching squares

The union grid is converted back to a contour by applying the 16 marching-squares cases over the sampled cells.

![Marching squares](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/08_marching_squares.png)

### 9. Simple toolpath ordering

The final contour is already one polyline in this dataset, so the path is straightforward. The same stage can support multiple contours by ordering them with nearest-neighbor travel moves.

![Toolpath](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/09_toolpath.png)

## What We Implemented Ourselves

- winding number
- point-in-polygon from winding number
- Graham scan
- incremental Bowyer-Watson triangulation
- triangle pruning
- grid booleans
- marching squares
- contour stitching
- nearest-neighbor contour ordering

## What This Demonstrates

- a direct understanding of GA ideas
- an ability to explain those ideas visually
- an application of those ideas to a fabrication-style geometry pipeline
- a clean mapping from mathematical concept to code to output

## Output Summary

The generated numeric summary is stored in:

- [outputs/summary.json](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/summary.json)
