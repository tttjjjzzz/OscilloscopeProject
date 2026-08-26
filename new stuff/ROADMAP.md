# DE0-CV Oscilloscope — Project Roadmap

**Hardware on hand:** Terasic DE0-CV (Cyclone V 5CEBA4, 64 MB SDRAM, VGA, 2× 40-pin GPIO), STM32 dev boards, Raspberry Pi 5, MacBook.

**Total scope:** ~30 weeks part-time. Every milestone below is independently demo-able and stands alone if you stop there.

---

## Ground rules

1. **Never debug two new things at once.** New RTL against known-good signals. New analog against known-good RTL. If you break this rule you will lose a weekend, guaranteed.
2. **Simulate before you synthesize.** A Quartus compile is 5–10 minutes. A cocotb run is 2 seconds. Anything with state goes through a testbench first.
3. **Instrument from day one.** Every milestone has numbers attached. Those numbers are the resume bullets.
4. **Tag every milestone in git.** `v0-siggen`, `v1-capture-sim`, etc. You want to be able to point at a working commit.
5. **Write the README as you go.** A screenshot + a measured number per milestone. Do not save this for the end.

---

## Repo layout

```
scope/
├── rtl/                    # SystemVerilog
│   ├── siggen/
│   ├── capture/            # ring buffer, trigger FSM, decimator
│   ├── adc_if/
│   ├── sdram/
│   ├── vga/
│   └── top/
├── sim/                    # cocotb testbenches
│   ├── test_trigger.py
│   ├── test_ringbuf.py
│   └── Makefile
├── fw/                     # STM32
│   ├── src/
│   ├── test/               # Unity host-side unit tests
│   └── Makefile
├── host/                   # Pi
│   ├── scope/              # transport, protocol, DSP
│   ├── gui/
│   └── tests/
├── hw/                     # KiCad AFE project
├── docs/                   # timing budgets, protocol spec, cal procedure
└── constraints/            # .sdc, pin assignments
```

Constraints and pin assignments live in git from day one. Do not assign pins in the Quartus GUI and let it live only in the `.qsf`.

---

## Toolchain setup (do this first, ~half a day)

| Tool | Where | Notes |
|---|---|---|
| Quartus Prime Lite | Linux box or Windows | Cyclone V is supported in Lite. macOS is not — you'll drive it from the Arch box or Windows. |
| Icarus Verilog + cocotb + GTKWave | Anywhere, incl. Mac | `pip install cocotb cocotb-test pytest` |
| STM32CubeCLT / arm-none-eabi-gcc | Anywhere | CMake + Ninja, not CubeIDE, if you want CI later |
| Python 3.11 + numpy/scipy/pyqtgraph | Pi 5 | |

**Verilator** is worth it later for speed, but Icarus is faster to get running and plenty for these module sizes. Start with Icarus.

---

# Phase A — Digital only (no purchases)

## M0 — FPGA signal generator
**~1 week**

**Goal:** Get the Quartus flow under your fingers on a project where nothing analog can lie to you.

**Build:**
- Parameterized clock divider → square wave, 1 Hz to 10 MHz
- Duty cycle control (0–100% in 1% steps)
- Frequency/duty selectable via onboard switches, displayed on the 7-segments
- Pulse-train mode: N pulses on button press, then idle
- Output on GPIO header pins + mirrored to LEDs at slow rates

**Learn:** SystemVerilog basics, `always_ff` vs `always_comb`, parameters, counters, synchronous reset discipline, Quartus project structure, **pin assignment via `.qsf` in git**, and your first `.sdc` timing constraints.

**Exit criteria:**
- Verify frequency accuracy on at least 5 settings using the STM32's input capture timer as your reference counter (you don't have a scope yet — the STM32 *is* your measurement instrument)
- Timing Analyzer reports zero failing paths at 50 MHz
- Resource utilization recorded in README

**Demo:** LEDs blinking at a rate you dialed in on the switches. Modest, but the toolchain is now real.

**Gotcha:** Async reset + no synchronizer on the switch inputs = metastability. Debounce and synchronize every external input. Do it now so it's habit.

---

## M1 — Capture engine, in simulation only
**~2 weeks**

This is the single highest-value milestone in the whole project. It's also the one most people skip.

**Goal:** A verified circular buffer + trigger FSM that has never touched hardware.

**Build (RTL):**
- `ring_buffer`: continuous write, wrap-around, tracks whether it has filled at least once
- `trigger_engine`: rising/falling/either edge, programmable level, **hysteresis**, holdoff counter
- `capture_ctrl` FSM: `IDLE → ARMED → PRE_FILL → TRIGGERED → POST_FILL → DONE`
- Programmable pre/post-trigger split (e.g. 25% pre / 75% post)

**Build (sim):**
- cocotb testbench feeding synthetic waveforms: square, ramp, noisy sine, a single glitch buried in a flat line
- Assert: the trigger sample lands at exactly the expected index in the output buffer
- Assert: pre-trigger data is correct **even when the trigger fires before the buffer has filled once** ← this is the edge case everyone gets wrong
- Assert: holdoff actually suppresses re-triggers
- Assert: wrap-around at buffer boundary preserves ordering
- Randomized test: random trigger positions × random pre/post splits, 1000 iterations

**Learn:** cocotb, coroutine-based stimulus, functional coverage thinking, waveform debug in GTKWave, and — most importantly — **verification as a discipline**. This is a large fraction of what a real FPGA job is.

**Exit criteria:**
- All tests pass, including the randomized sweep
- You can articulate why the pre-fill counter exists
- Testbench runs from a single `make` in `sim/`

**Demo:** `pytest` output, green. Plus a GTKWave screenshot showing a captured window with the trigger point marked.

**Resume bullet:** *"Verified a pre/post-trigger capture engine with randomized cocotb testbenches covering buffer wrap-around and pre-fill edge cases prior to synthesis."*

---

## M2 — 8-channel logic analyzer
**~2 weeks**

**Goal:** M1's engine on real pins, capturing real signals. First genuinely useful instrument.

**Build:**
- 8 GPIO inputs → synchronizers → M1 capture engine
- 100 MSPS sampling (PLL from the 50 MHz onboard clock)
- M10K block RAM buffer, start with 8k samples deep
- Trigger on any channel, edge or pattern match
- Readout over UART (115200 → 921600) to the Pi
- Pi-side: Python reader + matplotlib timing diagram

**Learn:** PLLs and clock domains, block RAM inference vs instantiation, CDC and synchronizer chains, UART TX in RTL, framing a binary protocol, SignalTap.

**Exit criteria:**
- Capture your M0 signal generator's output and confirm the measured frequency matches what you dialed in
- Capture SPI traffic between an STM32 and any peripheral you have lying around
- Trigger on a pattern (e.g. CS falling while CLK high) and confirm alignment

**Demo:** Timing diagram of real SPI traffic, on your screen, captured by hardware you wrote.

**This is already useful for Thunderbots.** You now have a logic analyzer you didn't have last month.

**Gotcha:** UART at 921600 for 8k samples is ~90 ms. Fine here. Do not scale this approach to the ADC — see M4.

---

## M3 — STM32 control plane + signal source
**~2 weeks**

**Goal:** Give the STM32 its permanent job, and turn it into your stimulus generator.

**Build (control):**
- SPI slave register file in the FPGA (address/data, read/write)
- STM32 as SPI master, **DMA-driven, not polled**
- Command protocol: `SET_TRIG_LEVEL`, `SET_TRIG_EDGE`, `SET_PRE_POST`, `ARM`, `FORCE_TRIG`, `GET_STATUS`, `ABORT`
- Command parser + instrument state machine on the STM32
- Error handling: timeout, bad opcode, illegal state transition
- Host-side Unity unit tests for the parser (runs on your laptop, no hardware)

**Build (signal source):**
- Precise PWM: variable frequency and duty, timer-based
- 1 kHz probe-compensation square wave with fast edges (you'll need this at M7)
- DAC output: sine, ramp, triangle via DMA-fed DAC
- Sweep mode for frequency response measurement later

**Learn:** STM32 SPI + DMA, register-file design in RTL, protocol design, defensive firmware, unit testing embedded C.

**Exit criteria:**
- Change trigger level from the Pi → through STM32 → FPGA → observe behavior change
- Unit tests pass in CI
- Signal generator output verified against your M2 logic analyzer

**Resume bullet:** *"Designed a DMA-driven SPI control plane between an STM32 and an FPGA register file with a fault-tolerant command state machine."*

---

# Phase B — Analog acquisition

## M4 — ADC + high-speed transport
**~2 weeks — first purchase, ~$40**

**Buy:**

| Item | ~Cost | Note |
|---|---|---|
| AD9226 module (12-bit, 65 MSPS, parallel) | $20 | **Verify it's strapped for 3.3 V DRVDD before connecting** |
| FT232H breakout | $15 | Sync FIFO 245 mode |
| Ribbon cable / headers | $5 | Keep leads short |

**Goal:** Real analog samples, at real speed, into the Pi.

**Build:**
- ADC parallel interface: capture on the ADC clock, dual-clock FIFO into the system domain
- FT232H synchronous FIFO interface in RTL (this is the fiddly part — read the FT232H datasheet's timing diagrams carefully)
- Pi-side: libftdi in userspace, frame reader, throughput benchmark
- Feed the ADC from the STM32 DAC through a simple RC filter and a resistor divider — **no protection circuit yet, so only known-safe low-voltage sources**

**Learn:** CDC done properly with async FIFOs, source-synchronous capture, USB bulk transfer, backpressure and flow control.

**Exit criteria:**
- Sustained transfer measured and recorded (target ≥20 MB/s)
- Capture a DAC sine, FFT it in NumPy, confirm the frequency matches what the STM32 generated
- SNR/ENOB measured on a clean sine — record it, you'll compare after adding the XO at M7

**Gotcha:** Ground bounce and coupling on a 40-pin ribbon between two boards is genuinely bad. Expect visible noise. Don't chase it — it goes away at M7. Just record the baseline.

---

## M5 — Real GUI
**~3 weeks**

**Goal:** Something that looks and behaves like an oscilloscope.

**Build:**
- **pyqtgraph** (not matplotlib — matplotlib can't do 20+ fps redraw)
- RUN / STOP / SINGLE / FORCE
- Timebase and vertical scale controls, 1-2-5 sequence
- **Sinc interpolation** on the display path (this is not optional — linear interpolation gives 11% amplitude error at 10 MHz)
- Cursors: time and voltage, with delta readout
- Auto-measurements: Vpp, Vrms, mean, min/max, frequency, period, duty cycle, rise/fall time
- Threaded acquisition so the UI never blocks
- Save capture to `.npy` / CSV

**Learn:** pyqtgraph, threading and queue-based producer/consumer, DSP fundamentals, measurement algorithms (edge detection with hysteresis, 10%/90% rise time).

**Exit criteria:**
- ≥20 waveform updates/sec, measured and recorded
- Measurements agree with the STM32's programmed values within 1%
- UI stays responsive under continuous acquisition

**Demo:** This is the first screenshot that makes people go "wait, you built that?"

---

## M6 — Deep memory + serious triggers
**~3 weeks**

**Goal:** Exceed the capability of a low-end commercial scope in at least one dimension.

**Build:**
- **SDRAM controller** for the DE0-CV's 64 MB (write your own, or use the Terasic/Altera controller and focus your effort elsewhere — either is defensible, but writing your own is the bigger learning win)
- Deep capture: millions of samples per acquisition
- **Min/max peak-detect decimation**: at slow timebases, keep both extremes per bucket instead of every Nth sample. Without this you miss narrow glitches entirely. Most hobby scopes get this wrong.
- Advanced triggers: pulse width (>, <, inside/outside range), runt, timeout
- Zoom/pan through deep memory without re-triggering

**Learn:** SDRAM timing (tRCD, tRP, tRFC, refresh), burst transfers, memory arbitration between write and read ports, hierarchical waveform storage.

**Exit criteria:**
- Capture depth recorded (target: >1 M samples)
- Generate a 50 ns glitch on the STM32 once per second, capture at a 100 ms/div timebase, and **see it** — that's the min/max decimator proving itself
- Pulse-width trigger catches a runt you deliberately generate

**Resume bullet:** *"Implemented min/max peak-detect decimation and an SDRAM-backed 1M-sample capture buffer, preserving 50 ns glitch visibility at 100 ms/div."*

---

# Phase C — Real instrument

## M7 — Analog front end PCB
**~5 weeks — second purchase, ~$105 + PCB**

This is the hardest milestone and the most transferable. It's also where you need a reference scope.

**Design:**

```
BNC → protection → attenuator → buffer → PGA/filter → ADC driver → ADC
```

| Block | Part | Purpose |
|---|---|---|
| Protection | BAV199 clamps + series R + TVS | Survive 24 V and DC-link discharge |
| Attenuator | 0.1% thin-film + C0G + 2–20 pF trimmers, G6K relays | ÷1 / ÷10 / ÷100, frequency-compensated |
| Coupling | 1 µF film + relay bypass | AC/DC |
| Buffer | AD8065 | 1 MΩ ∥ ~20 pF in, low-Z out |
| PGA + AA filter | LMH6518 | SPI gain control, built-in 20 MHz AA filter, differential out |
| Clock | 65 MHz XO | <5 ps jitter vs. 100–300 ps from the PLL |
| Power | LM27762 | ±5 V from single rail, low noise |
| Offset | STM32 internal DAC, buffered | Vertical position / DC null |

**PCB:** 4-layer, JLCPCB, ~$15/5. Uninterrupted ground plane under the entire analog chain. Split AVDD/DVDD with ferrites, single-point join under the ADC.

**Learn:** Analog design, frequency compensation, PCB layout for mixed-signal, power integrity, hot-air assembly (LMH6518 is TQFN-24).

**Exit criteria:**
- Square wave at 1 kHz shows flat top on all three attenuator ranges after trimmer adjustment
- −3 dB bandwidth measured via STM32 sweep, recorded per range
- **Re-measure SNR/ENOB and compare against your M4 baseline** — this is the payoff of the XO and the ground plane, and it's a great writeup

**Gotchas:**
- Input protection from the first rev. You *will* short something to 24 V.
- Clamping into a rail only works if the rail can sink current. Add a bleeder or zener.
- C0G caps only in the signal path. X7R's voltage coefficient makes gain amplitude-dependent.
- Budget for a rev B. Nobody's first analog board is right.

**Reference scope:** You cannot tune compensated attenuator trimmers blind. Used Rigol DS1054Z, ~$250, before you start this milestone.

---

## M8 — Calibration
**~1 week**

**Goal:** Turn a waveform display into a measurement instrument. This is the difference that most DIY scopes never cross.

**Build:**
- LM4040-2.5 voltage reference on the board
- Gain and offset calibration routine per range
- Cal constants stored in STM32 flash, applied on the Pi
- Self-cal command
- Documented cal procedure in `docs/`

**Exit criteria:**
- Gain error <1% across all ranges, verified against DMM + reference scope
- Documented accuracy spec, published in the README
- Before/after error table

**Resume bullet:** *"Developed a calibration procedure reducing gain error from 3.2% to <0.8% across 8 vertical ranges, with constants stored in MCU flash."*

---

## M9 — Channel 2, decode, standalone mode
**~4 weeks**

**Build:**
- Second AFE channel (rev B PCB, or a second board)
- Cross-channel triggering, channel math (A−B)
- Protocol decode on the Pi: UART, SPI, I²C, **CAN** — annotated overlays on the waveform
- **VGA standalone mode**: render the waveform directly from the FPGA to a monitor, no PC. Framebuffer, raster timing, column-wise min/max rendering, on-screen readout of settings.

**Learn:** VGA timing generation, framebuffer design, on-chip rendering, protocol state machines.

**Demo:** Unplug the Pi. It still works. That's the moment it becomes an *instrument* rather than a peripheral.

**CAN decode is directly useful to you** on both Thunderbots and anything Tesla-adjacent.

---

## M10 — Equivalent-time sampling + ecosystem
**~5 weeks**

**Build:**
- **Random-interleaved ETS**: on repetitive signals, build the waveform from thousands of triggers at varying sub-sample offsets. Requires a fine time-to-digital measurement of trigger-to-sample-clock phase. Effective sample rate goes to several hundred MSPS.
- **libsigrok driver** so your scope works in PulseView
- SCPI command interface over TCP
- Optional: FPGA FFT as a *benchmarking exercise* — compare latency, throughput, and DSP/LUT utilization against NumPy on the Pi 5. Do it to have the comparison, not because the instrument needs it.

**Exit criteria:**
- Effective sample rate in ETS mode, measured and recorded
- Your instrument enumerates and captures in PulseView

**Resume bullet:** *"Implemented random-interleaved equivalent-time sampling achieving an effective 500 MSa/s from a 65 MSPS ADC; contributed a libsigrok backend driver."*

---

# Purchase schedule

| When | Item | ~Cost |
|---|---|---|
| Now | Nothing. M0–M3 use what you own. | $0 |
| Before M4 | AD9226 + FT232H + cables | $40 |
| Before M7 | Used Rigol DS1054Z (or equivalent) | $250 |
| Before M7 | AFE BOM: LMH6518, AD8065 ×2, G6K ×8, LM27762, 0.1% thin film, trimmers, BNC, XO, passives | $105 |
| Before M7 | 4-layer PCB ×5 | $15 |
| Before M7 | Hot air station (if you don't have one) | $60 |
| Before M7 | 10× passive probes ×2 | $30 |
| **Total** | | **~$500** |

Spread over ~6 months. The reference scope is over half of it and is the one item that's genuinely non-optional — M8 does not exist without something to calibrate against.

---

# Numbers to collect

Instrument from day one. These are the sentences that go on the resume.

| Metric | Milestone |
|---|---|
| Resource utilization (LE/M10K/DSP) | every RTL milestone |
| Fmax and timing slack | every RTL milestone |
| Transport throughput (MB/s) | M4 |
| SNR / ENOB — baseline vs. post-AFE | M4, M7 |
| Waveform update rate (Hz) | M5 |
| Capture depth (samples) | M6 |
| Minimum visible glitch width at slow timebase | M6 |
| −3 dB bandwidth per range | M7 |
| Gain/offset error, before and after cal | M8 |
| Effective sample rate in ETS | M10 |

---

# Honest expected specs at completion

| Parameter | Value |
|---|---|
| Channels | 2 |
| Sample rate | 65 MSa/s real-time |
| Resolution | 12 bit |
| Analog bandwidth | ~20 MHz (AA-filter limited) |
| Single-shot usable BW | ~8 MHz (rise-time limited) |
| ETS effective rate | 200–500 MSa/s, repetitive signals |
| Memory depth | >1 M samples |
| Vertical ranges | ~8, via ÷1/÷10/÷100 + PGA |
| Input | 1 MΩ ∥ ~20 pF, AC/DC coupled |

**Never probe mains with this.** No isolation; ground is tied to your Pi and your laptop.

---

# Where this can go wrong

| Risk | Mitigation |
|---|---|
| **Stalling at M7** — analog is a different discipline and momentum dies | M0–M6 already produce a working instrument. Treat M7 as a separate sub-project with its own start date. |
| Debugging RTL and analog simultaneously | Never violate ground rule #1. Known-good on one side, always. |
| Scope creep into "let me add HMCAD1511 at 1 GSa/s" | Note it as a v2. Finish v1 first. |
| Analog board rev A doesn't work | Expected. Budget for rev B in time and money. |
| Losing interest around week 15 | The M6 → M7 boundary is the danger zone. Ship a proper README + demo video at M6 so the project has a defensible stopping point. |

---

# If you only do part of it

**M0–M2 (5 weeks):** a working logic analyzer, verified in simulation. Legitimately useful, legitimately resume-worthy.

**M0–M6 (15 weeks):** a functioning oscilloscope with deep memory and real triggers. This alone is a strong portfolio project.

**M0–M10 (30 weeks):** an instrument, with a calibration spec, that plugs into the open-source EE tooling ecosystem. This is a thing people notice.

---

**Start tonight: M0.** Nothing to buy, nothing to wait for.
