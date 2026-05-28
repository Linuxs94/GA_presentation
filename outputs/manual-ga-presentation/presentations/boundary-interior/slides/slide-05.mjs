import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Baseline", "Convex hull is a clean baseline, but it changes the shape", "Our monotone chain view sorts the points, builds two stacks, and keeps only convex turns.");
  await addAsset(slide, ctx, "actual_convex_hull_failure.png", 105, 210, 590, 365, "convex hull on p2");
  card(slide, ctx, 745, 220, 350, 100, "What the algorithm does", "It keeps only the points needed for the smallest convex envelope around the set.", C.blue);
  card(slide, ctx, 745, 350, 350, 100, "What the demo shows", "Candidate point, orientation test, stack before, stack after, and the push-or-pop decision.", C.orange);
  card(slide, ctx, 745, 480, 350, 100, "Why it fails here", "The real shape is concave. The hull fills that inward part, so it is the wrong boundary for this slice.", C.red);
  foot(slide, ctx, 5);
  return slide;
}
