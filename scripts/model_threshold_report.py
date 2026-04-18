from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"


def load_meta(slot: str) -> dict[str, Any] | None:
    path = MODELS_DIR / f"model_{slot}_meta.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def pct(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "n/a"


def num(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "n/a"


def signed(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):+.{digits}f}"
    except Exception:
        return "n/a"


def summarize(slot: str, meta: dict[str, Any]) -> list[str]:
    test_risk = meta.get("test_risk") or {}
    lines = [
        f"[{slot}] trained={meta.get('train_date', 'n/a')} data={meta.get('data_start', 'n/a')}..{meta.get('data_end', 'n/a')}",
        (
            f"  UP: thr={num(meta.get('threshold'))} val_wr={pct(meta.get('val_wr'))} "
            f"test_wr={pct(meta.get('test_wr'))} trades/day={num(meta.get('test_trades_per_day'), 1)} "
            f"ev/day={signed(meta.get('up_ev_per_day'))}"
        ),
        (
            f"  DOWN: enabled={meta.get('down_enabled', False)} thr={num(meta.get('down_threshold'))} "
            f"val_wr={pct(meta.get('down_val_wr'))} test_wr={pct(meta.get('down_test_wr'))} "
            f"trades/day={num(meta.get('down_test_tpd'), 1)} ev/day={signed(meta.get('down_ev_per_day'))}"
        ),
        (
            f"  WFV: folds={meta.get('wf_folds', 'n/a')} avg={pct(meta.get('wf_avg_wr'))} "
            f"min={pct(meta.get('wf_min_wr'))} max={pct(meta.get('wf_max_wr'))} std={pct(meta.get('wf_std_wr'))}"
        ),
        (
            f"  Risk: max_dd=${num(test_risk.get('max_dd_dollar'), 4)} "
            f"dd_pct={pct(test_risk.get('max_dd_pct'))} "
            f"loss_streak={test_risk.get('max_loss_streak', 'n/a')} blocked={meta.get('blocked', 'n/a')}"
        ),
    ]
    return lines


def compare(current: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    metrics = [
        ("UP threshold", candidate.get("threshold"), current.get("threshold"), 3, False),
        ("UP test WR", candidate.get("test_wr"), current.get("test_wr"), 4, True),
        ("UP EV/day", candidate.get("up_ev_per_day"), current.get("up_ev_per_day"), 4, False),
        ("DOWN threshold", candidate.get("down_threshold"), current.get("down_threshold"), 3, False),
        ("DOWN test WR", candidate.get("down_test_wr"), current.get("down_test_wr"), 4, True),
        ("DOWN EV/day", candidate.get("down_ev_per_day"), current.get("down_ev_per_day"), 4, False),
        ("WF avg WR", candidate.get("wf_avg_wr"), current.get("wf_avg_wr"), 4, True),
    ]
    lines = ["[comparison] candidate - current"]
    for label, cand, curr, digits, is_ratio in metrics:
        if cand is None or curr is None:
            continue
        delta = float(cand) - float(curr)
        if is_ratio:
            lines.append(
                f"  {label}: {pct(cand)} vs {pct(curr)} delta={delta * 100:+.2f} pp"
            )
        else:
            lines.append(
                f"  {label}: {cand:.{digits}f} vs {curr:.{digits}f} delta={delta:+.{digits}f}"
            )
    cand_blocked = candidate.get("blocked")
    curr_blocked = current.get("blocked")
    lines.append(f"  Gate: candidate_blocked={cand_blocked} current_blocked={curr_blocked}")
    return lines


def main() -> int:
    current = load_meta("current")
    candidate = load_meta("candidate")

    if not current and not candidate:
        print("No model metadata files found in models/.")
        return 1

    if current:
        print("\n".join(summarize("current", current)))
    else:
        print("[current] missing")

    if candidate:
        print()
        print("\n".join(summarize("candidate", candidate)))

    if current and candidate:
        print()
        print("\n".join(compare(current, candidate)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
