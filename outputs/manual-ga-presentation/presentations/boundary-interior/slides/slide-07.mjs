import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Boundary Assumption", "Closed and open polygons are not the same", "The final edge matters. If the loop is not closed, the winding sum changes.");
  await addAsset(slide, ctx, "actual_winding_open_closed.png", 70, 215, 725, 330, "winding closed and open");
  card(slide, ctx, 830, 220, 330, 95, "Closed mode", "The last vertex connects back to the first one, so the query point sees the full loop.", C.green);
  card(slide, ctx, 830, 345, 330, 95, "Open mode", "That final edge is missing. The algorithm does not silently invent it, so the result changes.", C.blue);
  card(slide, ctx, 830, 470, 330, 95, "Why this slide matters", "It makes the boundary assumption explicit and gives a clean transition from hulls to inside-outside tests.", C.orange);
  foot(slide, ctx, 7);
  return slide;
}
