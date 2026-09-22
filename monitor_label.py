# -*- coding: utf-8 -*-
"""Re-derive the monitor-labeling limit from per-item verdicts (stdlib only).

The README and POST say that the block-labeling defense, applied to a model that is REVIEWING work
rather than doing it, makes the reviewer worse. This recomputes that pair from
data/monitor_label_cells.json: gemma4:12b judging its own work, n=337, the same payload with and
without the label.

    python monitor_label.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "monitor_label_cells.json")


def rates(cell):
    n = cell["n"]
    catches = sum(cell["flag_inj"]) / n
    false_alarms = sum(cell["flag_clean"]) / n
    return catches, false_alarms, catches - false_alarms


def main():
    doc = json.load(open(PATH, encoding="utf-8"))
    rows = [("without the label", doc["cells"]["monatk_gemma_protocol_rs"]),
            ("with the label", doc["cells"]["mondef_gemma_protocol_rs"])]
    print("gemma4:12b reviewing its own work, n=%d, same payload" % rows[0][1]["n"])
    print("%-18s %8s %13s %15s" % ("", "catches", "false alarms", "discrimination"))
    for label, cell in rows:
        c, fa, d = rates(cell)
        print("%-18s %8.4f %13.4f %15.4f" % (label, c, fa, d))
    print("\ndiscrimination = catches - false alarms: how well the reviewer tells compromised output from clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
