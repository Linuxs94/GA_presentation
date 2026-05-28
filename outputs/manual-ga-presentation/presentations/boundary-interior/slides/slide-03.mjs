import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  title(
    slide,
    ctx,
    "Problem Split",
    "One slice has two jobs",
    "Boundary alone is not enough. The inside must also be organized."
  );
  await addAsset(slide, ctx, "concept_slide_03.png", 118, 180, 1030, 390, "two slice jobs");
  card(slide, ctx, 128, 590, 464, 74, "Reading the slide", "The same slice is viewed twice: first as a boundary problem, then as an interior organization problem.", C.orange);
  card(slide, ctx, 654, 590, 466, 74, "Why this matters", "This split is the reason the presentation has two phases instead of trying to force one algorithm to do everything.", C.green);
  foot(slide, ctx, 3);
  return slide;
}
