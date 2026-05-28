import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Running Example", "Our slice-like input is the repo polygon `p2`", "We use one real repo polygon through the talk so the algorithms stay connected.");
  await addAsset(slide, ctx, "actual_p2_polygon.png", 105, 210, 595, 360, "repo polygon p2");
  card(slide, ctx, 745, 220, 350, 96, "Why `p2` is useful", "It is not convex. So the example immediately exposes where a simple outer envelope loses information.", C.orange);
  card(slide, ctx, 745, 348, 350, 96, "What to notice", "There is a visible inward part of the shape. That feature must survive if we want the real boundary.", C.blue);
  card(slide, ctx, 745, 476, 350, 96, "Why we keep one dataset", "It lets the audience compare all algorithms on the same geometry instead of changing examples every slide.", C.green);
  foot(slide, ctx, 4);
  return slide;
}
