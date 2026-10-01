// FIG. 5 — 1983. The year in serif; a field card for Tony Rinaudo by a road home; a push-in on a
// scruffy little bush, which trembles through the riser ("it isn't a bush") and goes black on the
// last beat before the drop.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, hash, lerp, prog, frameIdx } from '../engine/util';
import { Plate } from './_plate';
import { drawLyric, drawScruff, plateHeader } from './_trees';

const GY = 760, BX = 1180;

export default class Bush extends Plate {
  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t, end = this.ctx.end;
    const o: PostOverrides = { bloom: 0.55, bloomThreshold: 0.6, grain: 0.06, vignette: 0.45 };
    const L = (i: number) => this.line(i - 18);
    if (t >= end - 0.6) { o.fade = 1; return o; }
    // ---- 1983
    if (t < L(19).start - 0.3) {
      const a = prog(t, L(18).start - 0.05, L(18).start + 0.25, ease.outCubic);
      c.save();
      c.globalAlpha = a;
      c.translate(960, 560);
      const s = 1.08 - 0.08 * a + 0.015 * (t - L(18).start);
      c.scale(s, s);
      c.font = font(F.serif(600), 420);
      c.textAlign = 'center';
      c.fillStyle = rgba('bone', 1);
      c.fillText('1983', 0, 140);
      c.font = font(F.mono(500), 22);
      c.letterSpacing = '8px';
      c.fillStyle = rgba('ember', 0.9);
      c.fillText('MARADI REGION  ·  NIGER', 0, 250);
      c.restore();
      return o;
    }
    // ---- the road home, then the push-in on the bush
    const zin = prog(t, L(20).words[1]!.start, L(20).end + 0.3, ease.inOutCubic);
    const riser = prog(t, L(21).start - 0.1, end - 0.6);
    const z = lerp(1, 2.6, zin) * (1 + 0.15 * riser * riser);
    const jit = riser * riser * 10;
    c.save();
    c.translate(960 + (hash(frameIdx(t), 1) - 0.5) * jit, 600 + (hash(frameIdx(t), 2) - 0.5) * jit);
    c.scale(z, z);
    c.translate(-lerp(960, BX, zin), -lerp(600, GY - 40, zin));
    plateHeader(c, 'FIELD NOTES', 'MARADI, NIGER  ·  1983', 1 - zin);
    // road
    c.fillStyle = rgba('bone', 0.85);
    c.fillRect(-400, GY, 2800, 2);
    c.fillRect(-400, GY + 70, 2800, 2);
    for (let x = -400; x < 2400; x += 70) c.fillRect(x + ((t * 40) % 70) * 0, GY + 35, 34, 2);
    // sign
    c.fillRect(1700, GY - 150, 3, 150);
    c.strokeStyle = rgba('bone', 0.9);
    c.lineWidth = 2;
    c.strokeRect(1620, GY - 210, 220, 60);
    c.font = font(F.mono(600), 28);
    c.letterSpacing = '5px';
    c.fillStyle = rgba('bone', 0.95);
    c.fillText('HOME →', 1650, GY - 168);
    // field card
    const ca = prog(t, L(19).start - 0.2, L(19).start + 0.3) * (1 - zin);
    if (ca > 0) {
      c.globalAlpha = ca;
      c.strokeStyle = rgba('bone', 0.5);
      c.lineWidth = 1;
      c.strokeRect(96, 360, 560, 220);
      c.font = font(F.mono(500), 18);
      c.letterSpacing = '3px';
      const rows = [['NAME', 'TONY RINAUDO'], ['WORK', 'AGRONOMIST'], ['TREES', 'PLANTED, MOSTLY DEAD'], ['STATUS', 'READY TO GO HOME']];
      rows.forEach(([k, v], i) => {
        c.fillStyle = rgba('bone', 0.5);
        c.fillText(k!, 120, 400 + i * 46);
        c.fillStyle = i === 3 ? rgba('signal', 1) : rgba('bone', 0.95);
        c.fillText(v!, 270, 400 + i * 46);
      });
      c.globalAlpha = 1;
    }
    c.letterSpacing = '0px';
    // the bush by the road
    c.strokeStyle = rgba('bone', 0.12);
    drawScruff(c, BX, GY, 70, 7, rgba('sand', 0.9), riser > 0 ? t : 0, 90);
    // a glow seeping from under it before the drop
    const glow = prog(t, L(21).words[2]!.start, end - 0.6);
    if (glow > 0) {
      const g = c.createRadialGradient(BX, GY + 10, 0, BX, GY + 10, 160);
      g.addColorStop(0, rgba('leaf', 0.5 * glow));
      g.addColorStop(1, rgba('leaf', 0));
      c.fillStyle = g;
      c.fillRect(BX - 160, GY, 320, 160);
    }
    // callout
    const cl = prog(t, L(20).words[5]!.start, L(20).words[5]!.start + 0.3);
    if (cl > 0) {
      c.globalAlpha = cl;
      c.strokeStyle = rgba('bone', 0.8);
      c.lineWidth = 1 / z;
      c.beginPath();
      c.moveTo(BX + 30, GY - 60);
      c.lineTo(BX + 80, GY - 110);
      c.lineTo(BX + 150, GY - 110);
      c.stroke();
      c.font = font(F.mono(500), 11);
      c.letterSpacing = '2px';
      c.fillStyle = rgba('bone', 0.9);
      c.fillText('A SCRUFFY LITTLE BUSH', BX + 156, GY - 106);
      const nt = L(21).words[2]!.start;
      const st = prog(t, nt, nt + 0.2, ease.outCubic);
      if (st > 0) {
        c.fillStyle = rgba('signal', 1);
        c.fillRect(BX + 154, GY - 111, 160 * st, 2.5);
        c.font = font(F.mono(600), 13);
        c.fillText('?', BX + 320, GY - 106);
      }
      c.globalAlpha = 1;
      c.letterSpacing = '0px';
    }
    c.restore();
    o.shake = [0, 0];
    o.zoom = 1 + 0.01 * riser;
    // lyrics stay put on top of the camera
    const cur = this.current(t, 0.6);
    if (cur) drawLyric(c, cur, t, 96, 230, { size: 80, maxWidth: 1500, hot: rgba('ember', 1), pop: 6, emphasis: { 'isnt': { color: rgba('signal', 1) } } });
    o.grain = 0.06 + 0.04 * riser;
    void clamp;
    return o;
  }
}
