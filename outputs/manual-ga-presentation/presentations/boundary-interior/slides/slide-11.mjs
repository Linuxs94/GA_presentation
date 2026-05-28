import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide11(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Final Pipeline", "Winding filters Delaunay into the final interior structure", "Delaunay proposes candidate edges. Winding keeps only the ones that stay inside the shape.");
  await addAsset(slide, ctx, "actual_combined.png", 95, 215, 610, 360, "combined boundary and interior");
  card(slide, ctx, 750, 220, 360, 95, "Filter rule", "Take one Delaunay edge, test its midpoint with winding number, keep it if the midpoint is inside.", C.orange);
  card(slide, ctx, 750, 345, 360, 95, "Final picture", "Black is the recovered boundary. Blue is the interior graph that survives the boundary test.", C.blue);
  card(slide, ctx, 750, 470, 360, 95, "End message", "Convex hull gives the baseline, winding gives the real boundary logic, and Delaunay gives the interior candidates.", C.green);
  foot(slide, ctx, 11);
  return slide;
}
