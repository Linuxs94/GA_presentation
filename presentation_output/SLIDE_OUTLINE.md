# Slide Outline

1. **From slice data to a usable structure**
   Claim: the project is one geometry pipeline with two goals, boundary recovery and interior organization.

2. **Why FDM gives us this problem**
   Claim: layer-by-layer fabrication naturally creates 2D slice problems that need geometric reasoning.

3. **One slice has two jobs**
   Claim: a slice needs both an outer contour and an internal organization, so boundary alone is not enough.

4. **Our slice-like input is the repo polygon `p2`**
   Claim: `p2` is a good running example because its concavity exposes where simple baselines fail.

5. **Convex hull is a clean baseline, but it changes the shape**
   Claim: monotone chain is simple and useful, but convex hull removes concavities and cannot recover the intended boundary.

6. **Winding number asks the right boundary question**
   Claim: winding number tests inside versus outside directly instead of forcing a convex envelope.

7. **Closed and open polygons are not the same**
   Claim: the final edge matters, so boundary assumptions must be explicit.

8. **Why we need interior structure**
   Claim: the contour gives the shell, but the interior still needs a local, geometrically meaningful organization.

9. **Fortune sweep builds the Voronoi structure event by event**
   Claim: Voronoi construction gives a principled view of how interior neighborhood structure emerges.

10. **Delaunay gives the interior neighbor graph**
   Claim: Delaunay is better than arbitrary interior connections because it is the dual of Voronoi adjacency and preserves local neighborhood relations.

11. **Winding filters Delaunay into the final interior structure**
   Claim: winding supplies the boundary test, Delaunay supplies candidate interior edges, and the midpoint filter combines them into one final pipeline.

## Demo Placement

Use short app demos after the relevant slides instead of keeping all demos for the end:

1. After slide 5: `Convex Hull` on `p2`.
2. After slide 7: `Winding Number (Closed)` and `Winding Number (Open)` on `p2`.
3. After slide 11: `Voronoi -> Delaunay Duality`, `Delaunay With Boundary Filter`, and `Combined Boundary + Interior` on `p2`.
