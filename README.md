# NekoAFK 🐾🤖

A lightweight, privacy-focused Windows desktop companion and real-time activity HUD for local AI coding agents. Powered by Tauri 2, Rust, and TypeScript.

---

## 🌟 Overview

NekoAFK brings observable AI agent activity directly to your desktop. As your coding agent works, an articulated vector companion reacts in real-time to what is happening:

- 🐱 **Neko** (the original midnight cat) or 🤖 **Nova** (the floating robot companion)
- 📊 **Live Progress HUD:** Clean, non-intrusive progress counter anchored next to the companion
- 🎛️ **Telemetry Dock:** Detachable diagnostic view tracking open operations, active tools, and exit codes
- 🛡️ **Zero-Network IPC:** Pure local atomic spool queue — no open listening ports, no telemetry uploads, and zero model keys required

---

## 🔌 Supported Agents

NekoAFK natively supports local event connections for modern AI development environments:

| Agent / Tool | Integration Type | Status |
|---|---|:---:|
| **OpenCode** | Local plugin (`.opencode/plugins/nekoafk.js`) | ✅ Supported |
| **Google Antigravity** | Workspace bridge (`integrations/antigravity/`) | ✅ Supported |
| **Claude Code** | CLI / Tool bridge (`integrations/claudecode/`) | ✅ Supported |
| **OpenAI Codex / Copilot** | CLI bridge (`integrations/codex/`) | ✅ Supported |
| **Zai** | Agent bridge (`integrations/zai/`) | ✅ Supported |

---

## 🚀 Getting Started

### Prerequisites

- Windows 10/11 (64-bit)
- [Node.js](https://nodejs.org/) (v18+)
- [Rust toolchain](https://rustup.rs/) (MSVC)
- Microsoft Edge WebView2 (pre-installed on Windows 10/11)

### Development

```powershell
# Install frontend dependencies
npm ci

# Launch desktop app in development mode
npm run desktop
```

### Production Build

```powershell
# Build frontend assets and native binary
npm run build
npx tauri build --no-bundle
```

The compiled release executable is generated at:
`src-tauri/target/release/nekoafk.exe`

---

## 🔒 Privacy & Verification Philosophy

1. **No Data Leaks:** Prompts, source code contents, full commands, and model outputs are **never** transmitted to the companion. Only high-level event types (`editing`, `testing`, `planning`, `permission`) are shared via local filesystem IPC.
2. **Silence Never Means Success:** Completion is an unverified candidate until confirmed.
3. **Double-Fingerprint Local Check:** When automated verification is enabled, NekoAFK runs your configured test command (e.g. `npm test`) inside an isolated Windows Job Object. A passing check requires an exit code of 0 and an unchanged source fingerprint before the companion celebrates.

---

## 🧪 Testing

```powershell
# Run JavaScript test suite (21 tests)
npm test

# Run Rust native test suite (42 tests)
cargo test --manifest-path src-tauri/Cargo.toml

# Run End-to-End native Playwright smoke tests
python tests/native_smoke.py
```

---

## 📄 License

This project is open-source software licensed under the MIT License.
