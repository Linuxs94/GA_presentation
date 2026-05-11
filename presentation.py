import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math
import heapq
from read_points import read_polygon, point_plotter
from data_struct import Point, Event, Arc, Segment, PriorityQueue
from Graham import get_convex_hull, CH_plotter
from windingN import winding_number, event_angles, inside_out_events, compute_bounds, build_winding_field, plot_wn
from voronoi import Voronoi, draw_voronoi

### MAIN ###

# # Read polygons
poly1 = read_polygon("p1.txt")
poly2 = read_polygon("p2.txt")

# # only points plot
point_plotter(poly1, "Punti del Poligono 1")
point_plotter(poly2, "Punti del Poligono 2")

# ###########
# # convex hull plot
# ##############
hull1 = get_convex_hull(poly1)
hull2 = get_convex_hull(poly2)

CH_plotter(poly1, hull1, "Convex Hull del Poligono 1")
CH_plotter(poly2, hull2, "Convex Hull del Poligono 2")

##################
# winding number plot
##################
# sweep center -> discuss, centroid?
xmin, xmax, ymin, ymax = compute_bounds([poly1, poly2], margin=2.0)


# CONTINUOUS FIELD
field1, xs, ys = build_winding_field(poly1, xmin, xmax, ymin, ymax, discrete=False)
field2, _, _   = build_winding_field(poly2, xmin, xmax, ymin, ymax, discrete=False)

plot_wn(field1, xs, ys, poly1, "Polygon 1 - Continuous Winding Field", discrete=False)
plot_wn(field2, xs, ys, poly2, "Polygon 2 - Continuous Winding Field", discrete=False)


# DISCRETE FIELD
field1_d, xs, ys = build_winding_field(poly1, xmin, xmax, ymin, ymax, discrete=True)
field2_d, _, _   = build_winding_field(poly2, xmin, xmax, ymin, ymax, discrete=True)

plot_wn(field1_d, xs, ys, poly1, "Polygon 1 - Discrete Field", discrete=True)
plot_wn(field2_d, xs, ys, poly2, "Polygon 2 - Discrete Field", discrete=True)


# Conversione in numpy array per il plotting dei punti
p1_arr = np.array(poly1, dtype=float)
p2_arr = np.array(poly2, dtype=float)

# Creazione figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Voronoi plot
draw_voronoi(ax1, poly1, 'red') 
ax1.plot(p1_arr[:, 0], p1_arr[:, 1], 'bo-', linewidth=0.5, markersize=3) # Punti + bordo
ax1.set_title("Diagramma 1")
ax1.set_aspect('equal')
ax1.grid(True)

# Plot Diagramma 2
draw_voronoi(ax2, poly2, 'orange')
ax2.plot(p2_arr[:, 0], p2_arr[:, 1], 'go-', linewidth=0.5, markersize=3) # Punti + bordo
ax2.set_title("Diagramma 2")
ax2.set_aspect('equal')
ax2.grid(True)

plt.tight_layout()
plt.show()



# DUAL (Voronoi edges -> Delaunay graph)

def delaunay_from_voronoi_vertices(ax, vor, color="blue"):
    drawn = set()

    for p1, p2, p3 in vor.triangles:

        tri = tuple(sorted([
            (p1.x, p1.y),
            (p2.x, p2.y),
            (p3.x, p3.y)
        ]))

        if tri in drawn:
            continue

        drawn.add(tri)

        ax.plot(
            [p1.x, p2.x, p3.x, p1.x],
            [p1.y, p2.y, p3.y, p1.y],
            color=color,
            linewidth=1
        )


p1 = np.array(poly1)
p2 = np.array(poly2)

h1 = np.array(get_convex_hull(poly1))
h2 = np.array(get_convex_hull(poly2))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))



# PLOT 1

v1 = draw_voronoi(ax1, poly1, "red")
delaunay_from_voronoi_vertices(ax1, v1, color="blue")

ax1.plot(p1[:, 0], p1[:, 1], "ko", markersize=3)

ax1.plot(
    np.r_[h1[:, 0], h1[0, 0]],
    np.r_[h1[:, 1], h1[0, 1]],
    "black",
    linewidth=2
)

ax1.set_title("Voronoi + Delaunay + Convex Hull 1")
ax1.set_aspect("equal")
ax1.grid(True)

# PLOT 2
v2 = draw_voronoi(ax2, poly2, "orange")
delaunay_from_voronoi_vertices(ax2, v2, color="green")

ax2.plot(p2[:, 0], p2[:, 1], "ko", markersize=3)

ax2.plot(
    np.r_[h2[:, 0], h2[0, 0]],
    np.r_[h2[:, 1], h2[0, 1]],
    "black",
    linewidth=2
)

ax2.set_title("Voronoi + Delaunay + Convex Hull 2")
ax2.set_aspect("equal")
ax2.grid(True)

plt.tight_layout()
plt.show()