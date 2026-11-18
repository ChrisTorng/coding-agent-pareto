
### Interactive UI and scheduled source monitoring (2026-11-18)

The live explorer keeps its plot separate from the reference and export section so fullscreen is usable. It offers shareable query parameters (`agent`, `benchmark`, `snapshot`, `scale`, `labels`, X/Y limits), per-agent localStorage checkbox exclusions and a compact logarithmic scale. Point labels are On/Off. The approved four static Matplotlib images are unchanged.

The ChatGPT monitor (Tue–Sat 07:30, Asia/Taipei) checks official source changes and updates versioned repository snapshots **only when changes are verified**; GHA then builds and deploys. Existing GHA alone does not discover new model prices or benchmark scores autonomously. See [website documentation](web/README.md).