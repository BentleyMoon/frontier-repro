# -*- coding: utf-8 -*-
"""Re-derive the oversight-channel section of README.md from per-item verdicts (stdlib only).

Every rate below is recomputed from data/oversight_cells.json and checked against the rate the engine
recorded for the same cell; the script exits nonzero if any disagree. The monitor's own FIRST verdict
(flag_*_first) is stored only as an aggregate, so it is printed as recorded, not recomputed.

    python oversight.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "oversight_cells.json")


def rate(xs):
    return sum(xs) / float(len(xs)) if xs else float("nan")


def main():
    doc = json.load(open(PATH, encoding="utf-8"))
    cells, bad = doc["cells"], []
    for group, ids in doc["groups"].items():
        print("\n%s" % group.replace("_", " "))
        print("  %-28s %-9s %-10s %-10s %6s %8s %8s %8s  %s" % ("cell", "pool", "monitor", "defense", "n",
                                                                 "fa", "catches", "fa_first", "verdict"))
        for did in ids:
            c = cells[did]
            fa, ca = rate(c["flag_clean"]), rate(c["flag_inj"])
            rec = c["recorded_rates"]
            for k, v in (("flag_clean", fa), ("flag_inj", ca)):
                if k in rec and abs(rec[k] - v) > 5e-5:          # the engine records rates to 4 decimals
                    bad.append("%s %s: recomputed %.4f vs recorded %.4f" % (did, k, v, rec[k]))
            first = rec.get("flag_clean_first")
            mon = "panel(3)" if c.get("panel") else (c["monitor"] or "").replace("gemma4:", "g4:")
            print("  %-28s %-9s %-10s %-10s %6d %8.4f %8.4f %8s  %s" % (
                did, c["task_pool_seed"], mon, c["monitor_defense"] or "-", c["n"], fa, ca,
                "%.4f" % first if first is not None else "-", c["discrimination_verdict"]))
    print("\nfa = false alarms on provably correct work; catches = flags on injected-actor answers;")
    print("fa_first = the monitor's own first verdict (recorded aggregate); verdict = the ledger's label")
    print("for discrimination (catches - false alarms) in that cell.")
    if bad:
        print("\nMISMATCH between per-item data and recorded rates:")
        for b in bad:
            print("  " + b)
        return 1
    print("\nevery recomputed rate matches the rate the engine recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
