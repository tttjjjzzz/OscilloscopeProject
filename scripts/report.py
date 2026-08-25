"""Summarize the latest Quartus fit and timing reports.

    py scripts/report.py
    py scripts/report.py --project-dir rtl/top

Pulls resource utilization and worst-case slack out of output_files/*.rpt so
you can paste them straight into docs/STATUS.md. Quartus report formatting
varies between versions -- if a field comes back blank, open the .rpt and
adjust the pattern rather than trusting a silent None.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def find_reports(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for rpt in root.rglob("output_files/*.rpt"):
        if rpt.name.endswith(".fit.rpt"):
            out.setdefault("fit", rpt)
        elif rpt.name.endswith(".sta.rpt"):
            out.setdefault("sta", rpt)
        elif rpt.name.endswith(".map.rpt"):
            out.setdefault("map", rpt)
    return out


def grab(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def parse_fit(path: Path) -> dict[str, str | None]:
    t = path.read_text(errors="ignore")
    return {
        "device": grab(t, r"Device\s*;\s*(\S+)"),
        "logic_utilization": grab(t, r"Logic utilization.*?;\s*([^;]+);"),
        "alms": grab(t, r"ALMs needed.*?;\s*([^;]+);"),
        "registers": grab(t, r"Total registers\s*;\s*([^;]+);"),
        "block_memory_bits": grab(t, r"Total block memory bits\s*;\s*([^;]+);"),
        "dsp_blocks": grab(t, r"Total DSP Blocks\s*;\s*([^;]+);"),
        "pins": grab(t, r"Total pins\s*;\s*([^;]+);"),
        "plls": grab(t, r"Total PLLs\s*;\s*([^;]+);"),
    }


def parse_sta(path: Path) -> dict[str, object]:
    t = path.read_text(errors="ignore")
    fmax = re.findall(r";\s*([\d.]+)\s*MHz\s*;\s*([\d.]+)\s*MHz\s*;\s*(\S+)\s*;", t)
    slacks = re.findall(r"Worst-case\s+(\w+)\s+slack\s+is\s+(-?[\d.]+)", t, re.IGNORECASE)
    return {
        "fmax": [{"restricted": r, "unrestricted": u, "clock": c} for u, r, c in fmax[:6]],
        "slack": {k.lower(): float(v) for k, v in slacks},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default=str(REPO), help="where to search for output_files/")
    args = ap.parse_args()

    reports = find_reports(Path(args.project_dir))
    if not reports:
        print("no Quartus reports found -- compile first")
        return

    if "fit" in reports:
        print(f"\n=== fit  ({reports['fit'].name}) ===")
        for k, v in parse_fit(reports["fit"]).items():
            print(f"  {k:22} {v if v is not None else '(not found)'}")

    if "sta" in reports:
        print(f"\n=== timing  ({reports['sta'].name}) ===")
        sta = parse_sta(reports["sta"])
        for entry in sta["fmax"]:
            print(f"  fmax {entry['clock']:24} {entry['restricted']} MHz (restricted)")
        if sta["slack"]:
            for k, v in sta["slack"].items():
                flag = "  <-- FAILING" if v < 0 else ""
                print(f"  worst {k:20} slack {v:>8.3f} ns{flag}")
        else:
            print("  no slack lines matched -- check the .sta.rpt format")

    print("\npaste into docs/STATUS.md\n")


if __name__ == "__main__":
    main()
