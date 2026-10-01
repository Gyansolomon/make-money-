// FIG. 4 — the usual answer, on bone paper: a planting form whose grid fills with seedlings on
// "Millions of seedlings", then a wilting wave on "die". A handful survive and stay green.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, hash, lerp, prog } from '../engine/util';
import { Plate } from './_plate';
import { drawLyric, drawShoot, plateHeader } from './_trees';

const COLS = 24, ROWS = 6, X0 = 170, X1 = 1750, Y0 = 560, Y1 = 980;

export default class Seedlings extends Plate {
  override setup() { this.bg = 'bone'; }

  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t;
    const o: PostOverrides = { paper: 1, bloom: 0.2, grain: 0.05, vignette: 0.3 };
    const L = (i: number) => this.line(i - 15);
    plateHeader(c, 'TREE PLANTING PROGRAMME  ·  FORM 7', 'SEEDLINGS ISSUED', 1, rgba('ink', 0.6));
    const fill0 = L(16).words[0]!.start, fill1 = L(16).end + 0.4;
    const dieT = L(17).words[4]!.start;
    const dx = (X1 - X0) / (COLS - 1), dy = (Y1 - Y0) / (ROWS - 1);
    // the form's grid
    c.strokeStyle = rgba('ink', 0.12);
    c.lineWidth = 1;
    for (let i = 0; i <= COLS; i++) { c.beginPath(); c.moveTo(X0 - dx / 2 + i * dx, Y0 - dy * 0.8); c.lineTo(X0 - dx / 2 + i * dx, Y1 + dy * 0.25); c.stroke(); }
    for (let j = 0; j <= ROWS; j++) { c.beginPath(); c.moveTo(X0 - dx / 2, Y0 - dy * 0.8 + j * dy); c.lineTo(X1 + dx / 2, Y0 - dy * 0.8 + j * dy); c.stroke(); }
    let alive = 0, planted = 0;
    for (let i = 0; i < COLS; i++) for (let j = 0; j < ROWS; j++) {
      const k = i * ROWS + j;
      const ta = lerp(fill0, fill1, i / COLS) + hash(k, 1) * 0.12;
      const g = prog(t, ta, ta + 0.35, ease.outBack);
      if (g <= 0) continue;
      planted++;
      const survivor = hash(k, 5) < 0.035;
      const td = dieT + i * 0.045 + hash(k, 2) * 0.2;
      const w = survivor ? 0 : prog(t, td, td + 0.5, ease.outCubic);
      if (w < 0.5) alive++;
      const x = X0 + i * dx, y = Y0 + j * dy;
      const col = w > 0.4 ? rgba('sand', 1) : survivor && t > dieT + 1.2 ? rgba('leaf', 1) : rgba('moss', 1);
      drawShoot(c, x, y, 44 * (1 - 0.45 * w), g, col, k, w * 0.9 * (hash(k, 3) > 0.5 ? 1 : -1));
      if (w > 0.6) {
        c.strokeStyle = rgba('blood', 0.55 * clamp((w - 0.6) * 3));
        c.lineWidth = 2;
        c.beginPath();
        c.moveTo(x - 9, y - 22); c.lineTo(x + 9, y - 4);
        c.moveTo(x + 9, y - 22); c.lineTo(x - 9, y - 4);
        c.stroke();
      }
    }
    // tallies
    c.font = font(F.mono(500), 20);
    c.letterSpacing = '4px';
    c.fillStyle = rgba('ink', 0.7);
    c.fillText(`PLANTED  ${String(planted).padStart(3, '0')}`, 96, 480);
    c.fillStyle = t > dieT ? rgba('blood', 1) : rgba('ink', 0.7);
    c.fillText(`ALIVE    ${String(alive).padStart(3, '0')}`, 420, 480);
    c.fillStyle = rgba('ink', 0.45);
    c.fillText('1 SQUARE = A LOT OF SEEDLINGS', 1250, 480);
    c.letterSpacing = '0px';
    const cur = this.current(t);
    if (cur) drawLyric(c, cur, t, 96, 230, { size: 84, maxWidth: 1600, sung: rgba('ink', 1), unsung: rgba('ink', 0.2), hot: rgba('blood', 1), pop: 6, emphasis: { die: { color: rgba('blood', 1) } } });
    o.zoom = 1 + 0.015 * clamp(1 - Math.abs(t - dieT) / 0.2);
    return o;
  }
}
