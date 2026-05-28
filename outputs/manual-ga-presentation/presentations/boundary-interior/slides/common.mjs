export const C = {
  ink: "#111827",
  muted: "#64748b",
  bg: "#f8fafc",
  panel: "#ffffff",
  line: "#dbe4f0",
  orange: "#ea580c",
  red: "#dc2626",
  green: "#059669",
  blue: "#2563eb",
  cyan: "#0891b2",
  purple: "#7c3aed",
};

export const ASSET_DIR =
  "/Users/edu/Desktop/USI/semestre 1/GA/GA_presentation/GA_presentation/outputs/manual-ga-presentation/presentations/boundary-interior/assets";

export function svgData(svg) {
  return `data:image/svg+xml;base64,${Buffer.from(svg, "utf8").toString("base64")}`;
}

export function addBg(slide, ctx) {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: C.bg });
  ctx.addShape(slide, { x: 0, y: 0, w: 12, h: ctx.H, fill: C.orange });
}

export function title(slide, ctx, kicker, heading, sub = "") {
  addBg(slide, ctx);
  ctx.addText(slide, {
    text: kicker.toUpperCase(),
    x: 58,
    y: 38,
    w: 680,
    h: 28,
    fontSize: 13,
    color: C.orange,
    bold: true,
    typeface: "Aptos",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    text: heading,
    x: 56,
    y: 70,
    w: 790,
    h: 82,
    fontSize: 35,
    color: C.ink,
    bold: true,
    typeface: "Aptos Display",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  if (sub) {
    ctx.addText(slide, {
      text: sub,
      x: 58,
      y: 150,
      w: 820,
      h: 48,
      fontSize: 18,
      color: C.muted,
      typeface: "Aptos",
      insets: { left: 0, right: 0, top: 0, bottom: 0 },
    });
  }
}

export function foot(slide, ctx, n) {
  ctx.addText(slide, {
    text: `GA presentation · ${String(n).padStart(2, "0")}`,
    x: 1030,
    y: 680,
    w: 190,
    h: 20,
    fontSize: 12,
    color: "#94a3b8",
    align: "right",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function card(slide, ctx, x, y, w, h, heading, body, accent = C.blue) {
  ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    fill: C.panel,
    line: { style: "solid", fill: C.line, width: 1 },
  });
  ctx.addShape(slide, { x, y, w: 6, h, fill: accent });
  ctx.addText(slide, {
    text: heading,
    x: x + 22,
    y: y + 18,
    w: w - 42,
    h: 28,
    fontSize: 18,
    bold: true,
    color: C.ink,
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    text: body,
    x: x + 22,
    y: y + 54,
    w: w - 42,
    h: h - 70,
    fontSize: 15,
    color: C.muted,
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export async function addSvg(slide, ctx, svg, x, y, w, h, alt = "diagram") {
  await ctx.addImage(slide, { dataUrl: svgData(svg), x, y, w, h, fit: "contain", alt });
}

export async function addAsset(slide, ctx, filename, x, y, w, h, alt = "algorithm visual") {
  await ctx.addImage(slide, { path: `${ASSET_DIR}/${filename}`, x, y, w, h, fit: "contain", alt });
}

export const arrow = (x1, y1, x2, y2, color = C.ink) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="3" marker-end="url(#arrow)"/>`;

export function defs() {
  return `<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="${C.ink}"/></marker></defs>`;
}
