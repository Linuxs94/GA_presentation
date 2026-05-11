import math
import matplotlib.pyplot as plt

# GRAHAM SCAN - CONVEX HULL
def get_convex_hull(points):
    n = len(points)
    if n < 3:
        return points

    # Trova il punto con la coordinata Y minima (e X minima in caso di parità)
    pivot = min(points, key=lambda p: (p[1], p[0]))

    # Funzione per calcolare l'orientamento (prodotto vettoriale)
    # > 0 in senso antiorario, < 0 orario, 0 collineari
    def cross_product(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Ordina i punti in base all'angolo polare rispetto al pivot
    def polar_angle(p):
        return math.atan2(p[1] - pivot[1], p[0] - pivot[0])

    sorted_points = sorted(points, key=lambda p: (polar_angle(p), math.dist(pivot, p)))

    # Costruisci l'hull
    hull = []
    for p in sorted_points:
        while len(hull) >= 2 and cross_product(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)
    
    # Chiudi il poligono per la visualizzazione (aggiungi il primo punto alla fine)
    hull.append(hull[0])
    return hull

def CH_plotter(points, hull, title):
    plt.figure(figsize=(6,6))
    px, py = zip(*points)
    hx, hy = zip(*hull)
    plt.scatter(px, py, color='blue', label='Punti Originali')
    plt.plot(hx, hy, color='red', linewidth=2, label='Convex Hull')
    plt.legend()
    plt.title(title)
    plt.show()