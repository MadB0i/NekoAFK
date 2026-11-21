# Product reset audit (2026-10-09)

- Initial Git state: only README tracked; assets/, prototype/, .artifacts/
  untracked. No existing work was reverted. No commits or pushes authorized.
- Existing functionality: a Node static server; browser-only companion/dock
  windows; drag, attachment, scaling, localStorage settings; transparent raster
  and layered character experiments; Python visual tests.
- Absent: native shell, tray, installer, actual agent transport, local independent
  verification. All telemetry in prototype/simulation/states.js was simulated.
- Reused: separate companion/dock surfaces, native-host boundary, attachment and
  recovery policies, state vocabulary, and explicit separation of fixtures.
- Original character/Blender work and browser experiments moved intact under
  archive/. A generated SHA-256 inventory records original files; dependencies
  and Python caches are excluded from the inventory but preserved on disk.
- No suitable simple cat asset existed. One original code-native 2D cat replaces
  the elaborate character. No model/animation refinement is part of this reset.
