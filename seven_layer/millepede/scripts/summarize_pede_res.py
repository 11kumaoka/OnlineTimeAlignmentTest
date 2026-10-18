#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ACTIVE = [1001, 1002, 1003, 2001, 2002, 2003]


def parse_res(path: Path):
    out = {}
    for line in path.read_text().splitlines():
        s = line.split()
        if len(s) < 5:
            continue
        try:
            lab = int(s[0])
        except ValueError:
            continue
        if lab in ACTIVE:
            out[lab] = {
                "value": float(s[1].replace("D", "E")),
                "par_err": float(s[4].replace("D", "E")),
            }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--comparison", required=True)
    args = ap.parse_args()

    b = parse_res(Path(args.baseline))
    c = parse_res(Path(args.comparison))

    print("label baseline comparison delta comp_err")
    for lab in ACTIVE:
        bv = b.get(lab, {}).get("value", float("nan"))
        cv = c.get(lab, {}).get("value", float("nan"))
        ce = c.get(lab, {}).get("par_err", float("nan"))
        print(lab, bv, cv, cv - bv, ce)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
