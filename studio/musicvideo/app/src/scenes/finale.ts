// FIG. 8 — the hook again, now in green, then the end card with the facts and the sources.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { ease, hash, prog } from '../engine/util';
import { Plate, slamWords } from './_plate';
import { drawAcacia } from './_trees';

export default class Finale extends Plate {
  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t, end = this.ctx.end;
    const l = this.line(0);
    const o: PostOverrides = { bloom: 0.7, bloomThreshold: 0.5, grain: 0.055, vignette: 0.45, hud: 0 };
    if (t < l.end + 0.7) {
      const p = slamWords(c, l, t, { NOBODY: rgba('leaf', 1), PLANTED: rgba('leaf', 1) });
      o.flash = p * 0.04;
      o.zoom = 1 + 0.02 * p;
      o.hud = 1;
      return o;
    }
    const t0 = l.end + 0.7;
    const a = prog(t, t0, t0 + 0.8, ease.outCubic);
    // a line of trees along the bottom
    c.fillStyle = rgba('bone', 0.5 * a);
    c.fillRect(0, 960, 1920, 1.5);
    for (let i = 0; i < 30; i++) {
      const x = 30 + i * 64 + (hash(i, 1) - 0.5) * 20;
      drawAcacia(c, x, 960, 60 + hash(i, 2) * 70, { growth: prog(t, t0 + i * 0.03, t0 + 0.8 + i * 0.03), seed: 500 + i, color: rgba('bone', 0.6), leaf: rgba('leaf', 1), leafAlpha: 0.5, sway: Math.sin(t + i) });
    }
    c.textAlign = 'center';
    c.globalAlpha = a;
    c.font = font(F.serif(600), 132);
    c.fillStyle = rgba('bone', 1);
    c.fillText('The Trees Nobody Planted', 960, 420);
    c.font = font(F.mono(500), 22);
    c.letterSpacing = '6px';
    c.fillStyle = rgba('leaf', 1);
    c.fillText('FARMER-MANAGED NATURAL REGENERATION  ·  NIGER  ·  1983 →', 960, 510);
    const b = prog(t, t0 + 1.0, t0 + 1.8);
    c.globalAlpha = b;
    c.font = font(F.mono(400), 20);
    c.letterSpacing = '3px';
    c.fillStyle = rgba('bone', 0.85);
    c.fillText('~200 MILLION TREES  ·  ~5 MILLION HECTARES  ·  FOOD FOR ~2.5 MILLION MORE PEOPLE', 960, 620);
    c.fillStyle = rgba('bone', 0.5);
    c.font = font(F.mono(400), 16);
    c.fillText('SOURCES: RIGHT LIVELIHOOD (TONY RINAUDO)  ·  YALE ENVIRONMENT 360  ·  UNCCD', 960, 680);
    c.font = font(F.serif(400, true), 30);
    c.letterSpacing = '0px';
    c.fillStyle = rgba('bone', 0.7);
    c.fillText('the forest was already there', 960, 760);
    c.textAlign = 'left';
    c.globalAlpha = 1;
    o.fade = prog(t, end - 1.4, end - 0.1, ease.inCubic);
    return o;
  }
}
