# wifi-motion-detector — Build Log

> Where we are, newest at top. Update before ending any session.

_Last updated: 2026-05-24 — Stage 0 (workspace setup) in progress._

## Status
🟡 **Stage 0 — workspace setup.** Project created on E:, venv + libs installed, git init,
foundation files written. Next: first commit, Desktop entry, GitHub repo → then Stage 1.

## Confirmed
- Feasibility verified: laptop reads live RSSI (`-69 dBm` to `BHARTI_HOME`) via netsh.
- Stack: Python 3.13.4 + numpy + rich + pytest. Windows, 2.4 GHz link.
- v1 = laptop-only single link; v2 = phones via Termux; v3 = web dashboard.

## Stages
- [~] Stage 0 — workspace + git + GitHub + continuity files
- [ ] Stage 1 — sensing (`wifi_reader.py`): live RSSI readout
- [ ] Stage 2 — detection (`detector.py`): baseline + MOTION/CLEAR
- [ ] Stage 3 — dashboard (rich live UI)
- [ ] Stage 4 — polish, tests, README, push

## Open questions
- (none yet)
