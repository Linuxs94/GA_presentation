import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Interior Graph", "Delaunay gives the interior neighbor graph", "It is better than arbitrary links because it comes from Voronoi region adjacency.");
  await addAsset(slide, ctx, "actual_duality.png", 100, 215, 610, 360, "Voronoi Delaunay duality");
  card(slide, ctx, 755, 220, 355, 95, "Why Delaunay is principled", "If two Voronoi regions touch, their sites become neighbors. So the graph is grounded in nearest-site geometry.", C.green);
  card(slide, ctx, 755, 345, 355, 95, "Why it is better", "It preserves local neighborhood relations instead of inventing random or long interior connections.", C.blue);
  card(slide, ctx, 755, 470, 355, 95, "But not enough alone", "Raw Delaunay does not know which edges fall outside the intended boundary. So we still need the winding test.", C.orange);
  foot(slide, ctx, 10);
  return slide;
}
