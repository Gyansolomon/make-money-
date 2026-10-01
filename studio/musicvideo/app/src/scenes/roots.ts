// FIG. 6 — the drop. The ground turns to x-ray: under the bush, a cut stump and a living root
// network that blooms out in green. Sap pulses along the roots on the kicks, then the camera pulls
// out to show the same network under every field: a whole forest, hiding underground.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { ease, hash, lerp, mulberry32, prog, pulse } from '../engine/util';
import { Plate } from './_plate';
import { drawLyric, drawScruff, drawStump } from './_trees';

const GY = 470;
type Seg = { x0: number; y0: number; x1: number; y1: number; d: number; w: number };

function network(seed: number): { segs: Seg[]; max: number } {
  const r = mulberry32(seed), segs: Seg[] = [];
  let max = 0;
  const grow = (x: number, y: number, a: number, len: number, d: number, depth: number, w: number) => {
    if (depth > 8 || len < 6) return;
    const nx = x + Math.cos(a) * len, ny = y + Math.sin(a) * len;
    if (ny < GY + 4) return;
    segs.push({ x0: x, y0: y, x1: nx, y1: ny, d, w });
    max = Math.max(max, d + len);
    const n = r() < 0.6 ? 2 : 1;
    for (let i = 0; i < n; i++) grow(nx, ny, a + (r() - 0.5) * 1.0, len * (0.74 + r() * 0.18), d + len, depth + 1, w * 0.72);
  };
  for (let i = 0; i < 7; i++) grow(0, GY + 6, Math.PI * (0.08 + 0.84 * (i / 6)) + (r() - 0.5) * 0.15, 60 + r() * 30, 0, 0, 5);
  return { segs, max };
}

export default class Roots extends Plate {
  N: { segs: Seg[]; max: number }[] = [];
  kicks: number[] = [];
  override setup() {
    this.N = Array.from({ length: 9 }, (_, i) => network(100 + i));
    this.kicks = this.ctx.audio.events('kick', this.ctx.start, this.ctx.end).map(([k]) => k);
  }

  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t, t0 = this.ctx.start;
    const L = (i: number) => this.line(i - 22);
    const o: PostOverrides = { bloom: 0.75, bloomThreshold: 0.5, bloomRadius: 0.6, grain: 0.06, vignette: 0.5 };
    o.flash = pulse(t, t0, 0.08) * 0.25;
    const out = prog(t, L(24).words[1]!.start, L(24).end + 0.4, ease.inOutCubic);
    const z = lerp(1, 0.3, out);
    // camera: pivot on the stump at (960, GY)
    c.save();
    c.translate(960, lerp(GY, 520, out));
    c.scale(z, z);
    c.translate(0, -GY);
    // soil x-ray tint
    c.fillStyle = rgba('ink2', 1);
    c.fillRect(-4000, GY, 8000, 3000);
    c.fillStyle = rgba('bone', 0.8);
    c.fillRect(-4000, GY, 8000, 2 / z);
    // kick pulses
    let lastK = -1;
    for (const k of this.kicks) if (k <= t) lastK = k;
    this.N.forEach((net, i) => {
      const ox = (i - 4) * 700;
      if (i !== 4 && out <= 0) return;
      const g = i === 4 ? prog(t, t0, t0 + 1.1, ease.outCubic) : prog(out, 0.1 + Math.abs(i - 4) * 0.08, 0.5 + Math.abs(i - 4) * 0.08);
      const reach = g * net.max;
      const alive = prog(t, L(23).words[3]!.start, L(23).words[4]!.start + 0.3);
      for (const s of net.segs) {
        if (s.d > reach) continue;
        const k = Math.min(1, (reach - s.d) / 60);
        const sap = lastK >= 0 && alive > 0 ? Math.exp(-Math.pow((s.d - (t - lastK) * 900) / 60, 2)) : 0;
        c.strokeStyle = rgba(sap > 0.3 ? 'bone' : 'leaf', 0.55 + 0.45 * Math.max(sap, k * 0.4 + alive * 0.3));
        c.lineWidth = Math.max(1, s.w) + sap * 3;
        c.beginPath();
        c.moveTo(ox + s.x0, s.y0);
        c.lineTo(ox + lerp(s.x0, s.x1, k), lerp(s.y0, s.y1, k));
        c.stroke();
      }
      // above ground: what everyone saw
      drawScruff(c, ox, GY, 60, 7 + i, rgba('sand', 0.55), 0, 60);
      if (i === 4 || out > 0.3) drawStump(c, ox, GY + 2, 50, { rings: 6, color: rgba('bone', 0.95) });
    });
    // stump callout
    const ca = prog(t, L(22).words[3]!.start, L(22).words[3]!.start + 0.25) * (1 - out);
    if (ca > 0) {
      c.globalAlpha = ca;
      c.strokeStyle = rgba('bone', 0.8);
      c.lineWidth = 1;
      c.beginPath();
      c.moveTo(25, GY - 20); c.lineTo(110, GY - 110); c.lineTo(200, GY - 110);
      c.stroke();
      c.font = font(F.mono(500), 18);
      c.letterSpacing = '3px';
      c.fillStyle = rgba('bone', 0.95);
      c.fillText('STUMP  ·  CUT DOWN YEARS AGO', 210, GY - 104);
      c.fillStyle = rgba('leaf', 1);
      c.fillText('ROOTS  ·  ALIVE', 210, GY + 140);
      c.globalAlpha = 1;
      c.letterSpacing = '0px';
    }
    c.restore();
    if (out > 0.6) {
      c.font = font(F.mono(500), 20);
      c.letterSpacing = '5px';
      c.fillStyle = rgba('leaf', prog(out, 0.6, 1));
      c.fillText('EVERY FIELD  ·  THOUSANDS OF LIVING ROOT SYSTEMS', 96, 1000);
      c.letterSpacing = '0px';
    }
    const cur = this.current(t, 0.7);
    if (cur) drawLyric(c, cur, t, 96, 200, { size: 84, maxWidth: 1600, hot: rgba('leaf', 1), pop: 6, emphasis: { alive: { color: rgba('leaf', 1) }, tree: { color: rgba('leaf', 1) }, forest: { color: rgba('leaf', 1) } } });
    o.zoom = 1 + 0.012 * f.a.kick;
    void hash;
    return o;
  }
}
