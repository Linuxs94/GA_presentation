from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import gradio as gr
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ga_presentation.convex_hull import graham_scan, orientation
from ga_presentation.datasets import (
    load_repo_polygons,
    sample_gaussian_clusters,
    sample_polygon_boundary,
    sample_uniform_points,
    star_polygon,
)
from ga_presentation.fortune import FortuneSnapshot, compute_voronoi
from ga_presentation.winding import build_winding_field, compute_bounds, polygon_edges, winding_trace


Point = tuple[float, float]

APP_CSS = """
.app-shell {max-width: 1600px !important; margin: 0 auto;}
.panel-card {
  background: linear-gradient(180deg, #ffffff 0%, #f7f8fb 100%);
  border: 1px solid #d9dbe3;
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 8px 20px rgba(18, 24, 40, 0.06);
}
.panel-card h3 {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #132238;
}
.panel-card h4 {
  margin: 12px 0 8px 0;
  font-size: 13px;
  color: #2d4a63;
}
.chip-row {display: flex; flex-wrap: wrap; gap: 8px;}
.chip {
  display: inline-block;
  border-radius: 999px;
  padding: 4px 10px;
  background: #eef3ff;
  border: 1px solid #c8d6ff;
  color: #223b71;
  font-family: "SFMono-Regular", Menlo, monospace;
  font-size: 12px;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.metric {
  background: white;
  border: 1px solid #e4e6ee;
  border-radius: 10px;
  padding: 8px 10px;
}
.metric-label {
  color: #5d6577;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.metric-value {
  color: #132238;
  font-family: "SFMono-Regular", Menlo, monospace;
  font-size: 14px;
  margin-top: 4px;
}
.list-block {
  background: white;
  border: 1px solid #e4e6ee;
  border-radius: 10px;
  padding: 10px 12px;
  font-family: "SFMono-Regular", Menlo, monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #1f2937;
  white-space: pre-wrap;
}
.explanation {
  background: linear-gradient(135deg, #132238 0%, #1f4060 100%);
  color: white;
  border-radius: 14px;
  padding: 14px 16px;
}
.explanation h3 {margin: 0 0 8px 0; font-size: 15px;}
.explanation p {margin: 0; line-height: 1.5;}
"""


def make_point_names(points: list[Point], prefix: str = "p") -> dict[Point, str]:
    return {point: f"{prefix}{index}" for index, point in enumerate(points)}


def format_point(point: Point) -> str:
    return f"({point[0]:.2f}, {point[1]:.2f})"


def chips(items: list[str]) -> str:
    if not items:
        return "<div class='chip-row'><span class='chip'>empty</span></div>"
    return "<div class='chip-row'>" + "".join(f"<span class='chip'>{escape(item)}</span>" for item in items) + "</div>"


def list_block(lines: list[str]) -> str:
    text = "\n".join(lines) if lines else "empty"
    return f"<div class='list-block'>{escape(text)}</div>"


def metric(label: str, value: str) -> str:
    return (
        "<div class='metric'>"
        f"<div class='metric-label'>{escape(label)}</div>"
        f"<div class='metric-value'>{escape(value)}</div>"
        "</div>"
    )


def panel(title: str, body: str) -> str:
    return f"<div class='panel-card'><h3>{escape(title)}</h3>{body}</div>"


def choose_points(mode: str, count: int, seed: int) -> list[Point]:
    polygons = load_repo_polygons(ROOT)
    if mode == "uniform":
        return sample_uniform_points(count, (0.0, 10.0, 0.0, 10.0), seed=seed)
    if mode == "gaussian":
        return sample_gaussian_clusters(count, [(2.5, 2.5), (7.0, 3.0), (5.0, 8.0)], sigma=0.8, seed=seed)
    return sample_polygon_boundary(polygons["p1"], count, seed=seed)


def build_scenarios(point_mode: str, count: int, seed: int) -> dict[str, object]:
    points = choose_points(point_mode, count, seed)
    polygons = load_repo_polygons(ROOT)
    winding_polygon = star_polygon((0.0, 0.0), 2.1, 5.0, 5)
    winding_query = (0.2, 0.25)
    winding_bounds = compute_bounds([winding_polygon], margin=1.0)
    hull, hull_steps = graham_scan(points)
    bounds = (
        min(point[0] for point in points) - 1.0,
        max(point[0] for point in points) + 1.0,
        min(point[1] for point in points) - 1.0,
        max(point[1] for point in points) + 1.0,
    )
    fortune = compute_voronoi(points, bounds, capture=True)
    return {
        "points": points,
        "hull": hull,
        "hull_steps": hull_steps,
        "fortune": fortune,
        "fortune_bounds": bounds,
        "winding_polygon": winding_polygon,
        "winding_bounds": winding_bounds,
        "winding_query": winding_query,
        "winding_closed_trace": winding_trace(winding_query, winding_polygon, closed=True),
        "winding_open_trace": winding_trace(winding_query, winding_polygon, closed=False),
        "repo_polygons": polygons,
    }


def base_layout(title: str) -> go.Layout:
    return go.Layout(
        title={"text": title, "font": {"size": 22, "family": "Avenir Next, Helvetica Neue, sans-serif"}},
        width=1120,
        height=760,
        template="plotly_white",
        xaxis={"scaleanchor": "y", "showgrid": True, "gridcolor": "#e7eaf2", "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": "#e7eaf2", "zeroline": False},
        margin={"l": 50, "r": 50, "t": 70, "b": 50},
        paper_bgcolor="#fbfcfe",
        plot_bgcolor="#fbfcfe",
        showlegend=False,
        font={"family": "Avenir Next, Helvetica Neue, sans-serif", "color": "#132238"},
    )


def add_state_annotation(fig: go.Figure, title: str, lines: list[str]) -> None:
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
        align="left",
        text=f"<b>{escape(title)}</b><br>" + "<br>".join(escape(line) for line in lines),
        showarrow=False,
        bordercolor="#d9dbe3",
        borderwidth=1,
        bgcolor="rgba(255,255,255,0.92)",
        font={"family": "Courier New, monospace", "size": 12, "color": "#132238"},
    )


def scatter_points(points: list[Point], names: dict[Point, str], color: str = "#243447", size: int = 10) -> go.Scatter:
    return go.Scatter(
        x=[point[0] for point in points],
        y=[point[1] for point in points],
        mode="markers+text",
        text=[names[point] for point in points],
        textposition="top center",
        marker={"size": size, "color": color, "line": {"color": "white", "width": 1}},
        textfont={"size": 12},
    )


def highlight_point(fig: go.Figure, point: Point, color: str, size: int = 16, symbol: str = "circle") -> None:
    fig.add_trace(
        go.Scatter(
            x=[point[0]],
            y=[point[1]],
            mode="markers",
            marker={"size": size, "color": color, "symbol": symbol, "line": {"color": "white", "width": 2}},
        )
    )


def hull_structure_html(state: dict[str, object], step: int) -> str:
    points = state["points"]
    names = make_point_names(points)
    hull = state["hull"]
    snapshot = state["hull_steps"][step]
    candidate_name = names[snapshot.candidate]
    stack_names = [names[point] for point in snapshot.stack]

    orientation_value = None
    triple_names: list[str] = []
    if len(snapshot.stack) >= 2:
        a, b = snapshot.stack[-2], snapshot.stack[-1]
        orientation_value = orientation(a, b, snapshot.candidate)
        triple_names = [names[a], names[b], candidate_name]

    body = "<div class='metric-grid'>"
    body += metric("Step", f"{step + 1}/{len(state['hull_steps'])}")
    body += metric("Action", snapshot.action)
    body += metric("Pivot", names[snapshot.pivot])
    body += metric("Candidate", candidate_name)
    body += "</div>"
    body += "<h4>Sorted Order</h4>"
    body += chips([names[point] for point in snapshot.sorted_points])
    body += "<h4>Hull Stack</h4>"
    body += chips(stack_names)
    body += "<h4>Current Orientation Test</h4>"
    orientation_lines = [f"triple = {', '.join(triple_names)}"] if triple_names else ["stack has fewer than 2 points"]
    if orientation_value is not None:
        turn = "counterclockwise" if orientation_value > 0 else "clockwise/flat"
        orientation_lines.extend([f"cross = {orientation_value:.3f}", f"decision = {turn}"])
    body += list_block(orientation_lines)
    if hull:
        body += "<h4>Final Hull (when done)</h4>"
        body += chips([names[point] for point in hull])
    return panel("Graham Scan State", body)


def winding_structure_html(state: dict[str, object], step: int, closed: bool) -> str:
    polygon = state["winding_polygon"]
    vertex_names = make_point_names(polygon, prefix="v")
    trace = state["winding_closed_trace" if closed else "winding_open_trace"]
    step_data = trace[min(step, len(trace) - 1)]
    edge_names = [(vertex_names[start], vertex_names[end]) for start, end in polygon_edges(polygon, closed=closed)]

    body = "<div class='metric-grid'>"
    body += metric("Step", f"{step + 1}/{len(trace)}")
    body += metric("Mode", "closed" if closed else "open")
    body += metric("Current Edge", f"e{step_data['edge_index']}")
    body += metric("Accumulated Winding", f"{step_data['winding']:.3f}")
    body += "</div>"
    body += "<h4>Polygon Vertex Order</h4>"
    body += chips([vertex_names[point] for point in polygon])
    body += "<h4>Edge List</h4>"
    body += list_block(
        [
            f"e{index}: {start_name} -> {end_name}" + ("  <-- active" if index == step_data["edge_index"] else "")
            for index, (start_name, end_name) in enumerate(edge_names)
        ]
    )
    body += "<h4>Angle Update</h4>"
    body += list_block(
        [
            f"query = {format_point(state['winding_query'])}",
            f"start = {vertex_names[step_data['start']]} {format_point(step_data['start'])}",
            f"end   = {vertex_names[step_data['end']]} {format_point(step_data['end'])}",
            f"delta = {step_data['angle']:.3f}",
        ]
    )
    return panel("Winding Number State", body)


def fortune_structure_html(state: dict[str, object], snapshot: FortuneSnapshot, step: int, mode: str) -> str:
    points = state["points"]
    names = make_point_names(points)
    focus_text = format_point(snapshot.focus) if snapshot.focus is not None else "none"
    pair = None
    if mode == "duality" and snapshot.voronoi_dual_pairs:
        pair = snapshot.voronoi_dual_pairs[min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)]

    body = "<div class='metric-grid'>"
    body += metric("Step", f"{step + 1}/{len(state['fortune'].snapshots)}")
    body += metric("Event", snapshot.event_kind)
    body += metric("Sweep X", f"{snapshot.sweep_x:.3f}")
    body += metric("Focus", focus_text)
    body += metric("Processed Sites", str(len(snapshot.processed_sites)))
    body += metric("Beach Arcs", str(len(snapshot.arc_sites)))
    body += metric("Voronoi Edges", str(len(snapshot.finished_segments)))
    body += metric("Delaunay Edges", str(len(snapshot.delaunay_edges)))
    body += "</div>"
    body += "<h4>Processed Sites</h4>"
    body += chips([names[point] for point in snapshot.processed_sites])
    body += "<h4>Beach Line Arc Order</h4>"
    body += chips([names.get(point, "?") for point in snapshot.arc_sites])
    body += "<h4>Pending Site Queue</h4>"
    body += list_block(
        [f"{names.get(point, '?')}  {format_point(point)}" for point in snapshot.pending_sites]
    )
    body += "<h4>Pending Circle Queue</h4>"
    body += list_block(
        [f"x={event_x:.3f}  center={format_point(center)}" for event_x, center in snapshot.pending_circles]
    )
    if pair is not None:
        start, end = pair["voronoi"]
        dual_start, dual_end = pair["dual"]
        body += "<h4>Highlighted Dual Pair</h4>"
        body += list_block(
            [
                f"Voronoi edge   = {format_point(start)} -> {format_point(end)}",
                f"Delaunay edge  = {names.get(dual_start, '?')} -> {names.get(dual_end, '?')}",
            ]
        )
    return panel("Sweep State", body)


def explanation_html(title: str, paragraphs: list[str]) -> str:
    body = f"<div class='explanation'><h3>{escape(title)}</h3>"
    for paragraph in paragraphs:
        body += f"<p>{escape(paragraph)}</p>"
    body += "</div>"
    return body


def hull_figure(state: dict[str, object], step: int) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    snapshots = state["hull_steps"]
    hull = state["hull"]
    snapshot = snapshots[step]
    bounds = (
        min(point[0] for point in points) - 1.0,
        max(point[0] for point in points) + 1.0,
        min(point[1] for point in points) - 1.0,
        max(point[1] for point in points) + 1.0,
    )

    fig = go.Figure(layout=base_layout("Convex Hull: Graham Scan"))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])
    fig.add_trace(scatter_points(points, names))

    fig.add_trace(
        go.Scatter(
            x=[point[0] for point in snapshot.sorted_points],
            y=[point[1] for point in snapshot.sorted_points],
            mode="lines",
            line={"color": "rgba(80, 112, 180, 0.25)", "width": 1, "dash": "dot"},
        )
    )
    if len(snapshot.stack) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[snapshot.stack[-2][0], snapshot.stack[-1][0], snapshot.candidate[0]],
                y=[snapshot.stack[-2][1], snapshot.stack[-1][1], snapshot.candidate[1]],
                mode="lines",
                line={"color": "#ff9f1c", "width": 3, "dash": "dash"},
            )
        )
    if snapshot.stack:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in snapshot.stack],
                y=[point[1] for point in snapshot.stack],
                mode="lines+markers",
                line={"color": "#d62828", "width": 4},
                marker={"size": 9, "color": "#d62828"},
            )
        )
    highlight_point(fig, snapshot.pivot, "#ef476f", size=18, symbol="diamond")
    highlight_point(fig, snapshot.candidate, "#ff9f1c", size=18)

    if step == len(snapshots) - 1 and hull:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in hull + [hull[0]]],
                y=[point[1] for point in hull + [hull[0]]],
                mode="lines",
                line={"color": "#2a9d8f", "width": 5},
            )
        )

    add_state_annotation(
        fig,
        "Current Geometry",
        [
            f"candidate = {names[snapshot.candidate]}",
            f"pivot = {names[snapshot.pivot]}",
            f"action = {snapshot.action}",
            "orange dashed chain = current orientation test",
            "red chain = current hull stack",
        ],
    )
    explanation = explanation_html(
        "What is happening now",
        [
            f"The algorithm is processing {names[snapshot.candidate]}.",
            "It checks the turn made by the last two stack points and the candidate.",
            "If the turn is clockwise or flat, the last stack point is removed; otherwise the candidate is pushed.",
        ],
    )
    return fig, hull_structure_html(state, step), explanation


def winding_figure(state: dict[str, object], step: int, closed: bool) -> tuple[go.Figure, str, str]:
    polygon = state["winding_polygon"]
    bounds = state["winding_bounds"]
    names = make_point_names(polygon, prefix="v")
    trace = state["winding_closed_trace" if closed else "winding_open_trace"]
    step_data = trace[min(step, len(trace) - 1)]
    field, _, _ = build_winding_field(polygon, bounds, resolution=90, discrete=False, closed=closed)
    min_x, max_x, min_y, max_y = bounds
    query_point = state["winding_query"]

    fig = go.Figure(layout=base_layout("Winding Number"))
    fig.update_xaxes(range=[min_x, max_x])
    fig.update_yaxes(range=[min_y, max_y])
    fig.add_trace(
        go.Heatmap(
            z=field,
            x=[min_x + index * (max_x - min_x) / (field.shape[1] - 1) for index in range(field.shape[1])],
            y=[min_y + index * (max_y - min_y) / (field.shape[0] - 1) for index in range(field.shape[0])],
            colorscale="RdBu",
            zmid=0,
            showscale=False,
            opacity=0.82,
        )
    )
    path = polygon + [polygon[0]] if closed else polygon
    fig.add_trace(
        go.Scatter(
            x=[p[0] for p in path],
            y=[p[1] for p in path],
            mode="lines+markers+text",
            text=[names[p] for p in polygon] + ([names[polygon[0]]] if closed else []),
            textposition="top center",
            line={"color": "#111827", "width": 3},
            marker={"size": 7, "color": "#111827"},
        )
    )
    highlight_point(fig, query_point, "#ff9f1c", size=16)
    fig.add_trace(
        go.Scatter(
            x=[query_point[0], step_data["start"][0]],
            y=[query_point[1], step_data["start"][1]],
            mode="lines",
            line={"color": "#ef476f", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[query_point[0], step_data["end"][0]],
            y=[query_point[1], step_data["end"][1]],
            mode="lines",
            line={"color": "#118ab2", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[step_data["start"][0], step_data["end"][0]],
            y=[step_data["start"][1], step_data["end"][1]],
            mode="lines",
            line={"color": "#06d6a0", "width": 5},
        )
    )
    add_state_annotation(
        fig,
        "Current Geometry",
        [
            f"mode = {'closed' if closed else 'open'}",
            f"edge = e{step_data['edge_index']}",
            f"delta = {step_data['angle']:.3f}",
            f"winding = {step_data['winding']:.3f}",
            "green edge contributes the current signed angle",
        ],
    )
    explanation = explanation_html(
        "What is happening now",
        [
            "The query point casts no ray here; instead the algorithm sums signed angles edge by edge.",
            "Closed mode includes the last-to-first edge, while open mode stops at the last listed segment.",
            "The heatmap shows the full field, and the highlighted edge shows the current incremental update.",
        ],
    )
    return fig, winding_structure_html(state, step, closed), explanation


def fortune_figure(state: dict[str, object], step: int, mode: str) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    snapshots = state["fortune"].snapshots
    snapshot = snapshots[step]
    bounds = state["fortune_bounds"]

    title = {
        "fortune": "Fortune Sweep",
        "voronoi": "Voronoi Edges Appearing",
        "delaunay": "Delaunay Dual Edges",
        "duality": "Voronoi -> Delaunay Duality",
    }[mode]
    fig = go.Figure(layout=base_layout(title))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])
    fig.add_trace(scatter_points(points, names, color="#4a4a4a"))

    if snapshot.pending_sites:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in snapshot.pending_sites],
                y=[point[1] for point in snapshot.pending_sites],
                mode="markers",
                marker={"size": 11, "color": "rgba(80,112,180,0.25)", "symbol": "circle"},
            )
        )
    if snapshot.processed_sites:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in snapshot.processed_sites],
                y=[point[1] for point in snapshot.processed_sites],
                mode="markers",
                marker={"size": 12, "color": "#1d4ed8"},
            )
        )

    if mode in {"fortune", "voronoi", "duality"}:
        for start, end in snapshot.finished_segments:
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#2a9d8f", "width": 2 if mode != "duality" else 1},
                    opacity=1.0 if mode != "duality" else 0.22,
                )
            )

    if mode in {"fortune", "delaunay", "duality"}:
        for start, end in snapshot.delaunay_edges:
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#264653", "width": 2 if mode != "duality" else 1},
                    opacity=1.0 if mode != "duality" else 0.22,
                )
            )

    if mode == "fortune":
        fig.add_shape(
            type="line",
            x0=snapshot.sweep_x,
            x1=snapshot.sweep_x,
            y0=bounds[2],
            y1=bounds[3],
            line={"color": "#d62828", "dash": "dash", "width": 3},
        )
        for polyline in snapshot.beachline:
            fig.add_trace(
                go.Scatter(
                    x=[p[0] for p in polyline],
                    y=[p[1] for p in polyline],
                    mode="lines",
                    line={"color": "#ff9f1c", "width": 3},
                )
            )

    if snapshot.focus is not None:
        highlight_point(fig, snapshot.focus, "#e63946", size=18, symbol="x")

    if mode == "duality" and snapshot.voronoi_dual_pairs:
        pair = snapshot.voronoi_dual_pairs[min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)]
        vs, ve = pair["voronoi"]
        ds, de = pair["dual"]
        fig.add_trace(
            go.Scatter(
                x=[vs[0], ve[0]],
                y=[vs[1], ve[1]],
                mode="lines",
                line={"color": "#00a896", "width": 5},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[ds[0], de[0]],
                y=[ds[1], de[1]],
                mode="lines",
                line={"color": "#e63946", "width": 5},
            )
        )

    description_lines = [
        f"phase = {snapshot.event_kind}",
        f"sweep x = {snapshot.sweep_x:.2f}",
        f"processed sites = {len(snapshot.processed_sites)}",
        f"pending circles = {len(snapshot.pending_circles)}",
    ]
    if mode == "fortune":
        description_lines.append("orange arcs = current beach line")
    if mode == "duality":
        description_lines.append("green edge and red edge form a dual pair")
    add_state_annotation(fig, "Current Geometry", description_lines)

    if mode == "duality":
        explanation = explanation_html(
            "What is happening now",
            [
                "The viewer highlights one Voronoi edge and the Delaunay edge connecting the two generating sites.",
                "This is the lecture-9 duality idea made explicit rather than only shown as a final triangulation.",
            ],
        )
    elif mode == "delaunay":
        explanation = explanation_html(
            "What is happening now",
            [
                "The Delaunay graph is extracted from the same sweep process.",
                "As circle events finalize local structure, more dual edges become available.",
            ],
        )
    elif mode == "voronoi":
        explanation = explanation_html(
            "What is happening now",
            [
                "Completed Voronoi edges appear only when the sweep has enough information to finish them.",
                "This view hides the beach line and emphasizes the diagram growth itself.",
            ],
        )
    else:
        explanation = explanation_html(
            "What is happening now",
            [
                "The red dashed line is the sweep line.",
                "Orange curves are the current beach line arcs.",
                "The state panel shows which sites are already processed and which events remain in the queues.",
            ],
        )
    return fig, fortune_structure_html(state, snapshot, step, mode), explanation


def algorithm_info(algorithm: str, state: dict[str, object]) -> tuple[int, str]:
    if algorithm == "convex_hull":
        total = len(state["hull_steps"])
        label = "Convex hull: inspect push/pop events, stack evolution, and the current orientation test."
    elif algorithm == "winding_closed":
        total = len(state["winding_closed_trace"])
        label = "Closed winding number: the last-to-first edge is part of the accumulation."
    elif algorithm == "winding_open":
        total = len(state["winding_open_trace"])
        label = "Open winding number: the final closing edge is excluded."
    else:
        total = len(state["fortune"].snapshots)
        label = "Fortune / Voronoi / Delaunay: all four views share the same event-by-event snapshot sequence."
    return total, label


def render_algorithm(
    algorithm: str,
    step: int,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
):
    if stored_state is None or stored_state.get("meta") != (point_mode, count, seed):
        stored_state = build_scenarios(point_mode, count, seed)
        stored_state["meta"] = (point_mode, count, seed)

    total_steps, description = algorithm_info(algorithm, stored_state)
    step = max(0, min(step, total_steps - 1))

    if algorithm == "convex_hull":
        figure, structure, explanation = hull_figure(stored_state, step)
    elif algorithm == "winding_closed":
        figure, structure, explanation = winding_figure(stored_state, step, True)
    elif algorithm == "winding_open":
        figure, structure, explanation = winding_figure(stored_state, step, False)
    elif algorithm == "fortune":
        figure, structure, explanation = fortune_figure(stored_state, step, "fortune")
    elif algorithm == "voronoi":
        figure, structure, explanation = fortune_figure(stored_state, step, "voronoi")
    elif algorithm == "delaunay":
        figure, structure, explanation = fortune_figure(stored_state, step, "delaunay")
    else:
        figure, structure, explanation = fortune_figure(stored_state, step, "duality")

    header = explanation_html("Current View", [description])
    return (
        figure,
        header,
        structure,
        explanation,
        gr.update(maximum=total_steps - 1, value=step),
        stored_state,
    )


def shift_step(delta: int, current_step: int, algorithm: str, stored_state: dict[str, object] | None):
    if stored_state is None:
        return current_step
    total_steps, _ = algorithm_info(algorithm, stored_state)
    return max(0, min(current_step + delta, total_steps - 1))


def launch() -> gr.Blocks:
    with gr.Blocks(title="GA Presentation Interactive Viewer", css=APP_CSS, fill_width=True) as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.Markdown(
                """
                # Interactive GA Visualizer

                Step through the algorithms event by event.  
                The plot shows the geometry, while the right-side panels expose the actual stack, edge list,
                beach-line order, and event queues used by the algorithm.
                """
            )

            state = gr.State(None)

            with gr.Row():
                algorithm = gr.Dropdown(
                    choices=[
                        ("Convex Hull", "convex_hull"),
                        ("Winding Number (Closed)", "winding_closed"),
                        ("Winding Number (Open)", "winding_open"),
                        ("Fortune Sweep", "fortune"),
                        ("Voronoi Growth", "voronoi"),
                        ("Delaunay Dual Edges", "delaunay"),
                        ("Voronoi -> Delaunay Duality", "duality"),
                    ],
                    value="convex_hull",
                    label="Algorithm",
                )
                point_mode = gr.Dropdown(
                    choices=[("Uniform random", "uniform"), ("Gaussian clusters", "gaussian"), ("Polygon boundary", "boundary")],
                    value="uniform",
                    label="Point generation mode",
                )
                point_count = gr.Slider(8, 24, value=14, step=1, label="Point count")
                seed = gr.Slider(1, 99, value=4, step=1, label="Seed")

            with gr.Row():
                prev_button = gr.Button("Previous Step", variant="secondary")
                next_button = gr.Button("Next Step", variant="primary")
                step = gr.Slider(0, 20, value=0, step=1, label="Step")
                regenerate = gr.Button("Regenerate / Recompute", variant="secondary")

            with gr.Row():
                with gr.Column(scale=7):
                    plot = gr.Plot(label="Geometry")
                with gr.Column(scale=4):
                    header = gr.HTML()
                    structure = gr.HTML()
                    explanation = gr.HTML()

            inputs = [algorithm, step, point_mode, point_count, seed, state]
            outputs = [plot, header, structure, explanation, step, state]

            algorithm.change(render_algorithm, inputs=inputs, outputs=outputs)
            step.change(render_algorithm, inputs=inputs, outputs=outputs)
            point_mode.change(render_algorithm, inputs=inputs, outputs=outputs)
            point_count.change(render_algorithm, inputs=inputs, outputs=outputs)
            seed.change(render_algorithm, inputs=inputs, outputs=outputs)
            regenerate.click(render_algorithm, inputs=inputs, outputs=outputs)

            prev_button.click(
                lambda current_step, algo, st: shift_step(-1, current_step, algo, st),
                inputs=[step, algorithm, state],
                outputs=[step],
            )
            next_button.click(
                lambda current_step, algo, st: shift_step(1, current_step, algo, st),
                inputs=[step, algorithm, state],
                outputs=[step],
            )

            demo.load(
                render_algorithm,
                inputs=[algorithm, step, point_mode, point_count, seed, state],
                outputs=outputs,
            )

    return demo


if __name__ == "__main__":
    launch().launch()
