// FIG. 3 — what the trees were doing. A soil cross-section: the cut trees' roots still lace the
// soil, rain falls, crops stand. The rain stops on "stops" (the beat drops out with it), the wind
// strips the soil and blows the words away, and a map shows the desert edge sliding south.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, hash, lerp, mulberry32, prog, TAU } from '../engine/util';
import { Plate } from './_plate';
import { drawLyric, drawStump, layoutLine, plateHeader } from './_trees';

const GY = 560;
const STUMPS = [430, 1490];

type Seg = { x0: number; y0: number; x1: number; y1: number; d: number };
function roots(x: number, seed: number): Seg[] {
  const r = mulberry32(seed), out: Seg[] = [];
  const grow = (px: number, py: number, a: number, len: number, d: number, depth: number) => {
    if (depth > 6 || len < 8) return;
    const nx = px + Math.cos(a) * len, ny = Math.min(1060, py + Math.sin(a) * len);
    out.push({ x0: px, y0: py, x1: nx, y1: ny, d });
    const n = r() < 0.55 ? 2 : 1;
    for (let i = 0; i < n; i++) grow(nx, ny, a + (r() - 0.5) * 1.1, len * (0.72 + r() * 0.2), d + len, depth + 1);
  };
  for (let i = 0; i < 5; i++) grow(x, GY + 4, Math.PI * (0.15 + 0.7 * (i / 4)) + (r() - 0.5) * 0.2, 70 + r() * 30, 0, 0);
  return out;
}

export default class Drought extends Plate {
  R: Seg[][] = [];
  override setup() { this.R = STUMPS.map((x, i) => roots(x, 40 + i)); }

  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t;
    const o: PostOverrides = { bloom: 0.55, bloomThreshold: 0.6, grain: 0.065, vignette: 0.45 };
    const L = (i: number) => this.line(i - 10);
    const mapT = L(14).start - 0.3;
    if (t >= mapT) return this.map(c, t, o);

    const stopT = L(12).words[3]!.start + 0.12;
    const windT = L(13).start - 0.1;
    const wind = prog(t, windT, windT + 1.2, ease.inCubic);
    plateHeader(c, 'CROSS-SECTION  ·  FARMLAND', 'AFTER THE TREES', prog(t, 31.25, 31.7));

    // ---- sun (grows hotter once the shade is gone)
    const heat = prog(t, L(11).words[1]!.start, L(11).end + 0.8);
    c.fillStyle = rgba('ember', 0.3 + 0.7 * heat);
    c.beginPath();
    c.arc(1680, 230, 60 + 20 * heat, 0, TAU);
    c.fill();
    c.strokeStyle = rgba('signal', 0.5 * heat);
    c.lineWidth = 2;
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * TAU + t * 0.2, r0 = 100 + 20 * heat;
      c.beginPath();
      c.moveTo(1680 + Math.cos(a) * r0, 230 + Math.sin(a) * r0);
      c.lineTo(1680 + Math.cos(a) * (r0 + 40 * heat), 230 + Math.sin(a) * (r0 + 40 * heat));
      c.stroke();
    }

    // ---- soil: stipple held by the roots, then blown away
    for (let i = 0; i < 900; i++) {
      const x0 = hash(i, 1) * 1920, y0 = GY + 8 + Math.pow(hash(i, 2), 1.6) * 480;
      const lift = y0 < GY + 120 ? wind * (1 - (y0 - GY) / 120) : 0;
      const dx = lift * (600 + hash(i, 3) * 1400) * prog(t, windT + hash(i, 4) * 1.5, windT + 3 + hash(i, 4) * 1.5);
      const dy = -lift * hash(i, 5) * 200 * prog(t, windT, windT + 3);
      c.fillStyle = rgba('sand', 0.25 + 0.35 * hash(i, 6));
      c.fillRect(x0 + dx, y0 + dy, 2.4, 2.4);
    }
    // ground line
    c.fillStyle = rgba('bone', 0.85);
    c.fillRect(0, GY, 1920, 2);

    // ---- roots of the cut trees (lit on "roots", fading as the soil goes)
    const rl = prog(t, L(10).words[1]!.start, L(10).words[1]!.start + 0.8, ease.outCubic);
    const rfade = 1 - 0.7 * prog(t, L(11).start, L(12).start);
    this.R.forEach((segs, k) => {
      c.strokeStyle = rgba('bone', (0.25 + 0.6 * rl) * rfade);
      c.lineWidth = 1.6;
      c.setLineDash(rl > 0.99 && rfade < 0.95 ? [6, 6] : []);
      c.beginPath();
      for (const s of segs) {
        if (s.d > rl * 400) continue;
        c.moveTo(s.x0, s.y0);
        c.lineTo(s.x1, s.y1);
      }
      c.stroke();
      c.setLineDash([]);
      drawStump(c, STUMPS[k]!, GY + 1, 40, { rings: 4 });
      // the shade that used to be there (dashed ghost canopy)
      const sh = prog(t, L(11).words[1]!.start - 0.1, L(11).words[1]!.start + 0.4) * (1 - prog(t, L(11).end, L(11).end + 0.8));
      if (sh > 0) {
        c.strokeStyle = rgba('bone', 0.5 * sh);
        c.setLineDash([8, 8]);
        c.beginPath();
        c.ellipse(STUMPS[k]!, GY - 240, 220, 36, 0, 0, TAU);
        c.stroke();
        c.setLineDash([]);
        c.fillStyle = rgba('ink2', 0.9 * sh);
        c.fillRect(STUMPS[k]! - 220, GY - 8, 440, 6);
        c.font = font(F.mono(500), 15);
        c.letterSpacing = '3px';
        c.fillStyle = rgba('bone', 0.6 * sh);
        c.fillText('SHADE  (GONE)', STUMPS[k]! - 70, GY - 290);
        c.letterSpacing = '0px';
      }
    });
    c.font = font(F.mono(500), 15);
    c.letterSpacing = '3px';
    c.fillStyle = rgba('bone', 0.6 * rl * rfade);
    c.fillText('ROOTS  ·  HOLDING THE SOIL', 640, GY + 440);
    c.letterSpacing = '0px';

    // ---- crops: wilt with the heat, flatten in the wind
    for (let x = 40; x < 1900; x += 26) {
      if (STUMPS.some((s) => Math.abs(s - x) < 40)) continue;
      const wilt = clamp(heat * 0.6 + prog(t, stopT, stopT + 2) * 0.4);
      const flat = prog(t, L(13).words[6]!.start + hash(x, 9) * 0.4, L(13).words[6]!.start + 0.5 + hash(x, 9) * 0.4, ease.inCubic);
      const h = 60 + hash(x, 2) * 20;
      const lean = wilt * 0.7 + flat * 1.0;
      c.strokeStyle = wilt > 0.5 ? rgba('sand', 0.8) : rgba('leaf', 0.75 - 0.4 * wilt);
      c.lineWidth = 1.6;
      c.beginPath();
      c.moveTo(x, GY);
      c.quadraticCurveTo(x, GY - h * 0.6, x + Math.sin(lean) * h, GY - Math.cos(lean) * h);
      c.stroke();
    }

    // ---- rain until "stops"
    if (t < stopT + 0.15) {
      const freeze = t > stopT ? stopT : t;
      c.strokeStyle = rgba('bone', t > stopT ? 0.6 : 0.32);
      c.lineWidth = 1.2;
      c.beginPath();
      for (let i = 0; i < 180; i++) {
        const sp = 1400 + hash(i, 1) * 600;
        const x = hash(i, 2) * 2000 - 40 + (freeze * 120) % 60;
        const y = ((hash(i, 3) * 700 + freeze * sp) % 700) - 100;
        if (y > GY - 30) continue;
        c.moveTo(x, y);
        c.lineTo(x - 6, y + 36);
      }
      c.stroke();
    }
    // a rainfall gauge reads zero
    const gz = prog(t, stopT, stopT + 0.6);
    if (gz > 0) {
      c.font = font(F.mono(500), 22);
      c.letterSpacing = '4px';
      c.fillStyle = rgba('signal', gz);
      c.fillText('RAINFALL  0 mm', 96, 420);
      c.letterSpacing = '0px';
    }

    // ---- lyrics; in the wind the sung words blow away
    const cur = this.current(t, 0.9);
    if (cur) {
      if (cur.i === L(13).i) {
        const rows = layoutLine(cur.words, { size: 76, maxWidth: 1500 });
        rows.forEach((row, ri) => row.items.forEach((it) => {
          const w = it.w;
          const vis = prog(t, w.start - 0.3, w.start);
          if (vis <= 0) return;
          const go = Math.max(0, t - cur.end - 0.1 - w.index * 0.05);
          const dx = go * go * 1600, dy = -go * go * 260 * (0.3 + hash(w.gi, 2));
          c.font = font(it.fam, it.size);
          c.fillStyle = rgba(t >= w.start ? 'bone' : 'bone', (t >= w.start ? 1 : 0.22 * vis) * clamp(1 - go * 2.5));
          c.fillText(w.w, 96 + it.x + dx, 230 + ri * 80 + dy);
          if (go > 0) for (let k = 0; k < 14; k++) {
            c.fillStyle = rgba('sand', 0.6 * clamp(1 - go));
            c.fillRect(96 + it.x + dx - k * 30 * go * hash(k, w.gi) - 10, 230 + ri * 80 + dy - hash(k, 3, w.gi) * 50, 4, 2);
          }
        }));
      } else drawLyric(c, cur, t, 96, 230, { size: 76, maxWidth: 1400, hot: rgba('ember', 1), pop: 6, emphasis: { stops: { color: rgba('signal', 1) } } });
    }
    if (t > stopT && t < windT) o.grain = 0.08;
    o.shake = wind > 0 && t < mapT ? [(hash(Math.round(t * 60), 1) - 0.5) * 6 * (1 - prog(t, windT + 1, windT + 3)), 0] : [0, 0];
    return o;
  }

  /** The desert edge moves south, year by year. */
  private map(c: CanvasRenderingContext2D, t: number, o: PostOverrides): PostOverrides {
    const L14 = this.line(4);
    plateHeader(c, 'WEST AFRICA  ·  DESERT EDGE', 'SCHEMATIC', 1);
    const p = prog(t, L14.words[2]!.start, L14.end + 1.6, ease.inOutCubic);
    const edge = lerp(330, 640, p);
    // sahara: sand hatching above the edge
    c.save();
    c.beginPath();
    c.rect(0, 100, 1920, edge - 100 + 20);
    for (let x = 0; x <= 1920; x += 20) c.lineTo(1920 - x, edge + Math.sin(x * 0.01 + 1) * 18);
    c.clip();
    c.strokeStyle = rgba('sand', 0.55);
    c.lineWidth = 1.2;
    for (let i = -60; i < 120; i++) {
      c.beginPath();
      c.moveTo(i * 22, 100);
      c.lineTo(i * 22 + 900, 1000);
      c.stroke();
    }
    c.restore();
    // edge line
    c.strokeStyle = rgba('signal', 1);
    c.lineWidth = 3;
    c.beginPath();
    for (let x = 0; x <= 1920; x += 20) {
      const y = edge + Math.sin(x * 0.01 + 1) * 18;
      if (x === 0) c.moveTo(x, y); else c.lineTo(x, y);
    }
    c.stroke();
    // old edge (dashed)
    c.setLineDash([10, 10]);
    c.strokeStyle = rgba('bone', 0.4);
    c.lineWidth = 1.5;
    c.beginPath();
    for (let x = 0; x <= 1920; x += 20) {
      const y = 330 + Math.sin(x * 0.01 + 1) * 18;
      if (x === 0) c.moveTo(x, y); else c.lineTo(x, y);
    }
    c.stroke();
    c.setLineDash([]);
    c.font = font(F.archivo(125, 900), 64);
    c.fillStyle = rgba('sand', 1);
    c.fillText('SAHARA', 1420, 240);
    c.font = font(F.mono(500), 18);
    c.letterSpacing = '4px';
    c.fillStyle = rgba('signal', 1);
    c.fillText('DESERT EDGE', 1560, edge - 30);
    c.fillStyle = rgba('bone', 0.7);
    c.fillText('SAHEL  ·  FARMS', 1560, edge + 80);
    c.fillText(`YEAR  ${Math.round(lerp(1968, 1984, p))}`, 96, 160);
    // arrows south
    for (let i = 0; i < 5; i++) {
      const x = 300 + i * 300, y = edge + 40 + ((t * 60 + i * 13) % 40);
      c.fillStyle = rgba('signal', 0.8);
      c.beginPath();
      c.moveTo(x - 12, y);
      c.lineTo(x + 12, y);
      c.lineTo(x, y + 18);
      c.fill();
    }
    c.letterSpacing = '0px';
    drawLyric(c, L14, t, 96, 900, { size: 80, hot: rgba('ember', 1), pop: 6, emphasis: { south: { color: rgba('signal', 1) } } });
    return o;
  }
}
