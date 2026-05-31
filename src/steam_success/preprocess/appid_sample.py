from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from steam_success.config import ProjectPaths, SETTINGS


def sample_appids(appids: pd.DataFrame, random_size: int, recent_size: int, random_state: int) -> pd.DataFrame:
    if "appid" not in appids.columns:
        raise ValueError("Input CSV must contain an appid column.")

    data = appids.copy()
    data["appid"] = data["appid"].astype(int)
    data = data.drop_duplicates("appid").sort_values("appid").reset_index(drop=True)

    samples: list[pd.DataFrame] = []
    if random_size > 0:
        random_sample = data.sample(n=min(random_size, len(data)), random_state=random_state).copy()
        random_sample["sampling_strategy"] = "random"
        samples.append(random_sample)

    if recent_size > 0:
        recent_sample = data.sort_values("appid", ascending=False).head(recent_size).copy()
        recent_sample["sampling_strategy"] = "high_appid_recent_proxy"
        samples.append(recent_sample)

    if not samples:
        return pd.DataFrame(columns=list(data.columns) + ["sampling_strategy"])

    combined = pd.concat(samples, ignore_index=True)
    strategy = (
        combined.groupby("appid")["sampling_strategy"]
        .apply(lambda values: ";".join(sorted(set(values))))
        .rename("sampling_strategy")
        .reset_index()
    )
    merged = data.merge(strategy, on="appid", how="inner")
    return merged.sort_values(["sampling_strategy", "appid"]).reset_index(drop=True)


def run(root: Path, input_csv: Path | None, output_name: str, random_size: int, recent_size: int) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_input = input_csv if input_csv is not None else paths.data_raw / "steam_official_appids.csv"
    appids = pd.read_csv(resolved_input)
    sampled = sample_appids(appids, random_size, recent_size, SETTINGS.random_state)
    output = paths.data_interim / output_name
    sampled.to_csv(output, index=False)
    print(f"input_rows={len(appids)}")
    print(f"sampled_rows={len(sampled)}")
    print(f"random_size={random_size}")
    print(f"recent_size={recent_size}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create reproducible appid candidates for slower appdetails collection.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--output", default="appid_candidates_for_details.csv")
    parser.add_argument("--random-size", type=int, default=5000)
    parser.add_argument("--recent-size", type=int, default=5000)
    args = parser.parse_args()
    run(args.root.resolve(), args.input_csv, args.output, args.random_size, args.recent_size)


if __name__ == "__main__":
    main()
