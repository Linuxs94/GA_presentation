# GA Presentation Project

We build a small geometry-processing pipeline that applies core **Geometrical Algorithms** ideas to a **Computational Fabrication inspired polygon workflow**.

The project is intentionally educational:
- the core algorithms are implemented by hand
- the code is kept short and direct
- each stage has a visual output that shows what the algorithm is doing

## Final Scope

This branch focuses on one coherent chain instead of a broad feature list:

1. static polygon datasets
2. winding-number inside / outside testing
3. convex hull with Graham scan
4. Delaunay triangulation with an incremental Bowyer-Watson pipeline
5. triangle pruning with point-in-polygon
6. CF-style grid booleans on two polygons
7. marching squares contour extraction
8. simple contour ordering for a fabrication-style toolpath

## What The Project Shows

### GA concepts
- point-in-polygon via winding number
- convex hull construction
- triangulation structure
- filtering geometric structures by location tests

### Application context
- polygon rasterization on a grid
- boolean operations on volumetric-style 2D fields
- contour extraction
- simple path ordering for downstream fabrication logic

## Design Rules

- no geometry library is used for the core algorithms
- functions stay small and explicit
- comments are only added where a loop is dense enough to need help
- the implementation favors clarity over micro-optimizations
- where practical, the logic follows the lecture-level algorithmic idea

## Files

- [datasets.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/datasets.py): input polygons and primitive datasets
- [algorithms.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/algorithms.py): handmade geometry algorithms
- [visuals.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/visuals.py): rendering helpers for the report and presentation figures
- [run_project.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/run_project.py): end-to-end pipeline runner
- [REPORT.md](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/REPORT.md): short project report with generated visuals
- [PRESENTATION.md](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/PRESENTATION.md): ready-to-use slide outline
- [outputs/](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs): generated figures and summary

## Complexity Notes

- `Graham scan`: `O(n log n)` because of angular sorting
- `Winding-number rasterization`: `O(r * c * m)` for a `rows x cols` grid and a polygon with `m` edges
- `Grid booleans`: `O(r * c)`
- `Marching squares`: `O(r * c)`
- `Triangle pruning`: `O(t * m)` for `t` triangles and a polygon with `m` edges

The Delaunay stage is implemented with a simple incremental Bowyer-Watson workflow. It is included because it is compact and visually explainable, not because it is the most asymptotically optimal triangulation implementation.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
MPLBACKEND=Agg python run_project.py
```

This generates:
- overview figures
- winding-number explanation figures
- convex hull step figures
- Delaunay step figures
- triangle pruning figures
- boolean grid figures
- marching squares figures
- toolpath ordering figures
- [outputs/summary.json](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/summary.json)

## Main Output Set

- [01_inputs.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/01_inputs.png)
- [02_winding_steps.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/02_winding_steps.png)
- [03_winding_grid.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/03_winding_grid.png)
- [04_convex_hull.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/04_convex_hull.png)
- [05_delaunay_steps.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/05_delaunay_steps.png)
- [06_pruned_mesh.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/06_pruned_mesh.png)
- [07_boolean_grids.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/07_boolean_grids.png)
- [08_marching_squares.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/08_marching_squares.png)
- [09_toolpath.png](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/outputs/09_toolpath.png)
