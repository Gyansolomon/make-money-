// FIG. 2 — the edge of the Sahara in the 1970s, as a field survey: millet rows and old acacias on
// a long horizon, dunes behind. People, fields and firewood stamp in; the trees fall one per 8th
// on "come down"; PROBLEM SOLVED stamps in green and is struck out in orange on "Not exactly".
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, hash, lerp, prog, pulse, TAU } from '../engine/util';
import { Plate } from './_plate';
import { drawAcacia, drawLyric, drawStump, plateHeader } from './_trees';

const GY = 820;
const TREES = [190, 450, 700, 980, 1240, 1500, 1760].map((x, i) => ({ x, h: 210 + hash(i, 3) * 70, seed: 11 + i }));

export default class Sahel extends Plate {
  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t;
    const o: PostOverrides = { bloom: 0.55, bloomThreshold: 0.6, grain: 0.06, vignette: 0.4 };
    const L = (i: number) => this.line(i - 3);
    plateHeader(c, 'FIELD SURVEY  ·  SAHEL', 'NIGER  ·  13°N  ·  1970s', prog(t, 12.1, 12.6));

    // ---- dunes behind the horizon (on "Sahara")
    const dn = prog(t, L(4).words[4]!.start - 0.2, L(4).words[4]!.start + 1.0, ease.outCubic);
    if (dn > 0) {
      c.strokeStyle = rgba('sand', 0.55 * dn);
      c.lineWidth = 1.4;
      for (let k = 0; k < 5; k++) {
        c.beginPath();
        for (let x = 0; x <= 1920; x += 12) {
          const y = GY - 40 - k * 26 + Math.sin(x * 0.006 + k * 1.7) * (10 + k * 4) + Math.sin(x * 0.017 + k) * 4;
          const reveal = x < 1920 - dn * 1920 ? 0 : 1;
          if (!reveal) continue;
          if (x === 0 || x - 12 < 1920 - dn * 1920) c.moveTo(x, y); else c.lineTo(x, y);
        }
        c.stroke();
      }
      c.font = font(F.mono(500), 16);
      c.letterSpacing = '4px';
      c.fillStyle = rgba('sand', 0.9 * dn);
      c.fillText('SAHARA  ↑ NORTH', 1520, GY - 175);
      c.letterSpacing = '0px';
    }
    // ground
    c.fillStyle = rgba('bone', 0.8);
    c.fillRect(0, GY, 1920 * prog(t, 12.0, 12.8, ease.outCubic), 2);

    // ---- millet rows (on "Millet")
    const m0 = L(5).words[0]!.start - 0.1;
    for (let x = 60; x < 1880; x += 22) {
      const k = prog(t, m0 + (x / 1920) * 0.9, m0 + (x / 1920) * 0.9 + 0.3, ease.outCubic);
      if (k <= 0) continue;
      const h = (34 + hash(x, 1) * 20) * k;
      const wind = Math.sin(t * 2 + x * 0.05) * 3;
      c.strokeStyle = rgba('sand', 0.8);
      c.lineWidth = 1.5;
      c.beginPath();
      c.moveTo(x, GY);
      c.quadraticCurveTo(x, GY - h * 0.6, x + wind, GY - h);
      c.stroke();
      c.fillStyle = rgba('sand', 0.9);
      c.beginPath();
      c.ellipse(x + wind, GY - h - 6, 2.6, 7 * k, 0, 0, TAU);
      c.fill();
    }

    // ---- the old trees (on "old trees"), falling on "come down"
    const g0 = L(5).words[4]!.start - 0.1;
    const fall0 = L(7).words[2]!.start;
    TREES.forEach((tr, i) => {
      const g = prog(t, g0 + i * 0.08, g0 + i * 0.08 + 0.9, ease.outCubic);
      const ft = fall0 + [3, 0, 5, 1, 6, 2, 4][i]! * 0.2;
      const fall = prog(t, ft, ft + 0.35, ease.inCubic);
      const gone = prog(t, ft + 0.6, ft + 1.6);
      if (fall > 0) drawStump(c, tr.x, GY + 1, 26, { color: rgba('bone', 0.9) });
      if (gone < 1) {
        c.globalAlpha = 1 - gone;
        drawAcacia(c, tr.x, GY, tr.h, { growth: g, seed: tr.seed, sway: Math.sin(t * 1.3 + i), fall, color: rgba('bone', 0.9), leaf: rgba('moss', 1), leafAlpha: 0.5 });
        c.globalAlpha = 1;
      }
      if (fall > 0 && fall < 1) o.shake = [(hash(i, Math.round(t * 60)) - 0.5) * 8 * (1 - fall), 0];
    });

    // ---- people, fields, firewood
    const tags: [number, string][] = [[1, 'PEOPLE'], [5, 'FIELDS'], [7, 'FIREWOOD']];
    tags.forEach(([wi, txt], k) => {
      const w = L(6).words[wi]!;
      const a = prog(t, w.start, w.start + 0.08) * (1 - prog(t, L(7).start + 0.4, L(7).start + 0.8));
      if (a <= 0) return;
      const s = 1 + 0.3 * (1 - ease.outExpo(clamp((t - w.start) / 0.2)));
      c.save();
      c.translate(1500, 330 + k * 70);
      c.scale(s, s);
      c.globalAlpha = a;
      c.strokeStyle = rgba('signal', 1);
      c.fillStyle = rgba('signal', 1);
      c.lineWidth = 2;
      c.strokeRect(-10, -36, 330, 52);
      c.font = font(F.mono(600), 30);
      c.letterSpacing = '4px';
      c.fillText(`+ ${txt}`, 10, 2);
      c.restore();
      c.letterSpacing = '0px';
    });
    // little people along the ground, more every word
    const pp = prog(t, L(6).words[1]!.start, L(6).end + 0.5) * (1 - prog(t, L(9).end, L(9).end + 0.6));
    const np = Math.floor(pp * 26);
    for (let i = 0; i < np; i++) {
      const x = 80 + hash(i, 7) * 1760, h = 26 + hash(i, 8) * 8;
      c.strokeStyle = rgba('bone', 0.75);
      c.lineWidth = 2;
      c.beginPath();
      c.moveTo(x, GY - 2);
      c.lineTo(x, GY - h);
      c.stroke();
      c.beginPath();
      c.arc(x, GY - h - 5, 4, 0, TAU);
      c.stroke();
    }

    // ---- PROBLEM SOLVED, then struck out
    const ps = L(8).words[0]!;
    const sa = prog(t, ps.start - 0.02, ps.start + 0.03);
    if (sa > 0) {
      const s = 1 + 0.4 * (1 - ease.outExpo(clamp((t - ps.start) / 0.16)));
      const nt = L(9).words[1]!.start;
      const strike = prog(t, nt, nt + 0.14, ease.outCubic);
      const col = strike > 0 ? rgba('graphite', 1) : rgba('leaf', 1);
      c.save();
      c.translate(960, 560);
      c.rotate(-0.07);
      c.scale(s, s);
      c.strokeStyle = col;
      c.fillStyle = col;
      c.lineWidth = 6;
      c.strokeRect(-470, -95, 940, 170);
      c.font = font(F.archivo(125, 900), 104);
      c.textAlign = 'center';
      c.fillText('PROBLEM SOLVED', 0, 25);
      if (strike > 0) {
        c.strokeStyle = rgba('signal', 1);
        c.lineWidth = 16;
        c.beginPath();
        c.moveTo(-500, 40);
        c.lineTo(lerp(-500, 500, strike), lerp(40, -50, strike));
        c.stroke();
      }
      c.restore();
      o.flash = pulse(t, ps.start, 0.06) * 0.06;
      o.zoom = 1 + 0.02 * pulse(t, nt, 0.1);
    }

    // ---- dust starts to move at the end of the verse
    const dust = prog(t, 29.0, 31.2);
    if (dust > 0) {
      for (let i = 0; i < 260; i++) {
        const sp = 300 + hash(i, 1) * 500;
        const x = ((hash(i, 2) * 2200 + (t - 29) * sp) % 2200) - 140;
        const y = GY - 6 - hash(i, 3) * 240 * hash(i, 4);
        c.fillStyle = rgba('sand', 0.6 * dust * hash(i, 5));
        c.fillRect(x, y, 6 + sp * 0.02, 1.6);
      }
    }

    // ---- lyrics
    const cur = this.current(t);
    if (cur) drawLyric(c, cur, t, 96, 230, { size: 84, maxWidth: 1300, hot: rgba('ember', 1), pop: 6, emphasis: { niger: { color: rgba('ember', 1) } } });
    return o;
  }
}
