#!/usr/bin/env python3
import pandas as pd
import shutil
from pathlib import Path

# Paths
processed_dir = Path("data/cache2/processed/")
xlsx_in = Path("data/cache2/raw/cache2-supplementary-tables-1-9-including-review-compound-and-computation-information.xlsx")
fasta_in = Path("data/cache2/raw/YP_009725308.1.fasta")
tsv_out = processed_dir / "smiles.tsv"
fasta_out = processed_dir / "protein.fasta"

# 1) make sure the directory is there
processed_dir.mkdir(parents=True, exist_ok=True)

# 2) read Excel & write TSV
df = pd.read_excel(
    xlsx_in,
    sheet_name=1,
    header=3,
    usecols=["CACHE ID", "Smiles", "NSP13 KD (µM)"]
).reset_index(drop=True)
df.columns = ["id_raw", "smiles", "NSP13 KD (µM)"]
df["id"] = [f"s_{i}" for i in df.index]
df["NSP13 KD (µM)"] = (
    df["NSP13 KD (µM)"]
    .astype(str)
    .str.replace(">", "", regex=False)
    .astype(float)
)
df["binder"] = df["NSP13 KD (µM)"] > 0
df = df[["id", "id_raw", "smiles", "binder"]]
df.to_csv(tsv_out, sep="\t", index=False)
print(f"Wrote {len(df)} rows to {tsv_out}")

# 3) copy FASTA
shutil.copy(fasta_in, fasta_out)
print(f"Copied {fasta_in} → {fasta_out}")
