import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  title(
    slide,
    ctx,
    "FDM Motivation",
    "Why FDM gives us this problem",
    ""
  );
  await addAsset(slide, ctx, "concept_slide_02_internet.png", 84, 150, 1110, 412, "fdm slice motivation");
  card(slide, ctx, 126, 596, 470, 68, "Why this matters", "Each printed layer becomes a 2D geometry problem: contour, inside-outside logic, and a usable path.", C.orange);
  card(slide, ctx, 654, 596, 466, 68, "Link to the talk", "That is why boundary recovery and interior structure belong to the same pipeline.", C.green);
  foot(slide, ctx, 2);
  return slide;
}
