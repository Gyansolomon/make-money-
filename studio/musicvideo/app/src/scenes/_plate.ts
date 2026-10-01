// Base for the Canvas2D plates of this video: clear to a background, draw one full-frame 2D layer
// (with an optional camera), composite it. Subclasses implement draw().
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D, clearRT } from '../engine/gl';
import { LIN, type PaletteKey } from '../engine/palette';
import type { Line } from '../engine/lyrics';

export abstract class Plate extends Scene {
  L = new Layer2D();
  bg: PaletteKey = 'ink';
  lines: Line[] = [];

  override init() {
    const { lyrics, start, end } = this.ctx;
    this.lines = lyrics.lines.filter((l) => l.start >= start - 0.05 && l.start < end);
    this.setup();
  }
  setup() {}

  /** The line on screen at t: from just before it starts until the next one is about to start (or `hold` after it ends). */
  current(t: number, hold = 0.9, pre = 0.4): Line | null {
    let cur: Line | null = null;
    for (let i = 0; i < this.lines.length; i++) {
      const l = this.lines[i]!;
      const next = this.lines[i + 1];
      const until = Math.min(l.end + hold, next ? next.start - pre : Infinity);
      if (t >= l.start - pre && t < until) cur = l;
    }
    return cur;
  }
  line(n: number) { return this.lines[n]!; }
  word(line: number, w: number) { return this.lines[line]!.words[w]!; }

  abstract draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides | void;

  render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides | void {
    const L = this.L;
    L.clear();
    const c = L.ctx;
    c.textBaseline = 'alphabetic';
    c.letterSpacing = '0px';
    const o = this.draw(c, f);
    clearRT(this.ctx.renderer, out, LIN[this.bg]);
    this.ctx.comp.draw(this.ctx.renderer, L.upload(), out, { mode: 'normal' });
    return o;
  }
}

// ------------------------------------------------------------------ the hook: one word per frame
import { F, fitSize, font, measure } from '../engine/type';
import { rgba } from '../engine/palette';
import { clamp, ease, pulse } from '../engine/util';

/**
 * "AND / NOBODY / PLANTED / THEM." one word at a time, each slammed full-frame on its onset.
 * `hot` colours the word that matters. Returns the onset pulse (for flash/zoom).
 */
export function slamWords(c: CanvasRenderingContext2D, line: Line, t: number, hot: Record<string, string>, base = rgba('bone', 1)) {
  let wi = -1;
  line.words.forEach((w, i) => { if (t >= w.start - 0.01) wi = i; });
  if (wi < 0) return 0;
  const w = line.words[wi]!;
  const txt = w.w.toUpperCase().replace(/[.,!]/g, '');
  const fam = F.archivo(txt.length > 5 ? 100 : 125, 900);
  const size = Math.min(520, fitSize(txt, fam, 1720, 520));
  const k = 1 + 0.16 * (1 - ease.outExpo(clamp((t - w.start) / 0.18))) + 0.02 * Math.max(0, t - w.start);
  c.save();
  c.translate(960, 540);
  c.scale(k, k);
  c.font = font(fam, size);
  c.textAlign = 'center';
  c.fillStyle = hot[txt] ?? base;
  c.fillText(txt, 0, size * 0.34);
  c.restore();
  // the previous word as a ghost, smaller, top-left
  if (wi > 0) {
    const p = line.words.slice(0, wi).map((x) => x.w.toUpperCase()).join(' ');
    c.font = font(F.mono(500), 22);
    c.letterSpacing = '6px';
    c.fillStyle = rgba('bone', 0.4);
    c.fillText(p, 96, 140);
    c.letterSpacing = '0px';
  }
  void measure;
  return pulse(t, w.start, 0.08);
}
