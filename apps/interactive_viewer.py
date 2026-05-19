from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import gradio as gr
import plotly.graph_objects as go
import math
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ga_presentation.convex_hull import monotone_chain, orientation
from ga_presentation.datasets import (
    load_repo_polygons,
    sample_gaussian_clusters,
    sample_polygon_boundary,
    sample_uniform_points,
    star_polygon,
)
from ga_presentation.fortune import FortuneSnapshot, compute_voronoi
from ga_presentation.winding import build_winding_field, WN_compute_bounds, polygon_edges, winding_trace


Point = tuple[float, float]
EDITOR_BOUNDS = (0.0, 10.0, 0.0, 10.0)
EDITOR_SIZE = 520

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


def point_key(point: object) -> tuple[float, float]:
    if hasattr(point, "x") and hasattr(point, "y"):
        return (float(point.x), float(point.y))
    return (float(point[0]), float(point[1]))


def make_point_names(points: list[Point], prefix: str = "p") -> dict[object, str]:
    names: dict[object, str] = {}
    for index, point in enumerate(points):
        label = f"{prefix}{index}"
        names[point] = label
        names[point_key(point)] = label
    return names


def format_point(point: Point) -> str:
    px, py = point_key(point)
    return f"({px:.2f}, {py:.2f})"


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

# call the right cloud of points
def choose_points(mode: str, count: int, seed: int) -> list[Point]:
    polygons = load_repo_polygons(ROOT)
    if mode == "uniform":
        return sample_uniform_points(count, (0.0, 10.0, 0.0, 10.0), seed=seed)
    if mode == "gaussian":
        return sample_gaussian_clusters(count, [(2.5, 2.5), (7.0, 3.0), (5.0, 8.0)], sigma=0.8, seed=seed)
    if mode == "custom":
        return []
    return sample_polygon_boundary(polygons["p1"], count, seed=seed)


def point_to_pixel(point: Point, size: int = EDITOR_SIZE, bounds: tuple[float, float, float, float] = EDITOR_BOUNDS) -> tuple[int, int]:
    min_x, max_x, min_y, max_y = bounds
    px = int(round((point[0] - min_x) / max(max_x - min_x, 1e-9) * (size - 1)))
    py = int(round((max_y - point[1]) / max(max_y - min_y, 1e-9) * (size - 1)))
    return px, py


def pixel_to_point(index: tuple[int, int], size: int = EDITOR_SIZE, bounds: tuple[float, float, float, float] = EDITOR_BOUNDS) -> Point:
    row, col = index
    min_x, max_x, min_y, max_y = bounds
    x = min_x + (col / max(size - 1, 1)) * (max_x - min_x)
    y = max_y - (row / max(size - 1, 1)) * (max_y - min_y)
    return (round(x, 3), round(y, 3))


def build_editor_image(points: list[Point], size: int = EDITOR_SIZE) -> Image.Image:
    image = Image.new("RGB", (size, size), "#fbfcfe")
    draw = ImageDraw.Draw(image)

    for tick in range(11):
        x = int(round(tick * (size - 1) / 10))
        y = int(round(tick * (size - 1) / 10))
        draw.line((x, 0, x, size), fill="#dde3ef", width=1)
        draw.line((0, y, size, y), fill="#dde3ef", width=1)

    draw.rectangle((0, 0, size - 1, size - 1), outline="#7c8798", width=2)

    for index, point in enumerate(points):
        px, py = point_to_pixel(point, size=size)
        draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill="#d62828", outline="white", width=2)
        draw.text((px + 8, py - 14), f"p{index}", fill="#132238")

    draw.text((12, 10), "Click to add points", fill="#132238")
    draw.text((12, size - 24), "Editor bounds: x,y in [0,10]", fill="#5d6577")
    return image


def custom_points_html(points: list[Point]) -> str:
    body = "<div class='metric-grid'>"
    body += metric("Mode", "custom clicks")
    body += metric("Point Count", str(len(points)))
    body += "</div>"
    body += "<h4>Custom Points</h4>"
    body += list_block([f"p{index} = {format_point(point)}" for index, point in enumerate(points)])
    body += "<h4>Usage</h4>"
    body += list_block(
        [
            "1. click on the editor to append a point",
            "2. the app switches to custom mode automatically",
            "3. use remove-last or clear to edit the set",
        ]
    )
    return panel("Point Editor", body)


def build_scenarios(point_mode: str, count: int, seed: int, custom_points: list[Point] | None = None) -> dict[str, object]:
    points = custom_points[:] if point_mode == "custom" and custom_points is not None else choose_points(point_mode, count, seed)
    polygons = load_repo_polygons(ROOT)
    winding_polygon = star_polygon((0.0, 0.0), 2.1, 5.0, 5)
    winding_query = (0.2, 0.25)
    winding_bounds = WN_compute_bounds([winding_polygon], margin=1.0)
    hull, hull_steps = monotone_chain(points)
    if points:
        bounds = (
            min(point[0] for point in points) - 1.0,
            max(point[0] for point in points) + 1.0,
            min(point[1] for point in points) - 1.0,
            max(point[1] for point in points) + 1.0,
        )
    else:
        bounds = EDITOR_BOUNDS
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


def add_circle_trace(fig: go.Figure, center: Point, radius: float, color: str = "#8d99ae") -> None:
    xs: list[float] = []
    ys: list[float] = []
    for index in range(121):
        angle = (2.0 * math.pi * index) / 120.0
        xs.append(center[0] + radius * math.cos(angle))
        ys.append(center[1] + radius * math.sin(angle))
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"color": color, "width": 2, "dash": "dot"},
        )
    )


def hull_structure_html(state: dict[str, object], step: int) -> str:
    points = state["points"]
    names = make_point_names(points)
    hull = state["hull"]
    snapshot = state["hull_steps"][step]
    candidate_name = names[snapshot.candidate]
    before_stack_names = [names[point] for point in snapshot.stack_before]
    after_stack_names = [names[point] for point in snapshot.stack]
    orientation_value = snapshot.orientation_value
    triple_names = [names[point] for point in snapshot.test_points] if snapshot.test_points is not None else []

    body = "<div class='metric-grid'>"
    body += metric("Step", f"{step + 1}/{len(state['hull_steps'])}")
    body += metric("Action", snapshot.action)
    body += metric("Pivot", names[snapshot.pivot])
    body += metric("Candidate", candidate_name)
    body += "</div>"
    body += "<h4>Sorted Order</h4>"
    body += chips([names[point] for point in snapshot.sorted_points])
    body += "<h4>Stack Before</h4>"
    body += chips(before_stack_names)
    body += "<h4>Stack After</h4>"
    body += chips(after_stack_names)
    body += "<h4>Current Orientation Test</h4>"
    orientation_lines = [f"triple = {', '.join(triple_names)}"] if triple_names else ["stack has fewer than 2 points"]
    if orientation_value is not None:
        turn = "counterclockwise" if orientation_value > 0 else "clockwise/flat"
        orientation_lines.extend([f"cross = {orientation_value:.3f}", f"decision = {turn}"])
    body += list_block(orientation_lines)
    body += "<h4>Action Log</h4>"
    action_lines = [
        f"take candidate {candidate_name}",
        f"compare against top of stack [{', '.join(before_stack_names)}]" if before_stack_names else "stack initially empty",
        f"{snapshot.action} candidate or top element",
        f"new stack = [{', '.join(after_stack_names)}]",
    ]
    body += list_block(action_lines)
    if hull:
        body += "<h4>Final Hull (when done)</h4>"
        body += chips([names[point] for point in hull])
    return panel("Monotone Chain State", body)


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
    body += "<h4>Action Log</h4>"
    body += list_block(
        [
            f"take edge e{step_data['edge_index']}",
            f"measure signed angle from {vertex_names[step_data['start']]} to {vertex_names[step_data['end']]} around the query point",
            f"add {step_data['angle']:.3f} to the running sum",
            f"new winding value = {step_data['winding']:.3f}",
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
    body += metric("Growing Edges", str(len(snapshot.active_segments)))
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
    if snapshot.active_circle_center is not None and snapshot.active_circle_radius is not None:
        body += "<h4>Active Circle Event</h4>"
        body += list_block(
            [
                f"center = {format_point(snapshot.active_circle_center)}",
                f"radius = {snapshot.active_circle_radius:.3f}",
                "sites = " + ", ".join(names.get(point, "?") for point in snapshot.active_circle_sites),
            ]
        )
    body += "<h4>Action Log</h4>"
    action_lines = [
        snapshot.action_summary or f"process {snapshot.event_kind} event",
        f"beach line after step = [{', '.join(names.get(point, '?') for point in snapshot.arc_sites)}]",
        f"completed Voronoi edges = {len(snapshot.finished_segments)}",
    ]
    if snapshot.active_circle_center is not None:
        action_lines.append("the dashed circle explains why this circle event occurs")
    body += list_block(action_lines)
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
    if not points:
        fig = go.Figure(layout=base_layout("Convex Hull: Monotone Chain"))
        fig.update_xaxes(range=[EDITOR_BOUNDS[0], EDITOR_BOUNDS[1]])
        fig.update_yaxes(range=[EDITOR_BOUNDS[2], EDITOR_BOUNDS[3]])
        add_state_annotation(fig, "Current Geometry", ["no points yet", "use the point editor to add a custom set"])
        return fig, panel("Monotone Chain State", list_block(["No points available. Add points in the editor."])), explanation_html("What is happening now", ["The hull view needs points. Click in the editor to create a custom set."])
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

    fig = go.Figure(layout=base_layout("Convex Hull: Monotone Chain"))
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
    if snapshot.test_points is not None:
        a, b, c = snapshot.test_points
        fig.add_trace(
            go.Scatter(
                x=[a[0], b[0], c[0]],
                y=[a[1], b[1], c[1]],
                mode="lines",
                line={"color": "#ff9f1c", "width": 3, "dash": "dash"},
            )
        )
        highlight_point(fig, a, "#577590", size=14)
        highlight_point(fig, b, "#577590", size=14)
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
            f"stack before = {len(snapshot.stack_before)} points",
            f"stack after = {len(snapshot.stack)} points",
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

    min_x, max_x, min_y, max_y = bounds
    query_point = state["winding_query"]

    fig = go.Figure(layout=base_layout("Winding Number"))
    fig.update_xaxes(range=[min_x, max_x])
    fig.update_yaxes(range=[min_y, max_y])

    visible_vertices = min(step + 2, len(polygon))
    partial_polygon = polygon[:visible_vertices]
    polygon_completed = (
        closed and visible_vertices == len(polygon)
    )

    if polygon_completed:
        path = partial_polygon + [polygon[0]]
        text_labels = (
            [names[p] for p in partial_polygon]
            + [names[polygon[0]]]
        )
    else:
        path = partial_polygon
        text_labels = [names[p] for p in partial_polygon]

    if len(partial_polygon) >= 2:

        field, _, _ = build_winding_field(
            partial_polygon,
            bounds,
            resolution=90,
            discrete=False,
            closed=polygon_completed,
        )

        fig.add_trace(
            go.Heatmap(
                z=field,
                x=[
                    min_x + index * (max_x - min_x) / (field.shape[1] - 1)
                    for index in range(field.shape[1])
                ],
                y=[
                    min_y + index * (max_y - min_y) / (field.shape[0] - 1)
                    for index in range(field.shape[0])
                ],
                colorscale="RdBu",
                zmid=0,
                showscale=False,
                opacity=0.82,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[p[0] for p in path],
            y=[p[1] for p in path],
            mode="lines+markers+text",
            text=text_labels,
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
            "The heatmap now grows progressively together with the polygon construction.",
        ],
    )

    return (
        fig,
        winding_structure_html(state, step, closed),
        explanation,
    )


def fortune_figure(state: dict[str, object], step: int, mode: str) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    snapshots = state["fortune"].snapshots
    snapshot = snapshots[step]
    bounds = state["fortune_bounds"]

    title = {
        "fortune": "Fortune Sweep",
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

    # voronoi
    if mode in {"fortune", "duality"}:
        # known voronoi graph
        for start, end in snapshot.finished_segments:
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#2a9d8f", "width": 2 if mode != "duality" else 1},
                    opacity=1.0 if mode != "duality" else 0.33,
                )
            )
        for start, end in snapshot.active_segments:
            is_fortune = (mode == "fortune")
            # dashed fortune
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={
                        "color": "#52b788",
                        "width": 3 if is_fortune else 2,
                        "dash": "dash" if is_fortune else "solid"
                    },
                    opacity=0.95 if is_fortune else 0.0
                )
            )
    # dual
    if mode in {"duality"}:
        for start, end in snapshot.delaunay_edges:
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#264653", "width": 2},
                    opacity=1.0             
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
    if snapshot.active_circle_center is not None and snapshot.active_circle_radius is not None and mode in {"fortune"}:
        add_circle_trace(fig, snapshot.active_circle_center, snapshot.active_circle_radius, color="#8d99ae")
        highlight_point(fig, snapshot.active_circle_center, "#8d99ae", size=14, symbol="diamond")
        for site in snapshot.active_circle_sites:
            highlight_point(fig, site, "#8338ec", size=15)

    if snapshot.focus is not None:
        highlight_point(fig, snapshot.focus, "#e63946", size=18, symbol="x")

    if mode == "duality" and snapshot.voronoi_dual_pairs:
        x_min, x_max = bounds[0], bounds[1]
        
        if snapshot.voronoi_dual_pairs:
            idx = min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)
            pair = snapshot.voronoi_dual_pairs[idx]
            if "site" in pair:
                active_site = pair["site"]
                a_act = active_site[0]
                b_act = -active_site[1]
                        
                fig.add_trace(
                    go.Scatter(
                        x=[x_min, x_max],
                        y=[a_act * x_min - b_act, a_act * x_max - b_act],
                        mode="lines",
                        line={"color": "#e63946", "width": 5},
                    )
                )

    description_lines = [
        f"phase = {snapshot.event_kind}",
        f"sweep x = {snapshot.sweep_x:.2f}",
        f"processed sites = {len(snapshot.processed_sites)}",
        f"pending circles = {len(snapshot.pending_circles)}",
        f"action = {snapshot.action_summary or snapshot.event_kind}",
    ]
    if mode == "fortune":
        description_lines.append("orange arcs = current beach line")
        description_lines.append("green dotted edges = growing Voronoi rays")
        if snapshot.active_circle_center is not None:
            description_lines.append("gray dashed circle = active circle event")
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
        total = max(1, len(state["hull_steps"]))
        label = "Convex hull: inspect push/pop events, stack evolution, and the current orientation test."
    elif algorithm == "winding_closed":
        total = max(1, len(state["winding_closed_trace"]))
        label = "Closed winding number: the last-to-first edge is part of the accumulation."
    elif algorithm == "winding_open":
        total = max(1, len(state["winding_open_trace"]))
        label = "Open winding number: the final closing edge is excluded."
    elif algorithm == "fortune":
        total = max(1,len(state["fortune"].snapshots))
        label = "from Voronoi to delaunay using duality laws"
    else:
        total = max(1, len(state["fortune"].snapshots))
        label = "Fortune / Voronoi : all views share the same event-by-event snapshot sequence."
    return total, label


def render_algorithm(
    algorithm: str,
    step: int,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
    custom_points: list[Point] | None,
):
    custom_key = tuple(custom_points or [])
    if stored_state is None or stored_state.get("meta") != (point_mode, count, seed, custom_key):
        stored_state = build_scenarios(point_mode, count, seed, custom_points=custom_points or [])
        stored_state["meta"] = (point_mode, count, seed, custom_key)

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
        build_editor_image(custom_points or []),
        custom_points_html(custom_points or []),
    )


def shift_step(delta: int, current_step: int, algorithm: str, stored_state: dict[str, object] | None):
    if stored_state is None:
        return current_step
    total_steps, _ = algorithm_info(algorithm, stored_state)
    return max(0, min(current_step + delta, total_steps - 1))


def add_custom_point(
    evt: gr.SelectData,
    custom_points: list[Point] | None,
    algorithm: str,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
):
    points = list(custom_points or [])
    if isinstance(evt.index, (tuple, list)) and len(evt.index) == 2:
        point = pixel_to_point((int(evt.index[0]), int(evt.index[1])))
        points.append(point)
    figure, header, structure, explanation, step_update, new_state, editor_image, editor_html = render_algorithm(
        algorithm,
        0,
        "custom",
        count,
        seed,
        stored_state,
        points,
    )
    return figure, header, structure, explanation, step_update, new_state, points, editor_image, editor_html, gr.update(value="custom")


def remove_last_custom_point(
    custom_points: list[Point] | None,
    algorithm: str,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
):
    points = list(custom_points or [])
    if points:
        points.pop()
    figure, header, structure, explanation, step_update, new_state, editor_image, editor_html = render_algorithm(
        algorithm,
        0,
        "custom",
        count,
        seed,
        stored_state,
        points,
    )
    return figure, header, structure, explanation, step_update, new_state, points, editor_image, editor_html, gr.update(value="custom")


def clear_custom_points(
    algorithm: str,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
):
    points: list[Point] = []
    figure, header, structure, explanation, step_update, new_state, editor_image, editor_html = render_algorithm(
        algorithm,
        0,
        "custom",
        count,
        seed,
        stored_state,
        points,
    )
    return figure, header, structure, explanation, step_update, new_state, points, editor_image, editor_html, gr.update(value="custom")


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
            custom_points = gr.State([])

            with gr.Row():
                algorithm = gr.Dropdown(
                    choices=[
                        ("Convex Hull", "convex_hull"),
                        ("Winding Number (Closed)", "winding_closed"),
                        ("Winding Number (Open)", "winding_open"),
                        ("Fortune Sweep", "fortune"),
                        ("Voronoi -> Delaunay Duality", "duality"),
                    ],
                    value="convex_hull",
                    label="Algorithm",
                )
                point_mode = gr.Dropdown(
                    choices=[("Uniform random", "uniform"), ("Gaussian clusters", "gaussian"), ("Polygon boundary", "boundary"), ("Custom clicks", "custom")],
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

            with gr.Row():
                with gr.Column(scale=5):
                    editor = gr.Image(
                        value=build_editor_image([]),
                        type="pil",
                        interactive=True,
                        sources=[],
                        label="Custom point editor",
                        height=420,
                        width=420,
                    )
                    with gr.Row():
                        remove_last = gr.Button("Remove Last Point", variant="secondary")
                        clear_points = gr.Button("Clear Points", variant="secondary")
                with gr.Column(scale=6):
                    editor_info = gr.HTML(value=custom_points_html([]))

            inputs = [algorithm, step, point_mode, point_count, seed, state, custom_points]
            outputs = [plot, header, structure, explanation, step, state, editor, editor_info]

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
            editor.select(
                add_custom_point,
                inputs=[custom_points, algorithm, point_mode, point_count, seed, state],
                outputs=[plot, header, structure, explanation, step, state, custom_points, editor, editor_info, point_mode],
            )
            remove_last.click(
                remove_last_custom_point,
                inputs=[custom_points, algorithm, point_mode, point_count, seed, state],
                outputs=[plot, header, structure, explanation, step, state, custom_points, editor, editor_info, point_mode],
            )
            clear_points.click(
                clear_custom_points,
                inputs=[algorithm, point_mode, point_count, seed, state],
                outputs=[plot, header, structure, explanation, step, state, custom_points, editor, editor_info, point_mode],
            )

            demo.load(
                render_algorithm,
                inputs=inputs,
                outputs=outputs,
            )

    return demo


if __name__ == "__main__":
    launch().launch()
