from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from steam_success.config import ProjectPaths


def release_year(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"(19\d{2}|20\d{2})", value)
    return int(match.group(1)) if match else None


LABEL_CUTOFF_90D = date(2026, 3, 3)


def parse_release_date(value: object) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y"):
        try:
            parsed = datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
        return parsed.date()
    return None


def _truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def filter_game_candidates(details: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    data = details.copy()
    data["release_year"] = data["release_date_text"].map(release_year)
    data["release_date"] = data["release_date_text"].map(parse_release_date)
    data["label_eligible_90d"] = data["release_date"].map(lambda value: bool(value and value <= LABEL_CUTOFF_90D))
    filtered = data[
        (_truthy(data["detail_success"]))
        & (data["type"] == "game")
        & (~_truthy(data["coming_soon"]))
        & (data["release_year"] >= start_year)
        & (data["release_year"] <= end_year)
    ].copy()
    return filtered.sort_values(["release_date", "appid"], na_position="last").reset_index(drop=True)


def run(root: Path, start_year: int, end_year: int, input_csv: Path | None, output_name: str | None) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_input = input_csv if input_csv is not None else paths.data_raw / "steam_appdetails.csv"
    details = pd.read_csv(resolved_input)
    candidates = filter_game_candidates(details, start_year, end_year)
    resolved_output = output_name or (
        f"game_candidates_{start_year}.csv"
        if start_year == end_year
        else f"game_candidates_{start_year}_{end_year}.csv"
    )
    output = paths.data_interim / resolved_output
    candidates.to_csv(output, index=False)
    print(f"input_rows={len(details)}")
    print(f"candidate_rows={len(candidates)}")
    print(f"start_year={start_year}")
    print(f"end_year={end_year}")
    print(f"label_eligible_90d_rows={int(candidates['label_eligible_90d'].sum()) if not candidates.empty else 0}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter appdetails rows to game candidates for a release year range.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--year", type=int, default=None, help="Backward-compatible single-year filter.")
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    start_year = args.start_year if args.start_year is not None else (args.year if args.year is not None else 2025)
    end_year = args.end_year if args.end_year is not None else (args.year if args.year is not None else start_year)
    run(args.root.resolve(), start_year, end_year, args.input_csv, args.output)


if __name__ == "__main__":
    main()
