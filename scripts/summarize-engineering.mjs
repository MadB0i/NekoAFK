import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const root = path.resolve(import.meta.dirname, '..');
const dir = path.join(root, '.artifacts', 'engineering');
const read = name => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
const baseline = read('before-repeat-performance.json');
const candidate = read('after-performance.json');
const comparison = Object.keys(candidate.phases).map(name => {
  const before = baseline.phases[name], after = candidate.phases[name];
  return {
    phase: name,
    before_cpu_one_core: before.cpu_percent_one_core,
    after_cpu_one_core: after.cpu_percent_one_core,
    before_private_mib: before.private_mib,
    after_private_mib: after.private_mib,
    before_raf_per_second: +(before.raf_callbacks / before.seconds).toFixed(1),
    after_raf_per_second: +(after.raf_callbacks / after.seconds).toFixed(1),
    before_mutation_cadence_ms: before.mutation_cadence_ms,
    after_mutation_cadence_ms: after.mutation_cadence_ms,
  };
});
const result = {
  scope: 'Actual release executables and their WebView2 process trees; one-core CPU, not total-machine percentage.',
  method: 'Serial native runs, same settings and display, no concurrent build. Local CDP sampling remains attached. Idle activity selection is random and recorded; typing uses the same authored keyboard clip.',
  baseline_exe_sha256: baseline.exe_sha256,
  candidate_exe_sha256: candidate.exe_sha256,
  final_exe_sha256: createHash('sha256').update(fs.readFileSync(path.join(root, 'src-tauri', 'target', 'release', 'nekoafk.exe'))).digest('hex'),
  final_build_note: 'Performance/600-second soak precede the final selected-session connection metadata/UI correction. The renderer and authored performances did not change afterward.',
  validation: {
    rust_passed: Number(fs.readFileSync(path.join(dir, 'rust-tests.log'), 'utf8').match(/test result: ok\. (\d+) passed/)[1]),
    javascript_passed: Number(fs.readFileSync(path.join(dir, 'javascript-tests.log'), 'utf8').match(/tests (\d+)/)[1]),
    native_desktop: read('desktop-native.json').checks,
    real_opencode: read('opencode-recovery.json'),
    character_preservation: read('character-preservation.json'),
  },
  comparison,
  exploratory_runs: ['before-performance.json', 'after-first-performance.json'],
  limitations: [
    'Earlier baseline idle was 23.31% and typing 15.39%; the repeat was 33.20% and 47.82%. Candidate typing was 36.94% and 35.62%. Run-to-run variation prevents claiming a universal CPU improvement.',
    'Quiet-rest sampling includes occasional blink and settling motion; it is not an entirely frozen-pose sample.',
    'DOM mutation cadence is not presented-frame timing. Graphics and renderer processes dominate remaining typing cost.',
    'Memory values are process-tree private memory at the end of each phase, not a leak test.',
  ],
};
const soakPath = path.join(dir, 'character-regression', 'native-acceptance.json');
if (fs.existsSync(soakPath)) {
  const soak = JSON.parse(fs.readFileSync(soakPath, 'utf8'));
  result.native_stability = { checks: soak.checks, resources: soak.resources, frame_pacing: soak.frame_pacing, video: soak.video };
}
const livingPath = path.join(dir, 'living-regression', 'report.json');
if (fs.existsSync(livingPath)) result.validation.living_native = JSON.parse(fs.readFileSync(livingPath, 'utf8')).checks;
const desktopPath = path.join(root, '.artifacts', 'native-validation', 'report.json');
if (fs.existsSync(desktopPath)) result.validation.complete_desktop = Object.fromEntries(Object.entries(JSON.parse(fs.readFileSync(desktopPath, 'utf8'))).filter(([key, value]) => value === 'passed' || key === 'console_errors'));
fs.writeFileSync(path.join(dir, 'performance-comparison.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
