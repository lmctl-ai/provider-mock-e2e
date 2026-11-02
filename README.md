# Provider mock E2E

Real coding tools installed by lminstall, pointed at a checksum-verified lmmock release. The gate needs no provider credentials and makes no model request to a vendor. Every prompt runs in an empty working directory and temporary HOME. Tools themselves are unmodified.

The matrix starts with locally qualified Claude Code, Codex, Gemini, Copilot, OpenCode, Qwen Pi, Kimi, Miniplayer, lmplayer, DSH and Agy on Linux, macOS and Windows. Further providers are admitted after a real local prompt, request audit and semantic negative control pass. CI records the installed versions; upstream latest packages can change.

The reusable procedure is lminstall → release checksum verification and private fixture compilation → isolated provider configuration → prompt → exact reply and request audit. `scripts/probe.py` contains each provider configuration. `scripts/run.py` obtains its owned binary from lminstall, never a global PATH fallback.

The released llm-api handler forces arbitrary first-tool calls. `scripts/prepare.py` makes a checked, small lmcode policy change for this no-tool smoke: advertised built-ins do not force tool use. This does not establish arbitrary tool execution, quota, persistence or live vendor fidelity. The stock handler is retained separately for wire-shape probes.

Every result requires exit0 and exact PROVIDER_MOCK_OK_129. The same checker is invoked with a deliberately wrong expectation and must raise its wrong-reply assertion. Raw stdout/stderr and synthetic request/audit records are retained without output caps. No sleeps, process deadlines or custom generation limits are used; CI has a job safety bound. No provider key or credential file is accepted.

Full endpoint and limitation inventory is maintained in the owning task report in skills-scripts. An unsupported authenticated vendor route requires a sanitized lminspect capture, not a guessed fixture.
