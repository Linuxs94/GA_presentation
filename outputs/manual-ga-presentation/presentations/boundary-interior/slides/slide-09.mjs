import { C, title, foot, card, addAsset } from "./common.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  title(slide, ctx, "Voronoi Construction", "Fortune sweep builds the Voronoi structure event by event", "Site and circle events change the beachline and gradually produce the interior geometry.");
  await addAsset(slide, ctx, "actual_fortune_event.png", 95, 215, 610, 360, "Fortune sweep event");
  card(slide, ctx, 750, 220, 350, 95, "Who is processed", "At each step the event is either a new site or a circle event where one beachline arc disappears.", C.orange);
  card(slide, ctx, 750, 345, 350, 95, "What changes", "The beachline changes, Voronoi segments start growing, and some edges become final.", C.green);
  card(slide, ctx, 750, 470, 350, 95, "What to say in the demo", "Show one site event and one circle event. The goal is the mechanism, not every low-level detail.", C.blue);
  foot(slide, ctx, 9);
  return slide;
}
