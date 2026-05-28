import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Boundary Recovery", "Winding number asks the right boundary question", "Instead of forcing a convex cover, it tests inside versus outside directly.");
  await addAsset(slide, ctx, "actual_winding_open_closed.png", 70, 215, 725, 330, "winding closed and open");
  card(slide, ctx, 830, 220, 330, 95, "Main idea", "Process one edge at a time and add its signed angle contribution around a query point.", C.orange);
  card(slide, ctx, 830, 345, 330, 95, "Why it is better", "It respects the actual polygon. It does not flatten concavities the way convex hull does.", C.green);
  card(slide, ctx, 830, 470, 330, 95, "What to show in the app", "Current edge in green, query point in orange, and the running winding value after each edge.", C.blue);
  foot(slide, ctx, 6);
  return slide;
}
