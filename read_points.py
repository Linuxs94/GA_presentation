import matplotlib.pyplot as plt

def read_polygon(file_path):
    polygon = []
    with open(file_path, 'r') as f:
        for line in f:
            x, y = map(float, line.strip().split())
            polygon.append((x, y))
    return polygon

def point_plotter(points, title):
    plt.figure(figsize=(6,6))
    px, py = zip(*points)
    plt.scatter(px, py, color='blue')
    plt.title(title)
    plt.show()
