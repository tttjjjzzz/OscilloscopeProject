# Protocol spec

Two independent interfaces. Keep them separate — that separation is the whole
architectural point.

| Link | Direction | Carries |
|---|---|---|
| SPI | STM32 ⇄ FPGA | Configuration and status. Small, latency-tolerant. |
| USB (FT232H sync FIFO) | FPGA → Pi | Sample data. Large, throughput-critical. |
| USB CDC | Pi ⇄ STM32 | Human-level commands |

---

## 1. FPGA register map (SPI)

Fill this in during M3. Design it before you write RTL — a register map you
invented incrementally becomes unusable by M6.

**Transaction format:** _decide and document — e.g. 1 byte address with R/W in
MSB, then N data bytes, MSB first._

| Addr | Name | Access | Width | Reset | Description |
|---|---|---|---|---|---|
| 0x00 | `ID` | R | 8 | | Magic byte, sanity check the link is alive |
| 0x01 | `VERSION` | R | 8 | | Gateware version |
| 0x02 | `CTRL` | RW | 8 | 0x00 | arm / abort / force trigger |
| 0x03 | `STATUS` | R | 8 | | idle / armed / triggered / done / overflow |
| | `TRIG_LEVEL` | RW | | | |
| | `TRIG_CONFIG` | RW | | | edge, hysteresis, source |
| | `TRIG_HOLDOFF` | RW | | | |
| | `PRE_POST` | RW | | | pre-trigger fraction |
| | `CAPTURE_LEN` | RW | | | |
| | `DECIMATION` | RW | | | rate + min/max mode |
| | `TRIG_POSITION` | R | | | where the trigger landed |
| | `SAMPLE_COUNT` | R | | | |

**Design notes to resolve:**
- Which registers are safe to write while armed? Which require idle?
- Are multi-byte registers latched atomically, or can a read tear mid-update?
- What happens on an unknown address — return 0, or set an error flag?
- Does a read of `STATUS` clear sticky bits?

---

## 2. STM32 command protocol (Pi ⇄ STM32)

Human-level, one level above the register map. The STM32 translates.

| Command | Args | Returns |
|---|---|---|
| `PING` | — | `PONG`, firmware version |
| `SET_TRIG_LEVEL` | volts | ack |
| `SET_TRIG_EDGE` | rising / falling / either | ack |
| `SET_TRIG_MODE` | auto / normal / single | ack |
| `SET_PRE_POST` | fraction | ack |
| `SET_RANGE` | channel, volts/div | ack — drives relays and PGA |
| `SET_COUPLING` | channel, AC / DC | ack |
| `SET_OFFSET` | channel, volts | ack — drives DAC |
| `ARM` | — | ack |
| `ABORT` | — | ack |
| `FORCE_TRIG` | — | ack |
| `GET_STATUS` | — | state, trigger position, sample count |
| `SELFCAL` | — | progress, result |
| `SIGGEN` | waveform, freq, amplitude | ack — stimulus output |

**Framing:** _decide — length-prefixed binary, or line-based ASCII?_
ASCII is far easier to debug by hand in a terminal, which matters a lot in M3.
Binary is faster, which does not matter on this link.

**Error handling to specify:**
- Unknown command
- Argument out of range
- Command illegal in current state (e.g. `SET_RANGE` while armed)
- SPI timeout talking to the FPGA
- Watchdog / recovery behavior

---

## 3. Sample transport (FPGA → Pi)

**Frame header:** _define before writing the RTL._

Needs at minimum: magic word, frame length, sample count, trigger position,
sample rate, decimation mode, a sequence number, and a status/overflow flag.

**Questions to answer:**
- Fixed-size or variable-size frames?
- How does the Pi resynchronize after a dropped byte?
- Is there a checksum? Over the header only, or the payload too?
- 12-bit samples: packed two-per-three-bytes, or padded to 16 bits?
  Padding wastes 25% of throughput; packing costs RTL and host CPU. Decide and
  record why.
- What does the FPGA do when the Pi stops reading — drop, stall, or overwrite?

---

## Changelog

| Date | Change |
|---|---|
| | |
