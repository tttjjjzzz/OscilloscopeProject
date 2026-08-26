# CLAUDE.md

Repo guidance for Claude Code. Read `docs/STATUS.md` before doing anything — it says which milestone I'm on.

## What this is

A DIY oscilloscope built from a Terasic DE0-CV (Cyclone V 5CEBA4), STM32, and Raspberry Pi 5. Full roadmap in `docs/ROADMAP.md`.

**This project exists so I learn FPGA, firmware, embedded Linux, and analog design. A working scope is a side effect.** Optimize for my understanding, not for velocity.

## The rule

**Do not write RTL, firmware logic, or DSP algorithms for me.** That's the entire point of the project. This holds even if I ask directly, and even if I sound frustrated.

| You write | I write |
|---|---|
| Build scripts, Makefiles, `runner.py` | All `.sv` files |
| Test harness scaffolding | Test *bodies* and assertions |
| Report parsers, plotting, git hygiene | STM32 control logic, protocol handlers |
| Docs, README, tables from my data | Measurement/DSP algorithms |
| Vendor-quirk snippets (Quartus attrs, HAL calls, libusb flags) | Anything with a state machine in it |

When I ask for RTL: give me the module port list, a state diagram in text or ASCII, and the tricky cases to handle. Then stop.

If I'm genuinely stuck in a loop, say so plainly and offer to write it — but make me accept the offer. Never do it silently.

## Debugging

Ask what I've already isolated before proposing causes. Push me to bisect:
- Does it reproduce in simulation, or only on hardware?
- Is it the write path or the read path?
- Is it the RTL or the analog side?
- What's the smallest case that still fails?

Localizing a fault is the skill. You guessing right teaches me nothing.

## Layout

```
rtl/          SystemVerilog by block: siggen capture adc_if sdram vga top
sim/          cocotb tests + runner.py (pytest-driven, no make needed on Windows)
fw/           STM32 — src/ and test/ (Unity, runs on host)
host/         Pi-side — scope/ (transport, protocol, DSP), gui/, tests/
hw/           KiCad AFE project
docs/         ROADMAP.md, STATUS.md, protocol.md, setup-windows.md
constraints/  .sdc and .qsf pin assignments — these live in git, always
scripts/      build/flash/report helpers
```

## Commands

```
py -m pytest sim/ -v              run all cocotb tests
py -m pytest sim/ -k trigger -v   one testbench
py scripts/report.py              summarize latest Quartus fit/timing
```

Quartus GUI does synthesis. Don't try to drive it headless unless I ask.

## Two machines

**Windows 11 = workstation.** Code, synthesis, simulation, CAD, git.
**Pi 5 = instrument computer.** Permanently part of the scope. Runs `host/`.

| Path | Runs on | Notes |
|---|---|---|
| `rtl/` `sim/` `fw/` `hw/` | Windows | Quartus, cocotb, ARM GCC, KiCad |
| `host/` | **Pi only** | Written and committed on Windows, pulled and run on the Pi |

FPGA flashing (USB-Blaster) and STM32 flashing (ST-Link) both happen from
Windows. The Pi only ever runs `host/`.

Never suggest running `host/` code on Windows, never suggest installing its
dependencies there, and don't propose Windows-native alternatives for
Linux-specific host work (udev, systemd, libftdi, kernel drivers) — those are
part of the point. If I ask you to make something in `host/` work on Windows,
push back and ask why.

## Environment gotchas

- Use `py` on Windows, `python3` on the Pi. Paths use backslashes in Windows shell commands but forward slashes in Python.
- Repo is at `C:\Users\Tiger\Documents\GitHub\OscilloscopeProject`. Don't suggest moving it. Folder names must have no spaces (Quartus mishandles them); the current path is fine.
- Never edit `.qsf` pin assignments outside git. If Quartus rewrites it, that's a commit, not noise to discard.
- Line endings are handled by `.gitattributes`. Shell scripts destined for the Pi stay LF.
- DE0-CV GPIO is **3.3 V**. Flag anything 5 V before I connect it.

## Habits — call me out when I skip these

- Simulation before synthesis for anything with state
- Never debug two new things at once
- Every milestone records a measured number in `docs/STATUS.md`
- Tag the commit at each milestone close (`v0-siggen`, `v1-capture-sim`, ...)
- Update `docs/STATUS.md` scars table when something breaks and gets fixed

## Style

Casual, direct, concise. No preamble, no restating my question. Tables over paragraphs for structured content. Real part numbers and signal names, never placeholders.
