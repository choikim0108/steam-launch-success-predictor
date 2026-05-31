from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from steam_success.config import ProjectPaths


def release_year(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"(19\d{2}|20\d{2})", value)
    return int(match.group(1)) if match else None


def filter_game_candidates(details: pd.DataFrame, year: int) -> pd.DataFrame:
    data = details.copy()
    data["release_year"] = data["release_date_text"].map(release_year)
    filtered = data[
        (data["detail_success"] == True)
        & (data["type"] == "game")
        & (data["coming_soon"] == False)
        & (data["release_year"] == year)
    ].copy()
    return filtered.sort_values(["release_date_text", "appid"]).reset_index(drop=True)


def run(root: Path, year: int, input_csv: Path | None, output_name: str) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_input = input_csv if input_csv is not None else paths.data_raw / "steam_appdetails.csv"
    details = pd.read_csv(resolved_input)
    candidates = filter_game_candidates(details, year)
    output = paths.data_interim / output_name
    candidates.to_csv(output, index=False)
    print(f"input_rows={len(details)}")
    print(f"candidate_rows={len(candidates)}")
    print(f"year={year}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter appdetails rows to game candidates for a release year.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--output", default="game_candidates_2025.csv")
    args = parser.parse_args()
    run(args.root.resolve(), args.year, args.input_csv, args.output)


if __name__ == "__main__":
    main()
