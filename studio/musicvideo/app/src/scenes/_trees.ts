// Shared drawing for "The Trees Nobody Planted": karaoke text, the TREES counter, line-drawn
// Sahel trees (flat-topped acacias), stumps, shoots and grain. All Canvas2D, deterministic in t.
import { Lyrics, type Line, type Word } from '../engine/lyrics';
import { rgba } from '../engine/palette';
import { F, font, glyphX, measure } from '../engine/type';
import { clamp, ease, hash, lerp, mulberry32, prog, TAU } from '../engine/util';

export type C2 = CanvasRenderingContext2D;

// ------------------------------------------------------------------ karaoke
export interface LyricStyle {
  family?: string;
  size?: number;
  tracking?: number;
  sung?: string; // colour of sung words
  unsung?: string; // colour of words not yet sung (shown early as a preview)
  hot?: string; // colour of the word being sung
  align?: 'left' | 'center' | 'right';
  preview?: number; // seconds before a word starts that it fades in (dim)
  pop?: number; // px the current word rises while sung
  maxWidth?: number; // wrap width
  lineHeight?: number;
  emphasis?: Record<string, { family?: string; color?: string; scale?: number }>;
}

/** Layout a line into wrapped rows of words (positions relative to x,y top-left of first baseline). */
export function layoutLine(words: Word[], s: LyricStyle) {
  const size = s.size ?? 72, fam = s.family ?? F.archivo(100, 900), tr = s.tracking ?? 0;
  const space = measure(' ', fam, size, tr);
  const rows: { w: Word; x: number; width: number; fam: string; size: number }[][] = [[]];
  let x = 0;
  for (const w of words) {
    const em = s.emphasis?.[norm(w.w)];
    const f2 = em?.family ?? fam, s2 = size * (em?.scale ?? 1);
    const width = measure(w.w, f2, s2, tr);
    if (s.maxWidth && x > 0 && x + width > s.maxWidth) { rows.push([]); x = 0; }
    rows[rows.length - 1]!.push({ w, x, width, fam: f2, size: s2 });
    x += width + space;
  }
  return rows.map((r) => ({ items: r, width: r.length ? r[r.length - 1]!.x + r[r.length - 1]!.width : 0 }));
}

/** Karaoke line: words fade in dim before they're sung, light up as sung, the current word pops. Returns the block height. */
export function drawLyric(c: C2, line: Line, t: number, x: number, y: number, s: LyricStyle = {}, alpha = 1): number {
  const size = s.size ?? 72, lh = s.lineHeight ?? size * 1.05;
  const rows = layoutLine(line.words, s);
  c.save();
  c.textBaseline = 'alphabetic';
  rows.forEach((row, ri) => {
    const ox = s.align === 'center' ? x - row.width / 2 : s.align === 'right' ? x - row.width : x;
    for (const it of row.items) {
      const w = it.w;
      const pre = s.preview ?? 0.35;
      const vis = prog(t, w.start - pre, w.start, ease.outCubic);
      if (vis <= 0) continue;
      const sp = Lyrics.wordProgress(w, t);
      const on = t >= w.start;
      const em = s.emphasis?.[norm(w.w)];
      const hotK = on ? clamp(1 - (t - w.end) / 0.25) : 0;
      const lift = (s.pop ?? 0) * (on ? Math.sin(Math.PI * Math.min(1, sp)) : 0);
      c.font = font(it.fam, it.size);
      c.letterSpacing = `${s.tracking ?? 0}px`;
      const base = on ? (em?.color ?? s.sung ?? rgba('bone', 1)) : (s.unsung ?? rgba('bone', 0.22));
      c.globalAlpha = alpha * (on ? 1 : vis);
      c.fillStyle = base;
      c.fillText(w.w, ox + it.x, y + ri * lh - lift);
      if (hotK > 0 && s.hot) {
        c.globalAlpha = alpha * hotK;
        c.fillStyle = s.hot;
        c.fillText(w.w, ox + it.x, y + ri * lh - lift);
      }
    }
  });
  c.restore();
  return rows.length * lh;
}

/** Character wipe of a whole line in one font (for typed / written text). */
export function typedLine(c: C2, line: Line, t: number, x: number, y: number, fam: string, size: number, color: string, caret = false) {
  const n = Math.floor(Lyrics.lineCharProgress(line, t + 0.02));
  const txt = line.text.slice(0, n);
  c.font = font(fam, size);
  c.fillStyle = color;
  c.fillText(txt, x, y);
  if (caret && n < line.text.length && t > line.start - 0.5) {
    const cx = x + glyphX(line.text, n, fam, size);
    if (Math.floor(t * 3) % 2 === 0 || n > 0) c.fillRect(cx + 2, y - size * 0.8, Math.max(2, size * 0.08), size * 0.95);
  }
  return n;
}

export const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

// ------------------------------------------------------------------ the counter
const fmt = (v: number) => Math.round(v).toLocaleString('en-US');

/** Rolling-digit counter (mono), with a small label. Digits roll like an odometer between values. */
export function drawCounter(c: C2, x: number, y: number, value: number, o: { size?: number; label?: string; color?: string; labelColor?: string; align?: 'left' | 'center' | 'right'; digits?: number; glow?: number } = {}) {
  const size = o.size ?? 120;
  const digits = o.digits ?? 9;
  const fam = F.mono(400);
  const v = Math.max(0, value);
  const intStr = Math.floor(v).toString().padStart(digits, '0');
  // odometer: the last digit rolls continuously, others snap when the lower ones wrap
  const chars: { ch: string; next: string; f: number }[] = [];
  for (let i = 0; i < digits; i++) {
    const place = Math.pow(10, digits - 1 - i);
    const dv = v / place;
    const d = Math.floor(dv) % 10;
    const frac = dv - Math.floor(dv);
    // only roll when the place below is about to wrap
    const roll = place === 1 ? frac : clamp((frac * place - (place - 1)) / 1);
    chars.push({ ch: String(d), next: String((d + 1) % 10), f: 0 * roll });
  }
  const text = fmt(Math.floor(v)).padStart(digits + Math.floor((digits - 1) / 3), ' ');
  // lay out with commas, using the full-width string for positions
  const groups: string[] = [];
  let k = 0;
  const lead = Math.floor(v) === 0 ? digits - 1 : digits - Math.floor(v).toString().length;
  for (let i = 0; i < digits; i++) {
    if (i > 0 && (digits - i) % 3 === 0) groups.push(',');
    groups.push(String(i));
  }
  c.save();
  c.font = font(fam, size);
  const cw = measure('0', fam, size);
  const commaW = cw * 0.6;
  const total = digits * cw + Math.floor((digits - 1) / 3) * commaW;
  let cx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x;
  const col = o.color ?? rgba('bone', 1);
  c.textBaseline = 'alphabetic';
  for (const g of groups) {
    if (g === ',') {
      const di = Number(groups[groups.indexOf(g) - 1] ?? 0);
      c.globalAlpha = 1;
      c.fillStyle = col;
      c.fillText(',', cx - cw * 0.1, y);
      cx += commaW;
      continue;
    }
    const i = Number(g);
    const it = chars[i]!;
    const dim = i < lead;
    c.save();
    c.beginPath();
    c.rect(cx - 2, y - size * 0.86, cw + 4, size * 1.02);
    c.clip();
    const off = it.f * size * 0.98;
    c.fillStyle = col;
    c.globalAlpha = dim ? 0.18 : 1;
    c.fillText(it.ch, cx, y - off);
    c.fillText(it.next, cx, y - off + size * 0.98);
    c.restore();
    cx += cw;
  }
  if (o.label) {
    c.font = font(F.mono(500), Math.max(14, size * 0.16));
    c.letterSpacing = `${size * 0.03}px`;
    c.fillStyle = o.labelColor ?? rgba('bone', 0.6);
    const lx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x;
    c.fillText(o.label, lx, y + size * 0.36);
  }
  c.restore();
  void text; void k;
  return total;
}

// ------------------------------------------------------------------ trees
export interface TreeOpts { color?: string; width?: number; growth?: number; seed?: number; sway?: number; fall?: number; leaf?: string; leafAlpha?: number }

/**
 * A flat-topped Sahel acacia drawn in hairlines: trunk, a fork, spreading branches and a flat
 * hatched canopy. (x, y) = base of the trunk, h = height. growth 0..1 draws it from the ground up.
 * fall 0..1 tips it over to the right around its base.
 */
export function drawAcacia(c: C2, x: number, y: number, h: number, o: TreeOpts = {}) {
  const g = clamp(o.growth ?? 1);
  if (g <= 0) return;
  const r = mulberry32(o.seed ?? 1);
  c.save();
  c.translate(x, y);
  if (o.fall) c.rotate(ease.inCubic(clamp(o.fall)) * (Math.PI / 2) * (r() > 0.5 ? 1 : -1));
  c.rotate((o.sway ?? 0) * 0.02);
  c.strokeStyle = o.color ?? rgba('bone', 0.9);
  c.lineWidth = o.width ?? Math.max(1.2, h * 0.012);
  c.lineCap = 'round';
  const trunkH = h * 0.55;
  const tg = clamp(g / 0.45);
  // trunk (slightly bent)
  const bend = (r() - 0.5) * h * 0.08;
  c.beginPath();
  c.moveTo(0, 0);
  c.quadraticCurveTo(bend, -trunkH * 0.5 * tg, bend * 0.6, -trunkH * tg);
  c.stroke();
  const bg = clamp((g - 0.35) / 0.4);
  const canopyY = -h * 0.92;
  const span = h * (0.75 + r() * 0.25);
  if (bg > 0) {
    // branches fanning up to the canopy line
    const n = 5;
    for (let i = 0; i < n; i++) {
      const u = i / (n - 1) - 0.5;
      const ex = u * span * (0.8 + r() * 0.3), ey = canopyY + (r() - 0.5) * h * 0.06;
      const sx = bend * 0.6, sy = -trunkH;
      c.beginPath();
      c.moveTo(sx, sy);
      c.quadraticCurveTo(sx + (ex - sx) * 0.3, sy + (ey - sy) * 0.8, lerp(sx, ex, bg), lerp(sy, ey, bg));
      c.stroke();
    }
  }
  const cg = clamp((g - 0.6) / 0.4);
  if (cg > 0) {
    // the flat crown: a thin lens of hatching
    const cw = span * 1.15 * ease.outCubic(cg), ch = h * 0.16;
    c.save();
    c.beginPath();
    c.ellipse(bend * 0.3, canopyY - ch * 0.15, cw / 2, ch / 2, 0, Math.PI, 0);
    c.quadraticCurveTo(bend * 0.3, canopyY + ch * 0.25, bend * 0.3 - cw / 2, canopyY - ch * 0.15);
    c.closePath();
    if (o.leaf) {
      c.globalAlpha = (o.leafAlpha ?? 0.35) * cg;
      c.fillStyle = o.leaf;
      c.fill();
      c.globalAlpha = 1;
    }
    c.clip();
    c.lineWidth = Math.max(0.8, h * 0.006);
    for (let i = -12; i <= 12; i++) {
      const hx = bend * 0.3 + (i / 12) * cw * 0.6;
      c.beginPath();
      c.moveTo(hx - ch, canopyY + ch);
      c.lineTo(hx + ch, canopyY - ch);
      c.stroke();
    }
    c.restore();
    c.beginPath();
    c.ellipse(bend * 0.3, canopyY - ch * 0.15, cw / 2, ch / 2, 0, Math.PI, 0);
    c.stroke();
  }
  c.restore();
}

/** A cut stump with growth rings visible from the side (a short cylinder). */
export function drawStump(c: C2, x: number, y: number, w: number, o: { color?: string; rings?: number; top?: boolean } = {}) {
  const h = w * 0.55;
  c.save();
  c.strokeStyle = o.color ?? rgba('bone', 0.9);
  c.lineWidth = Math.max(1, w * 0.03);
  c.beginPath();
  c.moveTo(x - w / 2, y);
  c.lineTo(x - w / 2 * 0.92, y - h);
  c.moveTo(x + w / 2, y);
  c.lineTo(x + w / 2 * 0.92, y - h);
  c.stroke();
  c.beginPath();
  c.ellipse(x, y - h, w / 2 * 0.92, w * 0.16, 0, 0, TAU);
  c.stroke();
  if (o.rings) {
    c.lineWidth = Math.max(0.7, w * 0.012);
    for (let i = 1; i < o.rings; i++) {
      const k = i / o.rings;
      c.beginPath();
      c.ellipse(x, y - h, w / 2 * 0.92 * k, w * 0.16 * k, 0, 0, TAU);
      c.stroke();
    }
  }
  c.restore();
}

/** A young shoot (curved stem + two leaves) from (x,y), height h, grown g. */
export function drawShoot(c: C2, x: number, y: number, h: number, g: number, color: string, seed = 1, lean = 0) {
  const k = clamp(g);
  if (k <= 0) return;
  const r = mulberry32(seed);
  const hh = h * ease.outCubic(k);
  const bx = (r() - 0.5) * h * 0.3 + lean * h;
  c.save();
  c.strokeStyle = color;
  c.fillStyle = color;
  c.lineWidth = Math.max(1.2, h * 0.05);
  c.lineCap = 'round';
  c.beginPath();
  c.moveTo(x, y);
  c.quadraticCurveTo(x + bx * 0.2, y - hh * 0.6, x + bx, y - hh);
  c.stroke();
  const lk = clamp((k - 0.4) / 0.6);
  if (lk > 0) {
    for (const s of [-1, 1]) {
      c.beginPath();
      const lx = x + bx, ly = y - hh * 0.92;
      c.ellipse(lx + s * h * 0.14 * lk, ly - h * 0.03, h * 0.14 * lk, h * 0.05 * lk, s * -0.5, 0, TAU);
      c.fill();
    }
  }
  c.restore();
}

/** A scruffy bush: tangled short strokes around (x,y), radius r. `jitter` animates the scribble. */
export function drawScruff(c: C2, x: number, y: number, r: number, seed: number, color: string, jitter = 0, n = 70) {
  const rr = mulberry32(seed);
  c.save();
  c.strokeStyle = color;
  c.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const a = -Math.PI * (0.05 + rr() * 0.9);
    const d = r * (0.2 + rr() * 0.8);
    const sx = x + Math.cos(a) * d * 0.3, sy = y;
    const ex = x + Math.cos(a) * d + (hash(i, seed, Math.floor(jitter * 24)) - 0.5) * r * 0.12 * (jitter > 0 ? 1 : 0);
    const ey = y + Math.sin(a) * d * 0.8;
    c.lineWidth = 0.8 + rr() * 1.4;
    c.beginPath();
    c.moveTo(sx, sy);
    c.quadraticCurveTo((sx + ex) / 2 + (rr() - 0.5) * r * 0.3, (sy + ey) / 2 + (rr() - 0.5) * r * 0.2, ex, ey);
    c.stroke();
  }
  c.restore();
}

/** Mono annotation with a leader line (field-notes style callout). */
export function callout(c: C2, x: number, y: number, tx: number, ty: number, text: string, o: { color?: string; size?: number; alpha?: number; align?: 'left' | 'right' } = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0) return;
  c.save();
  c.globalAlpha = a;
  c.strokeStyle = o.color ?? rgba('bone', 0.7);
  c.fillStyle = o.color ?? rgba('bone', 0.7);
  c.lineWidth = 1;
  c.beginPath();
  c.moveTo(x, y);
  c.lineTo(tx, ty);
  c.lineTo(tx + (o.align === 'right' ? -40 : 40), ty);
  c.stroke();
  c.beginPath();
  c.arc(x, y, 3, 0, TAU);
  c.fill();
  c.font = font(F.mono(500), o.size ?? 16);
  c.letterSpacing = '2px';
  c.textAlign = o.align === 'right' ? 'right' : 'left';
  c.fillText(text, tx + (o.align === 'right' ? -48 : 48), ty + 5);
  c.restore();
}

/** Small mono header used at the top of plates ("FIELD NOTES · …"). */
export function plateHeader(c: C2, text: string, right: string, alpha = 1, color = rgba('bone', 0.55)) {
  c.save();
  c.globalAlpha = alpha;
  c.font = font(F.mono(500), 15);
  c.letterSpacing = '3px';
  c.fillStyle = color;
  c.fillText(text, 96, 72);
  c.textAlign = 'right';
  c.fillText(right, 1920 - 96, 72);
  c.fillRect(96, 86, 1920 - 192, 1);
  c.restore();
}
