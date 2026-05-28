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
from ga_presentation.winding import build_winding_field, polygon_edges, winding_number, winding_trace


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
.story-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
.story-card {
  background: white;
  border: 1px solid #e4e6ee;
  border-radius: 12px;
  padding: 12px 14px;
}
.story-card h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #132238;
}
.story-card p {
  margin: 0;
  color: #334155;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}
.plot-legend-note {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e4e6ee;
  color: #334155;
  font-size: 12px;
  line-height: 1.45;
}
"""


def point_key(point: object) -> tuple[float, float]:
    if hasattr(point, "x") and hasattr(point, "y"):
        return (round(float(point.x), 6), round(float(point.y), 6))
    return (round(float(point[0]), 6), round(float(point[1]), 6))


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


def append_note(html: str, lines: list[str]) -> str:
    if not lines:
        return html
    note = "<div class='plot-legend-note'>" + "<br>".join(escape(line) for line in lines) + "</div>"
    return html + note


def story_card(title: str, lines: list[str]) -> str:
    text = "\n".join(lines) if lines else "empty"
    return f"<div class='story-card'><h4>{escape(title)}</h4><p>{escape(text)}</p></div>"


def story_panel(title: str, sections: list[tuple[str, list[str]]]) -> str:
    body = "<div class='story-grid'>" + "".join(story_card(section_title, lines) for section_title, lines in sections) + "</div>"
    return panel(title, body)


def padded_bounds(points: list[Point], min_pad: float = 20.0, pad_ratio: float = 0.08) -> tuple[float, float, float, float]:
    if not points:
        return EDITOR_BOUNDS
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)
    pad_x = max((max_x - min_x) * pad_ratio, min_pad)
    pad_y = max((max_y - min_y) * pad_ratio, min_pad)
    return (min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y)

# call the right cloud of points
def choose_points(mode: str, count: int, seed: int) -> list[Point]:
    polygons = load_repo_polygons(ROOT)
    if mode in polygons:
        return polygons[mode][:]
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
    winding_polygon = polygons[point_mode][:] if point_mode in polygons else star_polygon((0.0, 0.0), 2.1, 5.0, 5)
    winding_query = (
        sum(point[0] for point in winding_polygon) / len(winding_polygon),
        sum(point[1] for point in winding_polygon) / len(winding_polygon),
    )
    winding_bounds = padded_bounds(winding_polygon, min_pad=30.0, pad_ratio=0.12)
    hull, hull_steps = monotone_chain(points)
    if points:
        bounds = padded_bounds(points, min_pad=30.0, pad_ratio=0.12)
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
        "point_mode": point_mode,
    }


def filtered_delaunay_records(edges: list[tuple[Point, Point]], polygon: list[Point], enabled: bool) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    def ccw(a: Point, b: Point, c: Point) -> bool:
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
        return (
            ccw(a, c, d) != ccw(b, c, d)
            and ccw(a, b, c) != ccw(a, b, d)
        )

    if polygon:
        cx = sum(point[0] for point in polygon) / len(polygon)
        cy = sum(point[1] for point in polygon) / len(polygon)
    else:
        cx = 0.0
        cy = 0.0

    polygon_edges = []
    if len(polygon) >= 2:
        for i in range(len(polygon)):
            polygon_edges.append((polygon[i], polygon[(i + 1) % len(polygon)]))

    for start, end in edges:
        midpoint = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)

        intersects = False
        winding = 0.0

        if enabled and len(polygon) >= 3:
            for p0, p1 in polygon_edges:
                if start == p0 or start == p1 or end == p0 or end == p1:
                    continue

                if segments_intersect(start, end, p0, p1):
                    intersects = True
                    break

            winding = winding_number(midpoint, polygon, closed=True)

        # FINAL DECISION: ONLY WINDING
        keep = True
        if enabled and len(polygon) >= 3:
            keep = abs(winding) >= 0.5

        angle = math.atan2(midpoint[1] - cy, midpoint[0] - cx)
        if angle < 0:
            angle += 2.0 * math.pi

        records.append(
            {
                "start": start,
                "end": end,
                "midpoint": midpoint,
                "winding": winding,
                "keep": keep,
                "reason": (
                    "inside boundary"
                    if keep
                    else ("outside boundary" if abs(winding) < 0.5 else "uncertain")
                ),
                "order_angle": angle,
            }
        )

    records.sort(key=lambda item: (item["order_angle"], item["midpoint"][0], item["midpoint"][1]))
    return records
def final_filter_records(state: dict[str, object]) -> list[dict[str, object]]:
    final_snapshot = state["fortune"].snapshots[-1]
    return filtered_delaunay_records(
        final_snapshot.delaunay_edges,
        state["winding_polygon"],
        state.get("point_mode") in state["repo_polygons"],
    )


def final_duality_pairs(state: dict[str, object]) -> list[dict[str, object]]:
    final_snapshot = state["fortune"].snapshots[-1]
    points = state["points"]
    bounds = state["fortune_bounds"]
    min_x, max_x, min_y, max_y = bounds
    span = max(max_x - min_x, max_y - min_y, 1.0)
    limit = span * 20.0

    def canonical_site(site: Point) -> Point:
        best = min(points, key=lambda candidate: (candidate[0] - site[0]) ** 2 + (candidate[1] - site[1]) ** 2)
        if (best[0] - site[0]) ** 2 + (best[1] - site[1]) ** 2 <= 1e-4:
            return best
        return site

    cleaned: list[dict[str, object]] = []
    seen: set[tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]] = set()
    for pair in final_snapshot.voronoi_dual_pairs:
        vor_start, vor_end = pair["voronoi"]
        if max(abs(vor_start[0]), abs(vor_start[1]), abs(vor_end[0]), abs(vor_end[1])) > limit:
            continue
        dual_start = point_key(canonical_site(pair["dual"][0]))
        dual_end = point_key(canonical_site(pair["dual"][1]))
        key = (
            point_key(vor_start),
            point_key(vor_end),
            tuple(sorted((dual_start, dual_end)))[0],
            tuple(sorted((dual_start, dual_end)))[1],
        )
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(
            {
                "voronoi": (point_key(vor_start), point_key(vor_end)),
                "dual": (dual_start, dual_end),
            }
        )
    return cleaned


def fortune_event_snapshots(state: dict[str, object]) -> list[FortuneSnapshot]:
    snapshots = [snapshot for snapshot in state["fortune"].snapshots if snapshot.event_kind != "done"]
    return snapshots or state["fortune"].snapshots


def voronoi_growth_snapshots(state: dict[str, object]) -> list[FortuneSnapshot]:
    snapshots = [
        snapshot
        for snapshot in fortune_event_snapshots(state)
        if snapshot.finished_segments_this_step
        or snapshot.new_active_segments_this_step
        or snapshot.carried_finished_segments
        or snapshot.carried_active_segments
    ]
    return snapshots or fortune_event_snapshots(state)


def base_layout(title: str) -> go.Layout:
    return go.Layout(
        title={"text": title, "font": {"size": 22, "family": "Avenir Next, Helvetica Neue, sans-serif"}},
        width=900,
        height=620,
        template="plotly_white",
        xaxis={"scaleanchor": "y", "showgrid": True, "gridcolor": "#e7eaf2", "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": "#e7eaf2", "zeroline": False},
        margin={"l": 40, "r": 30, "t": 65, "b": 40},
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


def add_text_label(fig: go.Figure, point: Point, text: str, color: str = "#132238", yshift: int = 16) -> None:
    fig.add_annotation(
        x=point[0],
        y=point[1],
        text=escape(text),
        showarrow=False,
        yshift=yshift,
        bgcolor="rgba(255,255,255,0.88)",
        bordercolor="rgba(203,213,225,0.9)",
        borderwidth=1,
        borderpad=4,
        font={"size": 12, "color": color},
    )


def segment_midpoint(start: Point, end: Point) -> Point:
    return ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)


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

    who_lines = [
        f"step = {step + 1}/{len(state['hull_steps'])}",
        f"candidate = {candidate_name} {format_point(snapshot.candidate)}",
        f"pivot = {names[snapshot.pivot]} {format_point(snapshot.pivot)}",
        f"chain = {snapshot.chain}",
        f"orientation triple = {', '.join(triple_names)}" if triple_names else "orientation triple = not available yet",
    ]
    decision_lines = [
        f"action = {snapshot.action}",
        f"orientation = {snapshot.orientation_label}" if snapshot.orientation_label is not None else "orientation = not available yet",
        f"cross value = {orientation_value:.3f}" if orientation_value is not None else "cross value = not available yet",
        f"popped point = {names[snapshot.popped_point]}" if snapshot.popped_point is not None else "popped point = none",
    ]
    changed_lines = [
        f"stack before = [{', '.join(before_stack_names)}]" if before_stack_names else "stack before = []",
        f"stack after = [{', '.join(after_stack_names)}]" if after_stack_names else "stack after = []",
        f"sorted order = [{', '.join(names[point] for point in snapshot.sorted_points)}]",
    ]
    if snapshot.is_final and hull:
        changed_lines.append(f"final hull = [{', '.join(names[point] for point in hull)}]")
    why_lines = [
        "The hull keeps only turns that preserve a convex outer envelope.",
        "Clockwise or flat turns eject the last stack point.",
        "Lower and upper chains are built separately, then merged.",
    ]
    return story_panel(
        "Monotone Chain State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def winding_structure_html(state: dict[str, object], step: int, closed: bool) -> str:
    polygon = state["winding_polygon"]
    vertex_names = make_point_names(polygon, prefix="v")
    trace = state["winding_closed_trace" if closed else "winding_open_trace"]
    step_data = trace[min(step, len(trace) - 1)]
    edge_names = [(vertex_names[start], vertex_names[end]) for start, end in polygon_edges(polygon, closed=closed)]

    who_lines = [
        f"step = {step + 1}/{len(trace)}",
        f"mode = {'closed' if closed else 'open'}",
        f"current edge = e{step_data['edge_index']} : {vertex_names[step_data['start']]} -> {vertex_names[step_data['end']]}",
        f"query point = {format_point(step_data['query_point_original'])}",
        f"polygon center = {format_point(step_data['polygon_center'])}",
    ]
    decision_lines = [
        "decision = add the signed angle of the current edge to the running sum",
        f"cross = {step_data['cross']:.3f}",
        f"dot = {step_data['dot']:.3f}",
        f"angle contribution = {step_data['angle']:.3f}",
    ]
    changed_lines = [
        f"winding before = {step_data['winding_before']:.3f}",
        f"winding after = {step_data['winding_after']:.3f}",
        f"translated query = {format_point(step_data['query_point_translated'])}",
        f"translated edge = {format_point(step_data['start_translated'])} -> {format_point(step_data['end_translated'])}",
    ]
    why_lines = [
        "Each edge adds one signed angular contribution around the query point.",
        "Closed mode includes the last-to-first edge; open mode leaves it out.",
        "The translated frame is exposed so the internal computation can be explained honestly.",
    ]
    return story_panel(
        "Winding Number State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def fortune_structure_html(state: dict[str, object], snapshot: FortuneSnapshot, step: int, mode: str) -> str:
    points = state["points"]
    names = make_point_names(points)
    focus_text = format_point(snapshot.focus) if snapshot.focus is not None else "none"
    pair = None
    filter_records = filtered_delaunay_records(
        snapshot.delaunay_edges,
        state["winding_polygon"],
        state.get("point_mode") in state["repo_polygons"],
    )
    if mode == "duality" and snapshot.voronoi_dual_pairs:
        pair = snapshot.voronoi_dual_pairs[min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)]
    total_steps = len(fortune_event_snapshots(state)) if mode == "fortune" else len(state["fortune"].snapshots)

    who_lines = [
        f"step = {step + 1}/{total_steps}",
        f"event = {snapshot.event_kind}",
        f"focus = {focus_text}",
        f"sweep x = {snapshot.sweep_x:.3f}",
        f"affected arc = {names.get(snapshot.affected_arc_site, '?')} {format_point(snapshot.affected_arc_site) if snapshot.affected_arc_site is not None else 'none'}",
    ]
    if snapshot.active_circle_center is not None and snapshot.active_circle_radius is not None:
        who_lines.append(
            f"active circle = center {format_point(snapshot.active_circle_center)} radius {snapshot.active_circle_radius:.3f}"
        )
    decision_lines = [
        snapshot.action_summary or f"process {snapshot.event_kind} event",
        f"decision = {snapshot.decision or snapshot.event_kind}",
        f"processed sites = {len(snapshot.processed_sites)}",
        f"pending site events = {len(snapshot.pending_sites)}",
        f"pending circle events = {len(snapshot.pending_circles)}",
    ]
    changed_lines = [
        f"beachline after = [{', '.join(names.get(point, '?') for point in snapshot.arc_sites)}]",
        f"new Voronoi segments = {len(snapshot.created_segments_this_step)}",
        f"finished Voronoi segments = {len(snapshot.finished_segments_this_step)}",
        f"circle events added = {len(snapshot.circle_events_added_this_step)}",
        f"circle events invalidated = {len(snapshot.circle_events_invalidated_this_step)}",
        f"new Delaunay edges = {len(snapshot.new_delaunay_edges)}",
    ]
    if mode in {"filtered_delaunay", "combined"}:
        changed_lines.append(f"kept filtered edges = {sum(1 for item in filter_records if item['keep'])}")
        changed_lines.append(f"discarded filtered edges = {sum(1 for item in filter_records if not item['keep'])}")
    why_lines = [
        "Each site or circle event changes the beachline and therefore the Voronoi structure.",
        "Circle events remove one arc and finalize geometry that was only growing before.",
        "The panel reports the local delta of this step, not just the accumulated result.",
    ]
    if mode in {"filtered_delaunay", "combined"}:
        why_lines.append("The filter keeps only Delaunay edges whose midpoint stays inside the winding-number region.")
    if pair is not None:
        why_lines.append(
            f"highlighted dual pair = Voronoi {format_point(pair['voronoi'][0])}->{format_point(pair['voronoi'][1])} | Delaunay {names.get(pair['dual'][0], '?')}->{names.get(pair['dual'][1], '?')}"
        )
    return story_panel(
        "Sweep State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


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
    bounds = padded_bounds(points, min_pad=30.0, pad_ratio=0.12)

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
                line={"color": "#d62828" if snapshot.chain == "lower" else "#7c3aed", "width": 4},
                marker={"size": 9, "color": "#d62828" if snapshot.chain == "lower" else "#7c3aed"},
            )
        )
    if snapshot.popped_point is not None:
        highlight_point(fig, snapshot.popped_point, "#fb7185", size=18, symbol="x")
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

    explanation = explanation_html(
        "What is happening now",
        [
            f"The algorithm is processing {names[snapshot.candidate]}.",
            f"It is currently building the {snapshot.chain} chain.",
            "It checks the turn made by the last two stack points and the candidate.",
            f"The current orientation test is {snapshot.orientation_label or 'not available yet'}.",
            f"This step changes the stack from {len(snapshot.stack_before)} to {len(snapshot.stack)} points.",
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
    current_edge_index = step_data["edge_index"]

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
            resolution=300,
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
                opacity=0.62,
            )
        )
    if len(path) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[p[0] for p in path],
                y=[p[1] for p in path],
                mode="lines+markers+text",
                text=text_labels,
                textposition="top center",
                line={"color": "rgba(17,24,39,0.70)", "width": 2.4},
                marker={"size": 7, "color": "#111827"},
            )
        )
    if not closed and len(polygon) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[polygon[-1][0], polygon[0][0]],
                y=[polygon[-1][1], polygon[0][1]],
                mode="lines",
                line={"color": "#ef4444", "width": 2, "dash": "dash"},
                opacity=0.46,
            )
        )
    processed_edges = polygon_edges(polygon, closed=closed)
    for idx, (start, end) in enumerate(processed_edges[: current_edge_index]):
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#94a3b8", "width": 2},
                opacity=0.65,
            )
        )
    highlight_point(fig, query_point, "#ff9f1c", size=16)
    fig.add_trace(
        go.Scatter(
            x=[query_point[0], step_data["start"][0]],
            y=[query_point[1], step_data["start"][1]],
            mode="lines",
            line={"color": "#ef476f", "width": 3.8},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[query_point[0], step_data["end"][0]],
            y=[query_point[1], step_data["end"][1]],
            mode="lines",
            line={"color": "#118ab2", "width": 3.8},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[step_data["start"][0], step_data["end"][0]],
            y=[step_data["start"][1], step_data["end"][1]],
            mode="lines",
            line={"color": "#06d6a0", "width": 6},
        )
    )
    explanation = append_note(explanation_html(
        "What is happening now",
        [
            "The algorithm sums signed angles edge by edge around the query point.",
            "The bright green segment is the current edge; faded segments were processed earlier.",
            "In open mode the dashed red edge is intentionally missing from the sum.",
            "The heatmap is only context; the main step logic is the current angular contribution.",
        ],
    ), [
        "Legend: green = current edge, pink/blue = vectors to the query point, red dashed = missing closing edge in open mode.",
    ])

    return (
        fig,
        winding_structure_html(state, step, closed),
        explanation,
    )


def fortune_figure(state: dict[str, object], step: int, mode: str) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    snapshots = fortune_event_snapshots(state) if mode == "fortune" else state["fortune"].snapshots
    snapshot = snapshots[step]
    bounds = snapshot.camera_bounds

    title = {
        "fortune": "Fortune Sweep",
        "filtered_delaunay": "Delaunay With Boundary Filter",
        "combined": "Boundary + Interior Structure",
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
                marker={"size": 9, "color": "rgba(80,112,180,0.18)", "symbol": "circle"},
            )
        )
    if snapshot.processed_sites:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in snapshot.processed_sites],
                y=[point[1] for point in snapshot.processed_sites],
                mode="markers",
                marker={"size": 10, "color": "rgba(29,78,216,0.72)"},
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
                    line={"color": "#94a3b8", "width": 1.5 if mode != "duality" else 1},
                    opacity=0.55 if mode != "duality" else 0.48,
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
                        "color": "#9ccfb5",
                        "width": 2.4 if is_fortune else 1.5,
                        "dash": "dash" if is_fortune else "solid"
                    },
                    opacity=0.70 if is_fortune else 0.0
                )
            )
    filter_enabled = state.get("point_mode") in state["repo_polygons"]
    filter_records = filtered_delaunay_records(snapshot.delaunay_edges, state["winding_polygon"], filter_enabled)
    kept_edges = [item for item in filter_records if item["keep"]]
    discarded_edges = [item for item in filter_records if not item["keep"]]

    # dual
    if mode in {"duality"}:
        active_pair = None
        if snapshot.voronoi_dual_pairs:
            active_pair = snapshot.voronoi_dual_pairs[min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)]
        for start, end in snapshot.delaunay_edges:
            is_active = active_pair is not None and ((start, end) == active_pair["dual"] or (end, start) == active_pair["dual"])
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#1d4ed8" if is_active else "#cbd5e1", "width": 4.5 if is_active else 1.6},
                    opacity=1.0 if is_active else 0.32
                )
            )
    elif mode == "filtered_delaunay":
        polygon = state["winding_polygon"]
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in polygon + [polygon[0]]],
                y=[point[1] for point in polygon + [polygon[0]]],
                mode="lines",
                line={"color": "#111827", "width": 3},
            )
        )
        for item in discarded_edges:
            start, end = item["start"], item["end"]
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#9ca3af", "width": 1.8, "dash": "dash"},
                    opacity=0.5,
                )
            )
        for item in kept_edges:
            start, end = item["start"], item["end"]
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#1d4ed8", "width": 3.0},
                    opacity=1.0,
                )
            )
            highlight_point(fig, item["midpoint"], "#0f766e", size=10, symbol="diamond")
    elif mode == "combined":
        polygon = state["winding_polygon"]
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in polygon + [polygon[0]]],
                y=[point[1] for point in polygon + [polygon[0]]],
                mode="lines",
                line={"color": "#111827", "width": 3},
            )
        )
        for item in kept_edges:
            start, end = item["start"], item["end"]
            fig.add_trace(
                go.Scatter(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    mode="lines",
                    line={"color": "#1d4ed8", "width": 3.1},
                    opacity=1.0,
                )
            )
        hull = state.get("hull", [])
        if hull:
            fig.add_trace(
                go.Scatter(
                    x=[point[0] for point in hull + [hull[0]]],
                    y=[point[1] for point in hull + [hull[0]]],
                    mode="lines",
                    line={"color": "#ef4444", "width": 2, "dash": "dash"},
                    opacity=0.45,
                )
            )

    if mode == "fortune":
        fig.add_shape(
            type="line",
            x0=snapshot.sweep_x,
            x1=snapshot.sweep_x,
            y0=bounds[2],
            y1=bounds[3],
            line={"color": "#d62828", "dash": "dash", "width": 2.5},
        )
        for polyline in snapshot.beachline:
            fig.add_trace(
                go.Scatter(
                    x=[p[0] for p in polyline],
                    y=[p[1] for p in polyline],
                    mode="lines",
                    line={"color": "#ff9f1c", "width": 2.5},
                )
            )
    if snapshot.active_circle_center is not None and snapshot.active_circle_radius is not None and mode in {"fortune"}:
        add_circle_trace(fig, snapshot.active_circle_center, snapshot.active_circle_radius, color="#8d99ae")
        highlight_point(fig, snapshot.active_circle_center, "#8d99ae", size=14, symbol="diamond")
        for site in snapshot.active_circle_sites:
            highlight_point(fig, site, "#8338ec", size=15)

    if snapshot.focus is not None:
        highlight_point(fig, snapshot.focus, "#e63946", size=18, symbol="x")
    if snapshot.affected_arc_site is not None:
        highlight_point(fig, snapshot.affected_arc_site, "#f59e0b", size=18, symbol="diamond")
    if snapshot.removed_arc_site is not None:
        highlight_point(fig, snapshot.removed_arc_site, "#ef4444", size=20, symbol="x")
    for arc_site in snapshot.created_arc_sites:
        highlight_point(fig, arc_site, "#22c55e", size=14, symbol="circle-cross")
    for start, end in snapshot.finished_segments_this_step:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#111827", "width": 4.4},
                opacity=0.95,
            )
        )
    for item in snapshot.created_segments_this_step:
        start = item["start"]
        end = item["end"]
        if end is None:
            continue
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#10b981", "width": 4.4, "dash": "dot"},
                opacity=0.95,
            )
        )

    if mode == "duality" and snapshot.voronoi_dual_pairs:
        x_min, x_max = bounds[0], bounds[1]
        
        if snapshot.voronoi_dual_pairs:
            idx = min(step % len(snapshot.voronoi_dual_pairs), len(snapshot.voronoi_dual_pairs) - 1)
            pair = snapshot.voronoi_dual_pairs[idx]
            vor_start, vor_end = pair["voronoi"]
            fig.add_trace(
                go.Scatter(
                    x=[vor_start[0], vor_end[0]],
                    y=[vor_start[1], vor_end[1]],
                    mode="lines",
                    line={"color": "#10b981", "width": 5},
                    opacity=1.0,
                )
            )
            for site in pair["dual"]:
                highlight_point(fig, site, "#f59e0b", size=18, symbol="diamond")
            if "site" in pair:
                active_site = pair["site"]
                a_act = active_site[0]
                b_act = -active_site[1]
                        
                fig.add_trace(
                    go.Scatter(
                        x=[x_min, x_max],
                        y=[a_act * x_min - b_act, a_act * x_max - b_act],
                        mode="lines",
                        line={"color": "#ef4444", "width": 4, "dash": "dot"},
                    )
                )

    description_lines = [
        f"phase = {snapshot.event_kind}",
        f"decision = {snapshot.decision or snapshot.event_kind}",
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
        if snapshot.created_segments_this_step:
            description_lines.append("green dotted bold segments = segments created in this step")
        if snapshot.finished_segments_this_step:
            description_lines.append("black bold segments = segments finished in this step")
        if snapshot.removed_arc_site is not None:
            description_lines.append("red x = arc removed by the current circle event")
    if mode == "filtered_delaunay":
        description_lines.append("black loop = boundary used by the winding filter")
        description_lines.append("green/red edge = current decision")
        description_lines.append("blue edges = already kept; dashed gray = already discarded")
        description_lines.append("red/teal diamonds = tested midpoints")
    if mode == "combined":
        description_lines.append("black loop = recovered outer boundary")
        description_lines.append("blue graph = filtered interior structure")
        description_lines.append("red dashed loop = convex hull shown only as faint contrast")
    if mode == "duality":
        description_lines.append("green edge and red edge form a dual pair")
    if mode == "duality":
        explanation = explanation_html(
            "What is happening now",
            [
                "The viewer highlights one Voronoi edge and the Delaunay edge connecting the two generating sites.",
                "This is the lecture-9 duality idea made explicit rather than only shown as a final triangulation.",
            ],
        )
    elif mode == "filtered_delaunay":
        explanation = explanation_html(
            "What is happening now",
            [
                "The raw Delaunay graph is filtered by testing the midpoint of each edge against the winding-number boundary.",
                "This view makes the keep/discard decision explicit so the interior graph is not presented as arbitrary.",
            ],
        )
    elif mode == "combined":
        explanation = explanation_html(
            "What is happening now",
            [
                "This is the final proposal for the presentation: use winding number for the boundary and a filtered Delaunay graph for the interior.",
                "The combined view shows the intended outer shape together with the interior structure that survives the boundary test.",
            ],
        )
    else:
        explanation = append_note(explanation_html(
            "What is happening now",
            [
                "The red dashed line is the sweep line and the orange curves are the current beachline arcs.",
                "Bright black/green geometry was created or finalized in this step.",
                "Faded geometry is old context kept only so the step still makes sense.",
            ],
        ), [
            "Legend: orange = beachline, red dashed = sweep line, black = finalized this step, green dotted = created this step.",
        ])
    return fig, fortune_structure_html(state, snapshot, step, mode), explanation


def voronoi_growth_structure_html(state: dict[str, object], snapshot: FortuneSnapshot, step: int) -> str:
    snapshots = voronoi_growth_snapshots(state)
    who_lines = [
        f"step = {step + 1}/{len(snapshots)}",
        f"event = {snapshot.event_kind}",
        f"focus = {format_point(snapshot.focus) if snapshot.focus is not None else 'none'}",
        f"sweep x = {snapshot.sweep_x:.3f}",
    ]
    decision_lines = [
        f"decision = {snapshot.decision or snapshot.event_kind}",
        f"new finished segments = {len(snapshot.finished_segments_this_step)}",
        f"new growing segments = {len(snapshot.new_active_segments_this_step)}",
    ]
    changed_lines = [
        f"carried finished segments = {len(snapshot.carried_finished_segments)}",
        f"carried active segments = {len(snapshot.carried_active_segments)}",
        f"camera bounds = ({snapshot.camera_bounds[0]:.1f}, {snapshot.camera_bounds[1]:.1f}) x ({snapshot.camera_bounds[2]:.1f}, {snapshot.camera_bounds[3]:.1f})",
    ]
    why_lines = [
        "This view isolates Voronoi growth from Fortune mechanics.",
        "Black segments were finalized in this step; green segments started growing in this step.",
        "Older geometry stays faded only as context.",
    ]
    return story_panel(
        "Voronoi Growth State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def voronoi_growth_figure(state: dict[str, object], step: int) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    snapshots = voronoi_growth_snapshots(state)
    snapshot = snapshots[step]
    bounds = snapshot.camera_bounds

    fig = go.Figure(layout=base_layout("Voronoi Growth"))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])
    fig.add_trace(scatter_points(points, names, color="#4a4a4a"))

    for start, end in snapshot.carried_finished_segments:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#cbd5e1", "width": 1.5},
                opacity=0.6,
            )
        )
    for start, end in snapshot.carried_active_segments:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#cfe8db", "width": 2.0, "dash": "dash"},
                opacity=0.65,
            )
        )
    for start, end in snapshot.finished_segments_this_step:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#111827", "width": 4.5},
                opacity=1.0,
            )
        )
    for start, end in snapshot.new_active_segments_this_step:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#10b981", "width": 4.5, "dash": "dot"},
                opacity=1.0,
            )
        )
    if snapshot.focus is not None:
        highlight_point(fig, snapshot.focus, "#e63946", size=18, symbol="x")

    explanation = append_note(
        explanation_html(
            "What is happening now",
            [
                "This view shows only how the Voronoi diagram grows.",
                "Black edges were completed in this step, green edges started growing in this step, and faded lines are older context.",
                "Sweep line, beachline, and circle scaffolding are intentionally hidden here.",
            ],
        ),
        ["Legend: black = finalized this step, green dotted = started this step, faded gray/green = previous context."],
    )
    return fig, voronoi_growth_structure_html(state, snapshot, step), explanation


def filtered_delaunay_structure_html(state: dict[str, object], step: int) -> str:
    records = final_filter_records(state)
    current = records[min(step, len(records) - 1)] if records else None
    who_lines = [
        f"step = {min(step, len(records) - 1) + 1}/{max(1, len(records))}",
        f"edge = {format_point(current['start'])} -> {format_point(current['end'])}" if current else "edge = none",
        f"midpoint = {format_point(current['midpoint'])}" if current else "midpoint = none",
        f"evaluation order = midpoint angle {current['order_angle']:.3f} rad" if current else "evaluation order = none",
    ]
    decision_lines = [
        f"decision = {'keep' if current and current['keep'] else 'discard'}" if current else "decision = none",
        f"winding(midpoint) = {current['winding']:.3f}" if current else "winding(midpoint) = none",
        f"reason = {current['reason']}" if current else "reason = none",
    ]
    changed_lines = [
        f"kept so far = {sum(1 for item in records[: step + 1] if item['keep'])}",
        f"discarded so far = {sum(1 for item in records[: step + 1] if not item['keep'])}",
        f"raw candidate edges = {len(records)}",
        f"final kept edges = {sum(1 for item in records if item['keep'])}",
    ]
    why_lines = [
        "This is the filtering process, not the final result.",
        "Each Delaunay edge is tested independently through its midpoint.",
        "Edges are evaluated in a fixed clockwise order around the polygon center.",
    ]
    return story_panel(
        "Boundary Filter State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def filtered_delaunay_figure(state: dict[str, object], step: int) -> tuple[go.Figure, str, str]:
    points = state["points"]
    polygon = state["winding_polygon"]
    names = make_point_names(points)
    bounds = state["fortune_bounds"]
    records = final_filter_records(state)
    current_index = min(step, len(records) - 1) if records else 0
    current = records[current_index] if records else None

    fig = go.Figure(layout=base_layout("Delaunay With Boundary Filter"))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])
    fig.add_trace(scatter_points(points, names, color="#4a4a4a"))
    fig.add_trace(
        go.Scatter(
            x=[point[0] for point in polygon + [polygon[0]]],
            y=[point[1] for point in polygon + [polygon[0]]],
            mode="lines",
            fill="toself",
            fillcolor="rgba(22, 163, 74, 0.055)",
            line={"color": "#111827", "width": 3},
        )
    )
    for index, item in enumerate(records):
        start, end = item["start"], item["end"]
        color = "#d1d5db"
        width = 1.6
        dash = "solid"
        opacity = 0.55
        if index < current_index:
            color = "#1d4ed8" if item["keep"] else "#9ca3af"
            width = 2.6 if item["keep"] else 1.6
            dash = "solid" if item["keep"] else "dash"
            opacity = 0.95 if item["keep"] else 0.45
        if index == current_index:
            color = "#16a34a" if item["keep"] else "#ef4444"
            width = 4.2
            dash = "solid"
            opacity = 1.0
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": color, "width": width, "dash": dash},
                opacity=opacity,
            )
        )
        if index <= current_index:
            midpoint_color = "#0f766e" if item["keep"] else "#b91c1c"
            midpoint_size = 12 if index == current_index else 9
            highlight_point(fig, item["midpoint"], midpoint_color, size=midpoint_size, symbol="diamond")

    if current is not None:
        midpoint = current["midpoint"]
        start, end = current["start"], current["end"]
        decision_text = "midpoint inside -> keep" if current["keep"] else "midpoint outside -> discard"
        add_text_label(fig, midpoint, decision_text, "#166534" if current["keep"] else "#991b1b", yshift=20)
        fig.add_trace(
            go.Scatter(
                x=[start[0], midpoint[0], end[0]],
                y=[start[1], midpoint[1], end[1]],
                mode="markers",
                marker={
                    "size": [8, 16, 8],
                    "color": ["#4b5563", "#16a34a" if current["keep"] else "#ef4444", "#4b5563"],
                    "symbol": ["circle", "diamond", "circle"],
                    "line": {"color": "white", "width": 2},
                },
                opacity=1.0,
            )
        )

    explanation_lines = [
        "This is not a new triangulation algorithm. It is a cleanup step applied after Delaunay.",
        "For each raw Delaunay edge we test only its midpoint against the winding-number boundary.",
        "If the midpoint is inside the boundary, the edge stays as interior structure; if it is outside, the edge is removed.",
    ]
    if current is not None:
        explanation_lines.append(
            f"Current decision: {'keep' if current['keep'] else 'discard'} because winding(midpoint) = {current['winding']:.3f}."
        )
    return fig, filtered_delaunay_structure_html(state, step), append_note(
        explanation_html("What is happening now", explanation_lines),
        ["Legend: green = current kept edge, red = current rejected edge, blue = previously kept, dashed gray = previously rejected, faint gray = not yet evaluated."],
    )


def duality_structure_html(state: dict[str, object], step: int) -> str:
    pairs = final_duality_pairs(state)
    current = pairs[min(step, len(pairs) - 1)] if pairs else None
    point_names = make_point_names(state["points"])
    who_lines = [
        f"pair = {min(step, len(pairs) - 1) + 1}/{max(1, len(pairs))}",
        f"Voronoi edge = {format_point(current['voronoi'][0])} -> {format_point(current['voronoi'][1])}" if current else "Voronoi edge = none",
        f"Delaunay edge = {point_names.get(current['dual'][0], '?')} -> {point_names.get(current['dual'][1], '?')}" if current else "Delaunay edge = none",
    ]
    decision_lines = [
        "decision = show one Voronoi/Delaunay pair",
        "green = the boundary between two nearest-site regions",
        "blue = the direct connection between those same two sites",
    ]
    changed_lines = [
        "pale green background = complete Voronoi diagram",
        "pale blue background = complete Delaunay graph",
        f"total Voronoi segments = {len(state['fortune'].snapshots[-1].finished_segments)}",
        f"total Delaunay edges = {len(state['fortune'].snapshots[-1].delaunay_edges)}",
    ]
    why_lines = [
        "A Voronoi edge exists where two sites are equally good nearest neighbors.",
        "The Delaunay dual connects exactly those two sites.",
        "So every Voronoi separator has a matching Delaunay connection.",
    ]
    return story_panel(
        "Duality State",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def duality_figure(state: dict[str, object], step: int) -> tuple[go.Figure, str, str]:
    points = state["points"]
    names = make_point_names(points)
    bounds = state["fortune_bounds"]
    final_snapshot = state["fortune"].snapshots[-1]
    pairs = final_duality_pairs(state)
    current = pairs[min(step, len(pairs) - 1)] if pairs else None

    fig = go.Figure(layout=base_layout("Voronoi -> Delaunay Duality"))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])

    for start, end in final_snapshot.finished_segments:
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#bbf7d0", "width": 2.0},
                opacity=0.55,
            )
        )
    for start, end in final_snapshot.delaunay_edges:
        edge_key = tuple(sorted((point_key(start), point_key(end))))
        current_key = tuple(sorted(current["dual"])) if current is not None else None
        is_active = current_key is not None and edge_key == current_key
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#1d4ed8" if is_active else "#bfdbfe", "width": 4.8 if is_active else 1.8},
                opacity=1.0 if is_active else 0.46,
            )
        )
    fig.add_trace(scatter_points(points, names, color="#4a4a4a"))
    if current is not None:
        vor_start, vor_end = current["voronoi"]
        dual_start, dual_end = current["dual"]
        dual_names = [names.get(site, "?") for site in (dual_start, dual_end)]
        dual_midpoint = segment_midpoint(dual_start, dual_end)
        vor_midpoint = segment_midpoint(vor_start, vor_end)
        add_state_annotation(
            fig,
            "Underlying Structures",
            [
                "pale green = Voronoi region boundaries",
                "pale blue = Delaunay neighbor graph",
                f"selected pair links {dual_names[0]} and {dual_names[1]}",
            ],
        )
        fig.add_trace(
            go.Scatter(
                x=[vor_start[0], vor_end[0]],
                y=[vor_start[1], vor_end[1]],
                mode="lines",
                line={"color": "#10b981", "width": 5},
                opacity=1.0,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[dual_start[0], vor_midpoint[0], dual_end[0]],
                y=[dual_start[1], vor_midpoint[1], dual_end[1]],
                mode="lines",
                line={"color": "#f59e0b", "width": 2.0, "dash": "dot"},
                opacity=0.85,
            )
        )
        for site in current["dual"]:
            highlight_point(fig, site, "#f59e0b", size=18, symbol="diamond")
        highlight_point(fig, vor_midpoint, "#10b981", size=13, symbol="square")
        add_text_label(fig, dual_midpoint, f"Delaunay: connect {dual_names[0]} and {dual_names[1]}", "#1d4ed8", yshift=-26)
        add_text_label(fig, vor_midpoint, f"Voronoi: boundary between {dual_names[0]} and {dual_names[1]} regions", "#047857", yshift=18)

    explanation = append_note(
        explanation_html(
            "What is happening now",
            [
                "The pale green structure is the full Voronoi diagram: it partitions the plane into nearest-site regions.",
                "The pale blue structure is the full Delaunay graph: it connects sites whose Voronoi regions touch.",
                "The highlighted pair shows one example of the rule: the green separator exists because the two orange sites are neighbors, and the blue edge records that same neighbor relation.",
            ],
        ),
        ["Legend: pale green = all Voronoi edges, pale blue = all Delaunay edges, strong green/blue/orange = one selected dual pair."],
    )
    return fig, duality_structure_html(state, step), explanation


def combined_structure_html(state: dict[str, object]) -> str:
    records = final_filter_records(state)
    kept = [item for item in records if item["keep"]]
    discarded = [item for item in records if not item["keep"]]
    polygon = state["winding_polygon"]
    who_lines = [
        f"boundary vertices = {len(polygon)}",
        f"raw Delaunay edges = {len(records)}",
        f"kept interior edges = {len(kept)}",
    ]
    decision_lines = [
        "decision = assemble the final view from two different geometric roles",
        "boundary comes from winding / polygon interpretation",
        "interior graph comes from the filtered Delaunay edges",
    ]
    changed_lines = [
        f"discarded edges = {len(discarded)}",
        f"hull shown only as contrast = {'yes' if state.get('hull') else 'no'}",
        "midpoint markers and per-edge diagnostics are hidden here on purpose",
    ]
    why_lines = [
        "This is the final slide-level summary, not the filtering process.",
        "It keeps only the visual elements that support the presentation claim.",
        "The convex hull remains only as a faint comparison baseline.",
    ]
    return story_panel(
        "Combined Result",
        [
            ("1. Who Is Being Processed", who_lines),
            ("2. What Decision Was Taken", decision_lines),
            ("3. What Changed", changed_lines),
            ("4. Why The Result Evolves", why_lines),
        ],
    )


def combined_figure(state: dict[str, object]) -> tuple[go.Figure, str, str]:
    points = state["points"]
    polygon = state["winding_polygon"]
    names = make_point_names(points)
    bounds = state["fortune_bounds"]
    records = final_filter_records(state)
    kept = [item for item in records if item["keep"]]
    hull = state.get("hull", [])

    fig = go.Figure(layout=base_layout("Boundary + Interior Structure"))
    fig.update_xaxes(range=[bounds[0], bounds[1]])
    fig.update_yaxes(range=[bounds[2], bounds[3]])
    fig.add_trace(scatter_points(points, names, color="#4a4a4a"))
    fig.add_trace(
        go.Scatter(
            x=[point[0] for point in polygon + [polygon[0]]],
            y=[point[1] for point in polygon + [polygon[0]]],
            mode="lines",
            line={"color": "#111827", "width": 4.0},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[point[0] for point in polygon + [polygon[0]]],
            y=[point[1] for point in polygon + [polygon[0]]],
            mode="lines",
            fill="toself",
            fillcolor="rgba(37, 99, 235, 0.04)",
            line={"color": "rgba(0,0,0,0)"},
            hoverinfo="skip",
        )
    )
    for item in kept:
        start, end = item["start"], item["end"]
        fig.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"color": "#1d4ed8", "width": 3.2},
                opacity=1.0,
            )
        )
    if hull:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in hull + [hull[0]]],
                y=[point[1] for point in hull + [hull[0]]],
                mode="lines",
                line={"color": "#ef4444", "width": 2, "dash": "dash"},
                opacity=0.42,
            )
        )

    explanation = append_note(explanation_html(
        "What is happening now",
        [
            "This is the final presentation view, not the decision process.",
            "The black outline is the intended outer shape, the blue graph is the interior structure that survived filtering, and the red dashed hull is only a weak baseline for contrast.",
            "Unlike the filter view, this panel intentionally hides midpoint diagnostics so the final message stays clean.",
        ],
    ), [
        "Legend: black = final boundary, blue = final interior structure, faint red dashed = convex-hull baseline.",
    ])
    return fig, combined_structure_html(state), explanation


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
    elif algorithm == "voronoi_growth":
        total = max(1, len(voronoi_growth_snapshots(state)))
        label = "Voronoi growth: isolate only the diagram edges that appear or finish at each step."
    elif algorithm == "fortune":
        total = max(1, len(fortune_event_snapshots(state)))
        label = "Fortune sweep: inspect the current event, the decision taken, and the exact geometric delta of the step."
    elif algorithm == "filtered_delaunay":
        total = max(1, len(final_filter_records(state)))
        label = "Filtered Delaunay: inspect one keep/discard decision at a time."
    elif algorithm == "combined":
        total = 1
        label = "Combined result: outer boundary from winding number, interior graph from filtered Delaunay."
    else:
        total = max(1, len(final_duality_pairs(state)))
        label = "Voronoi / Delaunay duality: inspect one pure edge-pair correspondence at a time."
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
    elif algorithm == "voronoi_growth":
        figure, structure, explanation = voronoi_growth_figure(stored_state, step)
    elif algorithm == "fortune":
        figure, structure, explanation = fortune_figure(stored_state, step, "fortune")
    elif algorithm == "filtered_delaunay":
        figure, structure, explanation = filtered_delaunay_figure(stored_state, step)
    elif algorithm == "combined":
        figure, structure, explanation = combined_figure(stored_state)
    else:
        figure, structure, explanation = duality_figure(stored_state, step)

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


def render_view(
    algorithm: str,
    step: int,
    point_mode: str,
    count: int,
    seed: int,
    stored_state: dict[str, object] | None,
    custom_points: list[Point] | None,
):
    figure, header, structure, explanation, step_update, new_state, _, _ = render_algorithm(
        algorithm,
        step,
        point_mode,
        count,
        seed,
        stored_state,
        custom_points,
    )
    return figure, header, structure, explanation, step_update, new_state


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
                The plot shows the geometry, while the right-side panels answer four questions explicitly:
                who is being processed, what decision was taken, what changed, and why the result evolves.
                """
            )

            state = gr.State(None)
            custom_points = gr.State([])
            point_count = gr.State(14)
            seed = gr.State(4)

            with gr.Row():
                algorithm = gr.Dropdown(
                    choices=[
                        ("Convex Hull", "convex_hull"),
                        ("Winding Number (Closed)", "winding_closed"),
                        ("Winding Number (Open)", "winding_open"),
                        ("Fortune Sweep", "fortune"),
                        # ("Voronoi Growth", "voronoi_growth"),
                        ("Voronoi -> Delaunay Duality", "duality"),
                        ("Delaunay With Boundary Filter", "filtered_delaunay"),
                        ("Combined Boundary + Interior", "combined"),
                    ],
                    value="convex_hull",
                    label="Algorithm",
                )
                point_mode = gr.Dropdown(
                    choices=[
                        ("Repo polygon p1", "p1"),
                        ("Repo polygon p2", "p2"),
                        ("Repo polygon p3", "p3"),
                        ("Repo polygon p4", "p4"),
                    ],
                    value="p2",
                    label="Dataset",
                )

            with gr.Row():
                prev_button = gr.Button("Previous Step", variant="secondary")
                next_button = gr.Button("Next Step", variant="primary")
                step = gr.Slider(0, 20, value=0, step=1, label="Step")
                regenerate = gr.Button("Regenerate / Recompute", variant="secondary")

            with gr.Row():
                with gr.Column(scale=5):
                    plot = gr.Plot(label="Geometry")
                with gr.Column(scale=6):
                    header = gr.HTML()
                    structure = gr.HTML()
                    explanation = gr.HTML()

            inputs = [algorithm, step, point_mode, point_count, seed, state, custom_points]
            outputs = [plot, header, structure, explanation, step, state]

            algorithm.change(render_view, inputs=inputs, outputs=outputs)
            step.change(render_view, inputs=inputs, outputs=outputs)
            point_mode.change(render_view, inputs=inputs, outputs=outputs)
            regenerate.click(render_view, inputs=inputs, outputs=outputs)

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
                render_view,
                inputs=inputs,
                outputs=outputs,
            )

    return demo


if __name__ == "__main__":
    launch().launch()
