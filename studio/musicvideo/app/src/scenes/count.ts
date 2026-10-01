// FIG. 1 — the number first. A horizon draws itself, the TREES counter rolls to 200,000,000 on
// "Two hundred million trees", the sun comes up on "the driest places on Earth", the hook slams one
// word per frame, and the counter rewinds to zero to take us back to the 1970s.
import type { Frame, PostOverrides } from '../engine/scene';
import { rgba } from '../engine/palette';
import { F, font } from '../engine/type';
import { clamp, ease, lerp, prog, pulse, TAU } from '../engine/util';
import { Plate, slamWords } from './_plate';
import { drawCounter, drawLyric } from './_trees';

const HY = 780; // horizon

export default class Count extends Plate {
  draw(c: CanvasRenderingContext2D, f: Frame): PostOverrides {
    const t = f.t;
    const o: PostOverrides = { bloom: 0.7, bloomThreshold: 0.6, grain: 0.06, vignette: 0.45, hud: 1 };
    const l0 = this.line(0), l1 = this.line(1), l2 = this.line(2);

    // ---- the hook: word slams (pure type, nothing else)
    if (t >= l2.start - 0.01 && t < l2.end + 0.45) {
      const p = slamWords(c, l2, t, { PLANTED: rgba('signal', 1) });
      o.flash = p * 0.05;
      o.zoom = 1 + 0.025 * p;
      return o;
    }

    // ---- horizon, drawn from the centre out
    const hw = prog(t, 0.15, 2.0, ease.outCubic) * 960;
    // ---- the sun, rising for line 1 and sinking again during the rewind
    const rise = prog(t, l1.start - 0.4, l1.end + 0.4, ease.inOutCubic) * (1 - prog(t, 9.4, 11.6, ease.inOutCubic));
    if (rise > 0) {
      const sy = lerp(HY + 170, HY - 70, rise), r = 150;
      c.save();
      c.beginPath();
      c.rect(0, 0, 1920, HY);
      c.clip();
      const g = c.createRadialGradient(960, sy, 0, 960, sy, r * 3.2);
      g.addColorStop(0, rgba('signal', 0.32 * rise));
      g.addColorStop(1, rgba('signal', 0));
      c.fillStyle = g;
      c.fillRect(0, 0, 1920, HY);
      c.fillStyle = rgba('ember', 1);
      c.beginPath();
      c.arc(960, sy, r, 0, TAU);
      c.fill();
      // heat lines across the sun
      c.fillStyle = rgba('ink', 0.85);
      for (let i = 0; i < 6; i++) {
        const y = sy + r * 0.15 + i * 22 + ((t * 18) % 22);
        c.fillRect(960 - r, y, r * 2, 3 + i * 1.3);
      }
      c.restore();
      // shimmer above the ground
      c.strokeStyle = rgba('signal', 0.35 * rise);
      c.lineWidth = 1.2;
      for (let k = 0; k < 4; k++) {
        c.beginPath();
        for (let x = 960 - hw; x <= 960 + hw; x += 16) {
          const y = HY - 14 - k * 12 + Math.sin(x * 0.02 + t * 5 + k) * 3;
          if (x === 960 - hw) c.moveTo(x, y); else c.lineTo(x, y);
        }
        c.stroke();
      }
    }
    c.fillStyle = rgba('bone', 0.85);
    c.fillRect(960 - hw, HY, hw * 2, 2);
    // ground hatching
    c.strokeStyle = rgba('bone', 0.12);
    c.lineWidth = 1;
    for (let i = 0; i < 40; i++) {
      const y = HY + 14 + i * i * 0.35;
      if (y > 1080) break;
      const w = hw * (0.98 - i * 0.012);
      c.beginPath();
      c.moveTo(960 - w, y);
      c.lineTo(960 + w, y);
      c.stroke();
    }

    // ---- the counter
    const up = prog(t, l0.words[0]!.start, l0.words[3]!.start + 0.35, ease.outCubic);
    const down = prog(t, 9.4, 11.5, ease.inOutCubic);
    const v = 200_000_000 * up * (1 - down);
    const ca = prog(t, 0.6, 1.4);
    if (ca > 0) {
      c.globalAlpha = ca;
      const land = pulse(t, l0.words[3]!.start + 0.35, 0.12);
      drawCounter(c, 960, 470, v, { size: 170, align: 'center', label: down > 0 ? 'TREES  ·  REWINDING' : 'TREES  ·  SAHEL, WEST AFRICA', color: rgba(land > 0.05 ? 'ember' : 'bone', 1) });
      c.globalAlpha = 1;
      o.flash = land * 0.12;
    }

    // ---- lines 0 and 1 under the horizon
    const cur = t < l1.start - 0.4 ? l0 : t < 9 ? l1 : null;
    if (cur) drawLyric(c, cur, t, 960, 930, { size: 64, align: 'center', family: F.archivo(100, 700), hot: rgba('ember', 1), pop: 6 });
    // rewind: the decade appears
    const yr = prog(t, 10.2, 11.2, ease.outCubic);
    if (yr > 0) {
      c.font = font(F.serif(400, true), 64);
      c.textAlign = 'center';
      c.fillStyle = rgba('bone', yr * 0.9);
      c.fillText('back to the 1970s', 960, 930);
      c.textAlign = 'left';
    }
    o.fade = clamp(1 - t / 0.25);
    return o;
  }
}
