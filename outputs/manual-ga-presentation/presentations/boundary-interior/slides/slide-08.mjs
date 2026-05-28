import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Interior Goal", "Why we need interior structure", "The contour gives the shell, but the inside still needs a local geometric organization.");
  await addAsset(slide, ctx, "concept_slide_08.png", 118, 180, 1030, 390, "why interior structure");
  card(slide, ctx, 126, 590, 458, 74, "Main point", "A contour tells us where the slice ends, but it says almost nothing about relations inside the slice.", C.red);
  card(slide, ctx, 658, 590, 462, 74, "Bridge forward", "Voronoi and Delaunay are useful because they add interior organization without abandoning the geometry of the slice.", C.green);
  foot(slide, ctx, 8);
  return slide;
}
