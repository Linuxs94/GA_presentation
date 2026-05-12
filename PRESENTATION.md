# Presentation Outline

## Slide 1. Title

**From Geometrical Algorithms to a Fabrication-Style Polygon Pipeline**

- apply GA ideas in a new context
- implement the core logic ourselves
- show the algorithms visually, step by step

## Slide 2. Project Goal

- start from lecture concepts
- keep the code short and readable
- apply the algorithms to polygon processing inspired by Computational Fabrication

Main question:

How can a few classic GA tools become one coherent geometry-processing pipeline?

## Slide 3. Final Pipeline

1. polygon input
2. winding-number inside/outside test
3. convex hull
4. Delaunay triangulation
5. triangle pruning
6. boolean grids
7. marching squares
8. contour ordering

Use figure:

- [outputs/01_inputs.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/01_inputs.png)

## Slide 4. Winding Number

- classify a query point by summing signed angles around the polygon
- convert continuous geometry into an inside/outside decision
- reuse the same idea later for rasterization and filtering

Use figures:

- [outputs/02_winding_steps.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/02_winding_steps.png)
- [outputs/03_winding_grid.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/03_winding_grid.png)

## Slide 5. Convex Hull

- implemented with Graham scan
- sort by angle around the anchor point
- maintain a stack and remove clockwise turns
- complexity: `O(n log n)`

Use figure:

- [outputs/04_convex_hull.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/04_convex_hull.png)

## Slide 6. Delaunay Triangulation

- implemented with an incremental Bowyer-Watson style workflow
- insert one point at a time
- remove triangles whose circumcircle contains the new point
- retriangulate the boundary cavity

Use figure:

- [outputs/05_delaunay_steps.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/05_delaunay_steps.png)

## Slide 7. Triangle Pruning

- Delaunay gives structure over the whole point set
- then we filter triangles back to the polygon interior
- test the triangle centroid with point-in-polygon

Use figure:

- [outputs/06_pruned_mesh.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/06_pruned_mesh.png)

## Slide 8. CF-Inspired Boolean Processing

- rasterize the two polygons to a shared grid
- perform `union`, `intersection`, and `difference` cell by cell
- simple, clear bridge from geometry to fabrication-style processing

Use figure:

- [outputs/07_boolean_grids.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/07_boolean_grids.png)

## Slide 9. Marching Squares

- recover a contour from the union grid
- each cell becomes one of 16 binary cases
- output contour segments are stitched into polylines

Use figure:

- [outputs/08_marching_squares.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/08_marching_squares.png)

## Slide 10. Toolpath View

- final contour can be interpreted as a fabrication path
- if there are multiple contours, order them with simple nearest-neighbor travel moves
- this is where the pipeline starts to connect to downstream fabrication logic

Use figure:

- [outputs/09_toolpath.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/09_toolpath.png)

## Slide 11. What We Showed

- we understood the lecture concepts
- we implemented the logic ourselves
- we applied the algorithms in a coherent external context
- we kept the code readable and directly explainable

## Slide 12. Limits and Next Steps

- Delaunay implementation is educational, not industrial-strength
- marching squares is kept simple
- toolpath ordering is basic nearest-neighbor logic
- natural extensions:
  - open polygons
  - better contour smoothing
  - stronger toolpath optimization
  - animation exports for each intermediate state
