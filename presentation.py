import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import math

### Utilities
def read_polygon(file_path):
    polygon = []
    with open(file_path, 'r') as f:
        for line in f:
            x, y = map(float, line.strip().split())
            polygon.append((x, y))
    return polygon

### inside-outside test
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

# fill grid 
def inside_out(xs, ys, polygon, resolution, discrete):
    grid = []

    for y in ys[:-1]:
        row = []
        for x in xs[:-1]:
            cx = x + resolution/2
            cy = y + resolution/2

            wn=winding_number(cx, cy, polygon)

            if discrete:
                row.append(1 if abs(wn) > 0.5 else 0) # <- - -
            else:
                row.append(wn)

        grid.append(row)
    return grid

### Plotting section
def plotter(titles, objects, 
            rows, cols,
            xmin, xmax,
            ymin, ymax,
            xs=None, ys=None,
            object_type='polygon'):

    fig, axs = plt.subplots(rows, cols, figsize=(10,10))

    if rows == 1 and cols == 1:
        axs = [axs]
    else:
        axs = axs.flatten()

    for i, ax in enumerate(axs):
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(titles[i])
        # bounding box
        rect = Rectangle((xmin, ymin),
                            xmax-xmin,
                            ymax-ymin,
                            facecolor='none',
                            edgecolor='black',
                            linewidth=2)
        ax.add_patch(rect)

        if xs is not None and ys is not None:
            ax.set_xlim(xs[0], xs[-1])
            ax.set_ylim(ys[0], ys[-1])

        obj = objects[i]

        if object_type == 'polygon':
            poly_colors = ['skyblue', 'lightgreen']
            for idx, poly in enumerate(obj):
                color = poly_colors[idx % len(poly_colors)]
                ax.add_patch(
                    Polygon(poly,
                            closed=True,
                            facecolor=color,
                            edgecolor='black',
                            alpha=0.5)
                )

        elif object_type == 'boolean':
            for (x1,y1),(x2,y2) in obj:
                ax.plot([x1,x2], [y1,y2], color='black', linewidth=1)

    plt.show()

def plot_chain(field, polygon, xmin, xmax, ymin, ymax):

    plt.figure(figsize=(8,8))

    plt.imshow(field,
               origin='lower',
               extent=[xmin,xmax,ymin,ymax],
               cmap='coolwarm',
               interpolation='nearest')

    plt.colorbar(label="Winding number")

    xs_poly = [p[0] for p in polygon]
    ys_poly = [p[1] for p in polygon]
    plt.plot(xs_poly, ys_poly, color='black', linewidth=2)

    plt.title("winding number")
    plt.gca().set_aspect('equal')
    plt.show()

### MAIN ###
# grid
resolution = 1 # cell size, not quantity

# Read polygons
poly1 = read_polygon("p1.txt")
poly2 = read_polygon("p2.txt")
polygons = [poly1, poly2]

## grid construction
# bounds for the grid
all_x = [x for poly in polygons for x,_ in poly]
all_y = [y for poly in polygons for _,y in poly]

padding = 10
# add "resolution" cause continuous to discrete conversion
xmin = min(all_x) - resolution - padding
xmax = max(all_x) + resolution + padding
ymin = min(all_y) - resolution - padding
ymax = max(all_y) + resolution + padding

# grid of grid coordinates
xs = [xmin + i*resolution for i in range(int((xmax-xmin)/resolution)+1)]
ys = [ymin + i*resolution for i in range(int((ymax-ymin)/resolution)+1)]

# Generate grid with wn
grid1 = inside_out(xs, ys, poly1, resolution, False)
grid2 = inside_out(xs, ys, poly2, resolution, False)

#wn inside, it should be use grid
plot_chain(grid1, poly1, xmin, xmax, ymin, ymax)
plot_chain(grid2, poly2, xmin, xmax, ymin, ymax)

# Generate grid with wn
grid1 = inside_out(xs, ys, poly1, resolution, True)
grid2 = inside_out(xs, ys, poly2, resolution, True)

#wn inside, it should be use grid
plot_chain(grid1, poly1, xmin, xmax, ymin, ymax)
plot_chain(grid2, poly2, xmin, xmax, ymin, ymax)
