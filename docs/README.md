# Documents

What each file is and when you need it.

## Read now, in this order

| File | What it's for |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | The plan. 11 milestones, what to build, what to measure, what to buy and when. |
| [`setup-windows.md`](setup-windows.md) | Workstation setup — Quartus, Python, Icarus, cocotb, STM32 toolchain, git. Do this before M0. |
| [`pi-setup.md`](pi-setup.md) | Instrument computer setup — OS, udev rules, autostart, deploy. Needed from M2. |
| [`STATUS.md`](STATUS.md) | Where you are right now. **Keep this updated.** |

## Read when you get there

| File | When |
|---|---|
| [`protocol.md`](protocol.md) | M3 — design the register map and command protocol before writing RTL |
| [`../constraints/README.md`](../constraints/README.md) | M0 — why `.qsf` and `.sdc` are tracked in git |

## Configuration, not reading material

| File | Where it goes |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Repo root. Claude Code reads it automatically. |
| [`claude-project-instructions.md`](claude-project-instructions.md) | Paste into the Claude Project **instructions** box. Versioned here so it doesn't drift. |
| [`../.gitignore`](../.gitignore) | Quartus generates thousands of files per compile |
| [`../.gitattributes`](../.gitattributes) | Line endings — matters once the Pi is in the loop |
| [`../requirements.txt`](../requirements.txt) | Pinned to cocotb 2.x |

## Scripts

| File | Use |
|---|---|
| `../scripts/report.py` | Parse Quartus fit/timing reports into STATUS.md numbers |
| `../scripts/deploy.ps1` | Commit, push, pull on the Pi, optionally run — one command |

## Documents you'll write yourself

Not templated, because writing them is part of the work.

| File | Milestone |
|---|---|
| `timing-budget.md` | M2 — clock domains, CDC points, constraint rationale |
| `cal-procedure.md` | M8 — step-by-step calibration, repeatable by someone else |
| `afe-design.md` | M7 — attenuator math, filter response, component choices and why |
| `specs.md` | M8+ — the measured spec sheet for the finished instrument |

## Claude Project setup

1. Create a project named `scope`
2. Paste `claude-project-instructions.md` into the **instructions** box
3. Add `ROADMAP.md` and `STATUS.md` to **project knowledge**
4. One chat per milestone — `M0 - siggen`, `M1 - capture sim`, and so on
5. Re-upload `STATUS.md` when a milestone closes; project knowledge is a
   snapshot and does not auto-sync

Split of work: concepts, architecture, and design review in the project chat.
Build scripts, test scaffolding, report parsing, and git hygiene in Claude Code.
Keep the learning surface in chat and the plumbing in Claude Code.
