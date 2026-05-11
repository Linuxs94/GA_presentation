import math
import numpy as np
import matplotlib.pyplot as plt

# winding number
def winding_number(x, y, polygon):

    total_angle = 0.0
    n = len(polygon)

    for i in range(n-1):

        x1 = polygon[i][0] - x
        y1 = polygon[i][1] - y

        x2 = polygon[i+1][0] - x
        y2 = polygon[i+1][1] - y

        cross = x1*y2 - y1*x2
        dot   = x1*x2 + y1*y2

        angle = math.atan2(cross, dot)
        total_angle += angle

    return total_angle / (2*math.pi)

# the queue sorted
def event_angles(polygon, cx, cy):
    angles = []

    for vx, vy in polygon[:-1]:
        angle = math.atan2(vy - cy, vx - cx)
        angles.append(angle)
    return sorted(angles)

def inside_out_events(polygon, cx, cy, discrete):

    field = []

    angles = event_angles(polygon, cx, cy)

    for angle in angles:

        x = cx + math.cos(angle)
        y = cy + math.sin(angle)

        wn = winding_number(x, y, polygon)

        if discrete:
            value = 1 if abs(wn) > 0.5 else 0
        else:
            value = wn

        field.append((x, y, value))

    return field

# winding number is ploted as a field
def compute_bounds(polygons, margin=2.0):

    all_x = []
    all_y = []

    for poly in polygons:
        for x, y in poly:
            all_x.append(x)
            all_y.append(y)

    xmin = min(all_x) - margin
    xmax = max(all_x) + margin
    ymin = min(all_y) - margin
    ymax = max(all_y) + margin

    return xmin, xmax, ymin, ymax


# PLOT FIELD
def build_winding_field(polygon, xmin, xmax, ymin, ymax, resolution=300, discrete=False):

    xs = np.linspace(xmin, xmax, resolution)
    ys = np.linspace(ymin, ymax, resolution)

    field = np.zeros((resolution, resolution))

    for j, y in enumerate(ys):
        for i, x in enumerate(xs):

            wn = winding_number(x, y, polygon)

            if discrete:
                field[j, i] = 1 if abs(wn) > 0.5 else 0
            else:
                field[j, i] = wn

    return field, xs, ys

def plot_wn(field, xs, ys, polygon, title="Winding Field", discrete=False):

    fig, ax = plt.subplots(figsize=(8, 8))

    img = ax.imshow(
        field,
        origin="lower",
        extent=[xs[0], xs[-1], ys[0], ys[-1]],
        cmap="coolwarm",
        interpolation="nearest"
    )

    # do not close the polygon if discrete=False
    if discrete:
        poly_x = [p[0] for p in polygon] + [polygon[0][0]]
        poly_y = [p[1] for p in polygon] + [polygon[0][1]]
    else:
        poly_x = [p[0] for p in polygon]
        poly_y = [p[1] for p in polygon]

    ax.plot(poly_x, poly_y, color="black", linewidth=2)

    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(ys[0], ys[-1])

    ax.set_aspect("equal")
    ax.set_title(title)

    plt.colorbar(img, ax=ax, label="Winding Number")

    plt.show()