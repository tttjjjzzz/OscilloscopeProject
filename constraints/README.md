# constraints

`.sdc` timing constraints and `.qsf` pin assignments live here and are tracked
in git. This is not optional.

**Why:** Quartus lets you assign pins in the GUI, and it writes them into the
`.qsf`. If that file is gitignored or lives outside the repo, your pinout
exists only on one machine and is one reinstall away from gone. Everyone who
does this loses a day rediscovering their own pin assignments.

## Files

| File | Contents |
|---|---|
| `de0cv_pins.qsf` | Board pin assignments — clocks, LEDs, switches, GPIO headers |
| `de0cv_base.sdc` | Clock definitions, input/output delays, false paths |

Source them into the Quartus project rather than duplicating.

## Rules

- After Quartus rewrites a `.qsf`, that's a commit. Read the diff — an
  unexpected change usually means you clicked something in the GUI you didn't
  intend.
- Every clock gets a `create_clock`. An unconstrained clock means the timing
  report is meaningless, and Quartus will happily report success on a design
  that doesn't meet timing.
- Cross-domain paths get an explicit `set_false_path` or a proper synchronizer.
  Never both — if you're false-pathing it, be sure you actually handled the CDC.
- Asynchronous inputs from the GPIO headers need `set_false_path -from`, plus a
  two-flop synchronizer in RTL.

## DE0-CV specifics

The board reference manual and Terasic's system CD contain the official pin
assignment file. Start from theirs rather than transcribing the schematic by
hand — a mistyped pin on a GPIO header is a genuinely painful bug to find.

GPIO headers are **3.3 V**. Confirm any external module's I/O voltage before
connecting it. This is how the AD9226 module kills FPGA banks at M4.
