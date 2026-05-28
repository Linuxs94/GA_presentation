import { C, title, foot, card, addSvg, defs, arrow } from "./common.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  title(
    slide,
    ctx,
    "Geometrical Algorithms",
    "From slice data to a usable structure",
    "Recover the boundary first. Then build a useful interior structure."
  );
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="780" height="330" viewBox="0 0 780 330">
    ${defs()}
    <rect x="20" y="44" width="170" height="220" rx="18" fill="#fff" stroke="${C.line}" stroke-width="2"/>
    <path d="M55 98 L150 98 L150 226 L106 182 L55 226 Z" fill="#fde7da" stroke="${C.orange}" stroke-width="5" stroke-linejoin="round"/>
    <circle cx="80" cy="118" r="7" fill="${C.ink}"/><circle cx="136" cy="118" r="7" fill="${C.ink}"/><circle cx="136" cy="214" r="7" fill="${C.ink}"/><circle cx="106" cy="182" r="7" fill="${C.ink}"/><circle cx="55" cy="226" r="7" fill="${C.ink}"/>
    <text x="105" y="292" font-family="Aptos" font-size="20" text-anchor="middle" fill="${C.ink}">slice-like input</text>
    ${arrow(212, 154, 292, 154)}
    <rect x="308" y="44" width="180" height="220" rx="18" fill="#fff" stroke="${C.line}" stroke-width="2"/>
    <path d="M340 98 L440 98 L440 226 L392 184 L340 226 Z" fill="none" stroke="${C.ink}" stroke-width="5" stroke-linejoin="round"/>
    <path d="M340 98 L440 98 L440 226 L340 226 Z" fill="none" stroke="${C.red}" stroke-width="4" stroke-dasharray="10 8" opacity="0.7"/>
    <text x="398" y="292" font-family="Aptos" font-size="20" text-anchor="middle" fill="${C.ink}">boundary question</text>
    ${arrow(510, 154, 590, 154)}
    <rect x="606" y="44" width="150" height="220" rx="18" fill="#fff" stroke="${C.line}" stroke-width="2"/>
    <path d="M640 102 L725 102 M640 102 L682 184 M725 102 L682 184 M630 230 L682 184 M735 230 L682 184" stroke="${C.blue}" stroke-width="5" stroke-linecap="round"/>
    <circle cx="640" cy="102" r="8" fill="${C.ink}"/><circle cx="725" cy="102" r="8" fill="${C.ink}"/><circle cx="682" cy="184" r="8" fill="${C.ink}"/><circle cx="630" cy="230" r="8" fill="${C.ink}"/><circle cx="735" cy="230" r="8" fill="${C.ink}"/>
    <text x="680" y="292" font-family="Aptos" font-size="20" text-anchor="middle" fill="${C.ink}">interior structure</text>
  </svg>`;
  await addSvg(slide, ctx, svg, 240, 210, 800, 255, "pipeline overview");
  card(slide, ctx, 72, 500, 350, 118, "Core claim", "This is one pipeline, not a list of unrelated algorithms. We solve boundary recovery and interior organization together.", C.orange);
  card(slide, ctx, 448, 500, 664, 118, "Final idea", "Convex hull is the baseline. Winding gives inside-outside logic for the real boundary. Delaunay gives candidate interior edges. Winding filters those edges.", C.green);
  foot(slide, ctx, 1);
  return slide;
}
