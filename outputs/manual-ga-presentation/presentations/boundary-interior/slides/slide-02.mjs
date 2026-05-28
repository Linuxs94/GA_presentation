import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  title(
    slide,
    ctx,
    "FDM Motivation",
    "Why FDM gives us this problem",
    "Layer-by-layer fabrication turns one 3D object into many 2D geometry tasks."
  );
  await addAsset(slide, ctx, "concept_slide_02.png", 112, 178, 1030, 395, "fdm slice motivation");
  card(slide, ctx, 126, 590, 455, 74, "Why this matters", "Each slice becomes a 2D geometry problem: recover the contour, decide what is inside, and turn that into usable structure.", C.orange);
  card(slide, ctx, 700, 590, 420, 74, "Link to the talk", "This is why hulls, winding, Voronoi, and Delaunay belong in the same pipeline instead of appearing as separate tricks.", C.green);
  foot(slide, ctx, 2);
  return slide;
}
