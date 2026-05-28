from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


ROOT = Path(__file__).resolve().parents[4]
ASSET = Path(__file__).resolve().parent / "assets"
ASSET.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

from apps.interactive_viewer import build_scenarios, final_duality_pairs, final_filter_records, fortune_event_snapshots


state = build_scenarios("p2", 14, 4)
points = state["points"]
poly = state["winding_polygon"]
hull = state["hull"]
final = state["fortune"].snapshots[-1]
records = final_filter_records(state)
pairs = final_duality_pairs(state)

COL = {
    "ink": "#111827",
    "muted": "#64748b",
    "orange": "#ea580c",
    "red": "#dc2626",
    "green": "#059669",
    "blue": "#2563eb",
    "cyan": "#0891b2",
}


def setup(ax, title=None):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.16
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e5e7eb", lw=0.8)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")
    ax.tick_params(labelsize=8, colors="#64748b")
    if title:
        ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=COL["ink"], pad=10)


def draw_points(ax, pts=points, color=COL["ink"]):
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=55, c=color, edgecolors="white", linewidths=1.2, zorder=5)
    for i, p in enumerate(pts):
        ax.text(p[0] + 5, p[1] + 5, f"p{i}", fontsize=8, color=COL["ink"], zorder=6)


def save(fig, name):
    fig.savefig(ASSET / name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def coords(pts):
    return [(p[0], p[1]) for p in pts]


fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "actual repo polygon p2")
ax.add_patch(Polygon(coords(poly), closed=True, facecolor="#eff6ff", edgecolor=COL["ink"], linewidth=2.4, zorder=1))
draw_points(ax)
ax.text(0.02, 0.03, "ordered polygon data, not only a point cloud", transform=ax.transAxes, fontsize=10, color=COL["muted"])
save(fig, "actual_p2_polygon.png")

fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "convex hull baseline")
ax.add_patch(Polygon(coords(poly), closed=True, facecolor="#e0f2fe", edgecolor=COL["ink"], linewidth=2.2, alpha=0.45, zorder=1))
ax.plot([p[0] for p in hull + [hull[0]]], [p[1] for p in hull + [hull[0]]], color=COL["red"], lw=3.4, ls="--", zorder=3)
draw_points(ax)
ax.text(0.02, 0.04, "red hull covers points but loses the concavity", transform=ax.transAxes, fontsize=10, color=COL["red"], fontweight="bold")
save(fig, "actual_convex_hull_failure.png")

q = state["winding_query"]
fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.1))
for ax, closed, trace, ttl in [
    (axs[0], True, state["winding_closed_trace"], "closed polygon"),
    (axs[1], False, state["winding_open_trace"], "open polygon"),
]:
    setup(ax, ttl)
    path = poly + [poly[0]] if closed else poly
    ax.plot([p[0] for p in path], [p[1] for p in path], color=COL["ink"], lw=2.3, zorder=2)
    if not closed:
        ax.plot([poly[-1][0], poly[0][0]], [poly[-1][1], poly[0][1]], color=COL["red"], lw=2.2, ls="--", alpha=0.8, zorder=2)
    edge = trace[min(2, len(trace) - 1)]
    ax.plot([edge["start"][0], edge["end"][0]], [edge["start"][1], edge["end"][1]], color=COL["green"], lw=5, zorder=4)
    ax.plot([q[0], edge["start"][0]], [q[1], edge["start"][1]], color="#ef476f", lw=2.2, zorder=3)
    ax.plot([q[0], edge["end"][0]], [q[1], edge["end"][1]], color=COL["cyan"], lw=2.2, zorder=3)
    ax.scatter([q[0]], [q[1]], s=95, c=COL["orange"], edgecolors="white", linewidths=1.3, zorder=6)
    draw_points(ax)
axs[0].text(0.02, 0.04, "last-to-first edge included", transform=axs[0].transAxes, fontsize=9, color=COL["muted"])
axs[1].text(0.02, 0.04, "red dashed edge is not summed", transform=axs[1].transAxes, fontsize=9, color=COL["red"])
save(fig, "actual_winding_open_closed.png")

snapshots = fortune_event_snapshots(state)
snap = snapshots[min(5, len(snapshots) - 1)]
fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "Fortune sweep event view")
ax.axvline(snap.sweep_x, color=COL["red"], lw=2.3, ls="--")
for seg in snap.finished_segments:
    ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], color="#94a3b8", lw=1.5, alpha=0.75)
for seg in snap.active_segments:
    ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], color=COL["green"], lw=2.2, ls=":", alpha=0.85)
for line in snap.beachline:
    if line:
        ax.plot([p[0] for p in line], [p[1] for p in line], color=COL["orange"], lw=2.4)
if snap.focus:
    ax.scatter([snap.focus[0]], [snap.focus[1]], s=120, marker="x", c=COL["red"], linewidths=3, zorder=8)
draw_points(ax)
ax.text(0.02, 0.04, "red = event/sweep; orange = beachline; green = growing Voronoi", transform=ax.transAxes, fontsize=9, color=COL["muted"])
save(fig, "actual_fortune_event.png")

current = pairs[2] if len(pairs) > 2 else (pairs[0] if pairs else None)
fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "Voronoi -> Delaunay duality")
for s, e in final.finished_segments:
    ax.plot([s[0], e[0]], [s[1], e[1]], color="#86efac", lw=1.8, alpha=0.7, zorder=1)
for s, e in final.delaunay_edges:
    ax.plot([s[0], e[0]], [s[1], e[1]], color="#bfdbfe", lw=1.7, alpha=0.8, zorder=2)
if current:
    vs, ve = current["voronoi"]
    ds, de = current["dual"]
    ax.plot([vs[0], ve[0]], [vs[1], ve[1]], color=COL["green"], lw=4.5, zorder=5)
    ax.plot([ds[0], de[0]], [ds[1], de[1]], color=COL["blue"], lw=4.5, zorder=6)
    ax.scatter([ds[0], de[0]], [ds[1], de[1]], s=95, c=COL["orange"], edgecolors="white", linewidths=1.3, zorder=7)
draw_points(ax)
ax.text(0.02, 0.04, "green separator and blue connection are the same neighbor relation", transform=ax.transAxes, fontsize=9, color=COL["muted"])
save(fig, "actual_duality.png")

current_index = min(5, len(records) - 1)
fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "Delaunay boundary filter")
ax.add_patch(Polygon(coords(poly), closed=True, facecolor="#ecfdf5", edgecolor=COL["ink"], linewidth=2.3, alpha=0.7, zorder=1))
for i, item in enumerate(records):
    s, e = item["start"], item["end"]
    col, lw, ls, alpha = "#d1d5db", 1.2, "-", 0.6
    if i < current_index:
        col = COL["blue"] if item["keep"] else "#9ca3af"
        lw = 2 if item["keep"] else 1.4
        ls = "-" if item["keep"] else "--"
        alpha = 0.9 if item["keep"] else 0.45
    if i == current_index:
        col = COL["green"] if item["keep"] else COL["red"]
        lw, alpha = 4.2, 1
    ax.plot([s[0], e[0]], [s[1], e[1]], color=col, lw=lw, ls=ls, alpha=alpha, zorder=3)
    if i <= current_index:
        m = item["midpoint"]
        ax.scatter([m[0]], [m[1]], s=55 if i == current_index else 35, marker="D", c=COL["green"] if item["keep"] else COL["red"], edgecolors="white", linewidths=1, zorder=7)
draw_points(ax)
ax.text(0.02, 0.04, "each edge is accepted/rejected by midpoint winding test", transform=ax.transAxes, fontsize=9, color=COL["muted"])
save(fig, "actual_filtered_delaunay.png")

fig, ax = plt.subplots(figsize=(6.4, 4.3))
setup(ax, "final boundary + interior")
ax.add_patch(Polygon(coords(poly), closed=True, facecolor="#eff6ff", edgecolor=COL["ink"], linewidth=2.8, alpha=0.7, zorder=1))
for item in [r for r in records if r["keep"]]:
    s, e = item["start"], item["end"]
    ax.plot([s[0], e[0]], [s[1], e[1]], color=COL["blue"], lw=2.7, zorder=3)
ax.plot([p[0] for p in hull + [hull[0]]], [p[1] for p in hull + [hull[0]]], color=COL["red"], lw=1.8, ls="--", alpha=0.45, zorder=2)
draw_points(ax)
ax.text(0.02, 0.04, "black = winding boundary; blue = filtered Delaunay; red = hull", transform=ax.transAxes, fontsize=9, color=COL["muted"])
save(fig, "actual_combined.png")

print(f"assets written to {ASSET}")
