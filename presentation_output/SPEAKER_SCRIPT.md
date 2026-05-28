# Speaker Script


## Slide 1 - From slice data to a usable structure
- Today I will present our geometry pipeline.
- The starting point is fairly simple.
- We have slice-like 2D data, and we want to turn it into something geometrically useful.
- More precisely, we want to recover the shape in a way that is meaningful for the task.
- For us, that means two things.
- We want the correct outer boundary.
- And we also want a sensible structure inside that boundary.
- for this Convex hull gives us a baseline.
- Winding number helps us reason about the true boundary.
- Delaunay helps us build an interior graph.
- And in the end, those pieces are combined into one result.
- I will begin with the fabrication motivation.
- Then I will move through the boundary part and the interior part.
- After that, I will show the same ideas step by step in the interactive viewer.

## Slide 2 - Why FDM gives us this problem
- The motivation comes from fused deposition modeling printing.
- It is the printing process where material is deposited layer by layer.
- Once you look at it that way, a 3D object becomes a stack of 2D slices.
- And each slice creates its own geometry problem.
- A raw point set is not enough.
- The printer needs a contour.   it can actually follow.
- It also needs a clear notion of what lies inside that contour.
- So this is where computational geometry becomes relevant.
- A fabrication task turns    into a sequence of      boundary and         inside-outside questions in the plane.
- We are not trying to build a full slicer here.
- We are only using FDM as the practical reason for asking this geometry question.
- The important idea is that slice data by itself is too poor.
- To make it useful, we have to recover structure from it.

## Slide 3 - One slice has two jobs
- Once we focus on one slice, the problem separates naturally into two parts.
- First, we need the boundary.
- In other words, we want the real outer shape of the slice.
- Second, we need some structure inside the shape.
- The outline alone is not enough for that.
- So the talk also has two parts.
- First boundary, then interior.

## Slide 4 - Our slice-like input is the repo polygon `p2`
- This is `p2` from our repository.
- I use it as the running example for the whole talk.
- The important point is that it is not convex.
- So the differences between the algorithms become visible immediately.

## Slide 5 - Convex hull is a clean baseline, but it changes the shape
- The first method to try is convex hull.
- It is a natural baseline because it gives one outer envelope around the points.
- In the viewer, the main things to watch are the current candidate point, the stack, and the turn test.
- If the turn is acceptable, the point stays.
- If not, the top of the stack is removed.
- So the local rule is simple.
- The real issue is the result.
- Convex hull always tries to produce a convex boundary.
- For `p2`, that is exactly the problem.
- The shape is concave, so the hull removes the inward part.
- It gives a clean cover, but not the boundary we actually want.

## Demo - Convex Hull on `p2`
- lets look at the visualisation 
- At the beginning, there is no real decision yet because we do not have enough points.
- Once three points are available, the first turn is tested.
- If the turn is fine, the point stays.
- If the turn is wrong for the hull, the last point is removed.
- In this example, as you can see one new point can trigger more than one pop.
- After the lower chain is finished, the upper chain is built with the same rule in the opposite direction.
- And when the hull is complete, the key point is easy to see:
- the inward part of the shape disappears.
- So the algorithm is clear, but for this example the result is not the boundary we want.

## Slide 6 - Winding number asks the right boundary question
- After convex hull, we need something that does not erase the shape.
- This is where winding number becomes useful.
- It asks a different question.
- Instead of building one convex outer cover, it asks whether a query point lies inside or outside the polygon.
- The polygon is processed edge by edge around that query point.
- Each edge contributes a signed angle.
- Those contributions are accumulated.
- If the polygon winds around the point, the total is non-zero.
- If it does not, the total stays close to zero.
- That is why winding number fits our boundary problem much better.
- It respects the actual polygon.
- It does not force convexity.
- And it keeps the inside-outside decision explicit from start to finish.

## Slide 7 - Closed and open polygons are not the same
- There is one subtle point that matters here.
- Winding number depends on whether the polygon is treated as closed or open.
- In closed mode, the last vertex is connected back to the first one.
- So the query point is tested against a full loop.
- In open mode, that final edge is missing.
- And once that edge disappears, the result changes.
- This is important because it reminds us that the algorithm is not working on a vague sketch.
- It is working on a precisely defined geometric object.


## Demo - Winding Number on `p2`
- lets look at the visualisation
- I first show the closed version.
- Here the polygon is treated as a full loop.
- At each step, one edge contributes a signed angle around the query point.
- Those contributions are added one after another.
- What matters is not one edge by itself.
- What matters is the final accumulated result.
- Then I switch to the open version.
- Now the closing edge is missing.
- So the object is no longer the same.
- And because of that, the winding result changes.
- This is why closed and open polygons must be treated differently.

## Slide 8 - Why we need interior structure
- At this stage, the boundary part is in much better shape.
- But the project is still incomplete.
- The boundary tells us where the slice ends.
- It does not tell us how to organize the inside.
- For that, we want local neighbors, not arbitrary long connections.
- So winding number solves one part of the problem, but not the whole problem.

## Slide 9 - Fortune sweep builds the Voronoi structure event by event
- To move toward interior structure, we first look at Voronoi.
- The construction method we use is Fortune sweep.
- This step is useful because it shows that the structure is built, not guessed.
- Site events insert new arcs into the beachline.
- Circle events remove arcs and finalize parts of the Voronoi diagram.
- So the geometry evolves through local updates.
- This gives us a principled way to construct the Voronoi structure.

## Slide 10 - Delaunay gives the interior neighbor graph
- Once Voronoi is in place, we move to Delaunay.
- Delaunay is the dual of Voronoi.
- If two Voronoi regions touch, then the corresponding sites become neighbors in the Delaunay graph.
- This is the main reason Delaunay is useful here.
- It is not an arbitrary graph placed on the points.
- It is grounded in nearest-neighbor geometry.
- So it gives us a principled candidate structure for the interior.
- That already makes it much better than drawing random internal links.
- Still, one problem remains.
- Raw Delaunay does not know anything about our intended boundary.
- Some candidate edges may fall outside the actual shape.
- So Delaunay gives strong interior candidates,
- but it still needs to be constrained by the boundary logic from the earlier part of the talk.

## Slide 11 - Winding filters Delaunay into the final interior structure
- This is the final integration step.
- Delaunay proposes candidate interior edges.
- Winding number tells us whether something belongs inside the boundary.
- So we combine the two.
- For each Delaunay edge, we test its midpoint with winding number.
- If the midpoint lies inside the boundary, the edge is kept.
- If it lies outside, the edge is removed.
- This is where the two halves of the presentation finally come together.
- Winding answers the membership question.
- Delaunay answers the neighborhood question.
- Together, they produce a boundary-aware interior graph.
- That is the final result of the pipeline.

## Demo - Fortune, Duality, Filter, and Combined Result
- I first show `Fortune Sweep`.
- The main idea here is that the Voronoi structure is built event by event.
- Site events add new arcs.
- Circle events remove arcs and finalize edges.
- Then I show `Voronoi -> Delaunay Duality`.
- Here the main message is that Voronoi and Delaunay describe the same local neighbor relation in two different forms.
- After that, I show `Delaunay With Boundary Filter`.
- For each candidate edge, we test its midpoint with winding number.
- If the midpoint is inside the boundary, the edge is kept.
- If it is outside, the edge is removed.
- Finally I show `Combined Boundary + Interior`.
- This is the final result.
- The boundary is recovered with winding number.
- The interior graph comes from filtered Delaunay.
- So the full pipeline is now visible in one view.

## Final closing sentence
- In one sentence, the project starts from slice-like polygon data, recovers the boundary with winding number, and builds a boundary-aware interior structure by filtering Delaunay with that same boundary logic.

## App command

```bash
cd "/Users/edu/Desktop/USI/semestre 1/GA/GA_presentation/GA_presentation"
source .venv/bin/activate
python presentation.py --interactive
```
