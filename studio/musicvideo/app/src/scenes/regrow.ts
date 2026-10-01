// FIG. 7 — farmer-managed natural regeneration. Shoots crowd a stump; "cutting" is struck out;
// one strong shoot is kept and the rest trimmed; it grows into an acacia; the land fills with trees
// while the counter rolls to 200,000,000; then a field of dots: food for 2.5 million more people.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, hash, lerp, prog, TAU } from '../engine/util';
import { Plate } from './_plate';
import { drawAcacia, drawCounter, drawLyric, drawShoot, drawStump, layoutLine } from './_trees';

const SX = 960, SY = 820;

export default class Regrow extends Plate {
  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t;
    const L = (i: number) => this.line(i - 25);
    const o: PostOverrides = { bloom: 0.65, bloomThreshold: 0.55, grain: 0.055, vignette: 0.4 };
    const landT = L(27).start - 0.3, dotsT = L(28).start - 0.3;

    if (t < landT) {
      // ---- the stump, its shoots, the choice
      const keepT = L(26).words[0]!.start, trimT = L(26).words[3]!.start, growT = L(26).words[5]!.start;
      const tree = prog(t, growT, landT, ease.inOutCubic);
      c.fillStyle = rgba('bone', 0.8);
      c.fillRect(0, SY, 1920, 2);
      drawStump(c, SX, SY, 110, { rings: 5 });
      for (let i = 0; i < 7; i++) {
        const keep = i === 3;
        const g = prog(t, this.ctx.start + 0.2 + i * 0.12, this.ctx.start + 1.4 + i * 0.12);
        const cut = keep ? 0 : prog(t, trimT + i * 0.06, trimT + 0.3 + i * 0.06, ease.inCubic);
        if (cut >= 1) continue;
        const x = SX - 45 + i * 15, y = SY - 60;
        c.globalAlpha = 1 - cut;
        if (!(keep && tree > 0)) drawShoot(c, x, y + cut * 50, 110 + hash(i, 1) * 50 + (keep ? 40 : 0), g, keep && t > keepT ? rgba('leaf', 1) : rgba('moss', 1), 20 + i, (i - 3) * 0.12 + cut * (i < 3 ? -1 : 1));
        c.globalAlpha = 1;
      }
      // KEEP ring
      const kr = prog(t, keepT + 0.2, keepT + 0.5, ease.outBack) * (1 - tree);
      if (kr > 0) {
        c.strokeStyle = rgba('leaf', 1);
        c.lineWidth = 3;
        c.beginPath();
        c.arc(SX, SY - 160, 95 * kr, 0, TAU);
        c.stroke();
        c.font = font(F.mono(600), 22);
        c.letterSpacing = '5px';
        c.fillStyle = rgba('leaf', kr);
        c.fillText('KEEP ONE', SX + 110, SY - 230);
        c.fillStyle = rgba('signal', prog(t, trimT, trimT + 0.2) * kr);
        c.fillText('TRIM THE REST', SX + 110, SY - 190);
        c.letterSpacing = '0px';
      }
      if (tree > 0) drawAcacia(c, SX, SY - 50, lerp(140, 520, tree), { growth: clamp(0.3 + tree), seed: 77, color: rgba('bone', 0.95), leaf: rgba('leaf', 1), leafAlpha: 0.55, sway: Math.sin(t) });
      // lyric with "cutting" struck out
      const cur = this.current(t, 0.8);
      if (cur) {
        const st = { size: 80, maxWidth: 1700, hot: rgba('leaf', 1), pop: 6, emphasis: { choosing: { color: rgba('leaf', 1) }, grow: { color: rgba('leaf', 1) } } };
        drawLyric(c, cur, t, 96, 220, st);
        if (cur.i === L(25).i) {
          const rows = layoutLine(cur.words, st);
          rows.forEach((row, ri) => row.items.forEach((it) => {
            if (it.w.w !== 'cutting,') return;
            const s = prog(t, it.w.end - 0.05, it.w.end + 0.15, ease.outCubic);
            c.fillStyle = rgba('signal', 1);
            c.fillRect(96 + it.x - 6, 220 + ri * 84 - 28, (it.width - 6) * s, 9);
          }));
        }
      }
      return o;
    }

    if (t < dotsT + 0.8) {
      // ---- twenty years later: the land fills with trees
      const k = 1 - prog(t, dotsT, dotsT + 0.8);
      c.globalAlpha = k;
      c.fillStyle = rgba('bone', 0.8);
      c.fillRect(0, 900, 1920, 2);
      const g0 = L(27).words[0]!.start;
      for (let i = 0; i < 46; i++) {
        const x = 40 + (i / 45) * 1840 + (hash(i, 1) - 0.5) * 30;
        const d = Math.abs(x - 960) / 960;
        const g = prog(t, g0 + d * 1.6 + hash(i, 2) * 0.3, g0 + d * 1.6 + 0.9 + hash(i, 2) * 0.3, ease.outCubic);
        drawAcacia(c, x, 900, 120 + hash(i, 3) * 160, { growth: g, seed: 300 + i, color: rgba('bone', 0.85), leaf: rgba('leaf', 1), leafAlpha: 0.5, sway: Math.sin(t + i) });
      }
      const cv = 200_000_000 * prog(t, L(27).words[3]!.start, L(27).words[6]!.start + 0.4, ease.outCubic);
      drawCounter(c, 960, 430, cv, { size: 150, align: 'center', label: 'TREES  ·  NIGER, 2000s', color: rgba('leaf', 1), labelColor: rgba('leaf', 0.7) });
      c.font = font(F.mono(500), 20);
      c.letterSpacing = '5px';
      c.fillStyle = rgba('bone', 0.6);
      c.textAlign = 'center';
      c.fillText(`${Math.round(lerp(1984, 2004, prog(t, g0, g0 + 1.2)))}`, 960, 230);
      c.textAlign = 'left';
      c.letterSpacing = '0px';
      c.globalAlpha = 1;
      const cur = this.current(t, 0.5);
      if (cur && cur.i === L(27).i) drawLyric(c, cur, t, 960, 1010, { size: 56, align: 'center', hot: rgba('leaf', 1), family: F.archivo(100, 700) });
      if (t < dotsT) return o;
    }

    // ---- food for 2.5 million more people: 2,500 dots, one per 1,000
    const a = prog(t, dotsT, dotsT + 0.5);
    const sweep = prog(t, L(28).words[2]!.start, L(28).words[8]!.start + 0.3, ease.inOutCubic);
    const cols = 100, rows = 25, x0 = 170, x1 = 1750, y0 = 480, y1 = 830;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
      const x = lerp(x0, x1, i / (cols - 1)), y = lerp(y0, y1, j / (rows - 1));
      const on = (i + hash(i, j) * 6) / (cols + 6) < sweep;
      c.fillStyle = on ? rgba('leaf', a) : rgba('bone', 0.12 * a);
      c.fillRect(x - 2.5, y - 2.5, 5, 5);
    }
    drawCounter(c, 170, 420, 2_500_000 * sweep, { size: 90, digits: 7, label: '', color: rgba('leaf', a) });
    c.font = font(F.mono(500), 20);
    c.letterSpacing = '5px';
    c.fillStyle = rgba('bone', 0.7 * a);
    c.fillText('■ = 1,000 PEOPLE  ·  MORE FOOD FROM THE SAME FIELDS', 170, 900);
    c.letterSpacing = '0px';
    const cur = this.current(t, 1.2);
    if (cur && cur.i === L(28).i) drawLyric(c, cur, t, 96, 200, { size: 80, maxWidth: 1700, hot: rgba('leaf', 1), pop: 6, emphasis: { people: { color: rgba('leaf', 1) } } }, a);
    return o;
  }
}
