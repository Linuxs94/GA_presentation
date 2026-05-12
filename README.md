# GA Presentation

This branch turns the original `dev` experiments into a presentation-oriented project structure.

The goal is simple:
- keep the working algorithm ideas from the branch
- make the project easier to navigate
- build a dedicated visualization layer around those algorithms
- store all generated figures and animations in a report folder
- make the main deliverable a step-by-step interactive viewer instead of only static plots

## Main Algorithms

- `Winding number`
  - input: polygon
  - process: sum signed angles around a query point
  - output: continuous field and inside/outside classification
- `Graham scan`
  - input: point set
  - process: sort by polar angle and remove clockwise turns
  - output: convex hull
- `Fortune sweep`
  - input: point set
  - process: handle site and circle events while updating the beach line
  - output: Voronoi diagram
- `Delaunay from Voronoi duality`
  - input: the Fortune sweep state
  - process: extract dual edges from the generated Voronoi structure
  - output: Delaunay graph

## Project Structure

- [src/ga_presentation](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/src/ga_presentation)
  - algorithm and data modules
- [apps/interactive_viewer.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/apps/interactive_viewer.py)
  - the main Gradio + Plotly app for event-by-event exploration
- [visualizations/build_all.py](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/visualizations/build_all.py)
  - generates static figures and GIFs for the report
- [report/figures](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/report/figures)
  - static plots and snapshot panels
- [report/animations](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/report/animations)
  - animated GIFs
- [report/REPORT.md](/Users/edu/Desktop/USI/semestre%201/GA/GA_presentation/GA_presentation/report/REPORT.md)
  - short project report generated from the pipeline

## Random Input Modes

The visualization pipeline includes:
- uniform random points
- clustered / gaussian points
- points sampled from polygon boundaries

## What The Interactive Viewer Shows

The interactive app gives you:
- step-by-step convex hull growth with the current stack and orientation test
- closed and open winding-number modes with the active edge and accumulated winding value
- Fortune sweep with the current beach line, processed sites, pending site queue, and pending circle queue
- Voronoi growth as completed edges appear
- Delaunay dual edges derived from the Voronoi process
- an explicit Voronoi-edge to Delaunay-edge duality view
- random point-set simulation modes:
  - uniform random
  - gaussian clusters
  - polygon boundary sampling

The static pipeline still creates:
- convex hull growth snapshots and GIF
- Fortune sweep snapshots and GIF
- Voronoi edges appearing animation
- Delaunay dual-edge animation
- winding-number input / process / output figures
- random input generator comparison figures

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run The Interactive Viewer

```bash
python presentation.py --interactive
```

This launches the step-by-step viewer on `http://127.0.0.1:7860` by default.

## Build The Static Report Assets

```bash
MPLBACKEND=Agg python presentation.py
```

This writes all static figures and animations to `report/`.
