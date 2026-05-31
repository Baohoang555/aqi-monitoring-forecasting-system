"""
PH-04: Build Parquet Datalake — AirGlobal AQI Dataset
Author: An

Đọc processed data từ PH-03 → partition theo country/year → ghi Parquet datalake.

Input : outputs/ph03/processed_airglobal_features.pkl
Output: data/datalake/aqi/<country>/<year>/data.parquet

Chạy từ thư mục gốc project:
    python src/build_datalake.py
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

# ── Project root (same pattern as preprocess_features.py) ─────────────────────
def find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current.parent] + list(current.parents):
        if (parent / "data").exists() and (
            (parent / "src").exists() or (parent / "outputs").exists()
        ):
            return parent
        if (parent / "data").exists() and (parent / "ph03_preprocessing").exists():
            return parent
    return current.parents[1]


BASE_DIR      = find_project_root()
PROCESSED_PKL = BASE_DIR / "outputs" / "ph03" / "processed_airglobal_features.pkl"
DATALAKE_DIR  = BASE_DIR / "data" / "datalake" / "aqi"

# ── Helpers ───────────────────────────────────────────────────────────────────
def to_partition_key(value: str) -> str:
    """Lowercase, spaces/special chars → underscore. E.g. 'South Korea' → 'south_korea'."""
    s = str(value).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "unknown"


def log(msg: str) -> None:
    print(msg, flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 72)
    print("PH-04 BUILD DATALAKE | AirGlobal AQI")
    print("=" * 72)

    # 1. Load processed data
    log(f"\n1. Loading processed data from: {PROCESSED_PKL.relative_to(BASE_DIR)}")
    if not PROCESSED_PKL.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {PROCESSED_PKL}\n"
            "Hãy chạy preprocess_features.py trước."
        )

    df = pd.read_pickle(PROCESSED_PKL)
    log(f"   Rows    : {len(df):,}")
    log(f"   Columns : {len(df.columns)}")

    # 2. Validate required columns
    for col in ["country", "date"]:
        if col not in df.columns:
            raise ValueError(f"Cột '{col}' không có trong processed data.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["_year"] = df["date"].dt.year

    missing_year = df["_year"].isna().sum()
    if missing_year:
        log(f"   Warning: {missing_year:,} rows thiếu year — sẽ bỏ qua.")
    df = df.dropna(subset=["_year"]).copy()
    df["_year"] = df["_year"].astype(int)

    # 3. Build partitions
    log(f"\n2. Building datalake → {DATALAKE_DIR.relative_to(BASE_DIR)}")
    DATALAKE_DIR.mkdir(parents=True, exist_ok=True)

    groups     = df.groupby(["country", "_year"], sort=True)
    total_rows = 0
    total_files = 0
    country_set: set = set()

    drop_cols = ["_year"]  # internal helper column, không ghi vào parquet

    for (country, year), group in groups:
        country_key   = to_partition_key(str(country))
        partition_dir = DATALAKE_DIR / country_key / str(year)
        partition_dir.mkdir(parents=True, exist_ok=True)

        out_path = partition_dir / "data.parquet"
        group.drop(columns=drop_cols).to_parquet(out_path, index=False, engine="pyarrow")

        total_rows  += len(group)
        total_files += 1
        country_set.add(country_key)

    log(f"   Countries written : {len(country_set)}")
    log(f"   Parquet files     : {total_files:,}")
    log(f"   Total rows written: {total_rows:,}")

    # 4. Verify — spot-check 1 file và tổng record
    log("\n3. Verifying datalake...")
    all_files   = sorted(DATALAKE_DIR.rglob("*.parquet"))
    verify_rows = 0
    for fp in all_files:
        verify_rows += len(pd.read_parquet(fp, engine="pyarrow"))

    match = "✅ OK" if verify_rows == total_rows else f"⚠️  MISMATCH (expected {total_rows:,})"
    log(f"   Re-counted rows : {verify_rows:,}  {match}")

    # Sample schema from first file
    sample_df = pd.read_parquet(all_files[0], engine="pyarrow")
    rel_path  = all_files[0].relative_to(DATALAKE_DIR)
    log(f"   Sample partition: {rel_path}")
    log(f"   Shape           : {sample_df.shape}")

    print("\n" + "=" * 72)
    print("-> PH-04 DONE")
    print(f"   Datalake : {DATALAKE_DIR.relative_to(BASE_DIR)}")
    print(f"   Structure: <country>/<year>/data.parquet")
    print(f"   To read  : pd.read_parquet(DATALAKE_DIR / '<country>' / '<year>' / 'data.parquet')")
    print(f"   Or all   : pd.concat([pd.read_parquet(f) for f in DATALAKE_DIR.rglob('*.parquet')])")
    print("=" * 72)


if __name__ == "__main__":
    main()