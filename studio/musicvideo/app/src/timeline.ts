// The edit for "The Trees Nobody Planted": one plate per section of the song, each cut on the
// downbeat before its first line (bars are 2.4 s at 100 BPM).
import type { TimelineEntry } from './engine/engine';
import type { SceneClass } from './engine/scene';
import type { Lyrics } from './engine/lyrics';
import type { AudioData } from './engine/audio';

const modules = import.meta.glob<{ default: SceneClass }>('./scenes/*.ts');
const scene = (name: string) => () => {
  const m = modules[`./scenes/${name}.ts`];
  return m ? m() : Promise.reject(new Error(`scene module not found: scenes/${name}.ts`));
};

export function makeTimeline(ly: Lyrics, au: AudioData): TimelineEntry[] {
  /** The downbeat at or before the first word of the line containing q. */
  const cut = (q: string) => {
    const s = ly.get(q).words[0]!.start;
    return au.downbeats.filter((d) => d <= s + 0.02).pop() ?? 0;
  };
  const b = {
    sahel: cut('Niger. The'),
    drought: cut('Those roots'),
    seed: cut('So the world'),
    bush: cut('1983'),
    roots: cut('It’s a tree'),
    regrow: cut('stop cutting'),
    finale: ly.find('nobody planted').pop()!.words[0]!.start - 0.1,
    end: au.duration,
  };
  const finale = au.downbeats.filter((d) => d <= b.finale + 0.12).pop()!;
  const E = (id: string, start: number, end: number, fig: string, text: string): TimelineEntry =>
    ({ id, load: scene(id), start, end, caption: { fig, text, delay: 0.6 } });
  return [
    E('count', 0, b.sahel, 'FIG. 1', 'a number from the Sahel'),
    E('sahel', b.sahel, b.drought, 'FIG. 2', 'the edge of the Sahara, 1970s'),
    E('drought', b.drought, b.seed, 'FIG. 3', 'what the trees were doing'),
    E('seedlings', b.seed, b.bush, 'FIG. 4', 'the usual answer'),
    E('bush', b.bush, b.roots, 'FIG. 5', 'Maradi, Niger, 1983'),
    E('roots', b.roots, b.regrow, 'FIG. 6', 'the underground forest'),
    E('regrow', b.regrow, finale, 'FIG. 7', 'farmer-managed natural regeneration'),
    E('finale', finale, b.end, 'FIG. 8', 'nobody planted them'),
  ];
}
