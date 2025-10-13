#!/usr/bin/env python3
"""
casp16_args.py

Read YAMLs from a directory and send them to Boltz2 NIM.
Now supports command-line arguments:
  --yaml-dir         directory with yaml files (default: data/L1000-example/yamls-with-msa)
  --sampling_steps   sampling steps (default: 10)
  --out-dir          where to save responses (default: results)
  --base-url         NIM base URL (default: http://localhost:8000)
  --timeout          request timeout seconds (default: 1200)
"""
import argparse
import json
import glob
import os
import time
from typing import Dict, Any
from pathlib import Path

import requests
import yaml

def query_boltz2_nim(
    input_data: Dict[str, Any],
    base_url: str = "http://localhost:8000",
    timeout: int = 600
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/biology/mit/boltz2/predict"
    headers = {"Content-Type": "application/json"}
    
    print("POST ->", url)
    print("payload keys:", list(input_data.keys()))
    resp = requests.post(url, json=input_data, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def build_msa_field(msa_value, seq: str):
    if msa_value is None:
        return {"uniref90": {"a3m": {"alignment": f">seq1\n{seq}", "format": "a3m"}}}
    if isinstance(msa_value, dict):
        return msa_value
    p = Path(msa_value)
    if p.exists():
        return {"uniref90": {"a3m": {"alignment": p.read_text(), "format": "a3m"}}}
    return {"uniref90": {"a3m": {"alignment": f">seq1\n{seq}", "format": "a3m"}}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml-dir", type=str, default="examples/yamls_L1000",
                        help="Directory with yaml files (one protein per yaml)")
    parser.add_argument("--sampling_steps", type=int, default=200, help="sampling_steps for Boltz2")
    parser.add_argument("--out-dir", type=str, default="results", help="Output directory for responses")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="NIM base URL")
    parser.add_argument("--timeout", type=int, default=1200, help="HTTP request timeout (s)")
    args = parser.parse_args()

    yaml_dir = Path(args.yaml_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    yaml_files = sorted(glob.glob(str(yaml_dir / "*.yaml")))
    if not yaml_files:
        print(f"No YAML files found in {yaml_dir}")
        return

    # optional: try to find a common msa file in a predictable location
    msa_path = yaml_dir.parent / "msa" / "uniref.a3m"
    msa_field = None
    if msa_path.exists():
        print("Using MSA file:", msa_path)
        msa_text = msa_path.read_text()
        msa_field = {"uniref90": {"a3m": {"alignment": msa_text, "format": "a3m"}}}
    else:
        print("No uniref.a3m found at", msa_path, "- will inline minimal MSA from sequence if needed.")

    for yaml_file in yaml_files:
        print("▶ Processing", yaml_file)
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        protein_entry = next((s["protein"] for s in data.get("sequences", []) if "protein" in s), None)
        if not protein_entry:
            print("  Skipping (no protein entry):", yaml_file)
            continue

        seq_id = protein_entry.get("id", Path(yaml_file).stem)
        sequence = protein_entry.get("sequence", "")

        # pick msa specified in yaml if present, else global msa_field or minimal inline
        yaml_msa = data.get("msa") or protein_entry.get("msa")
        msa_payload = build_msa_field(yaml_msa, sequence) if (yaml_msa or msa_field is None) else msa_field

        ligands = []
        
        for idx, s in enumerate(data.get("sequences", []), start=1):
            if "ligand" not in s:
                continue
            lig = s["ligand"]
            # получить smiles и id (fallback на L1, L2 ...)
            smiles = lig.get("smiles") if isinstance(lig, dict) else None
            if not smiles:
                print(f"  Warning: ligand entry #{idx} in {yaml_file} has no smiles — skipping")
                continue
            ligand_id = lig.get("id") or f"L{len(ligands)+1}"
            ligands.append({
                "smiles": str(smiles).strip(),
                "id": ligand_id,
                "predict_affinity": True
            })

        example_input = {
            "polymers": [
                {
                    "id": "A",
                    "molecule_type": "protein",
                    "sequence": sequence,
                    "msa": msa_payload,
                },
            ],
            
            **({"ligands": ligands} if ligands else {}),
            "recycling_steps": 3,
            "sampling_steps": args.sampling_steps,
            "diffusion_samples": 1,
            "step_scale": 1.5,
            "without_potentials": True
        }

        print(f"  id={seq_id}, seq_len={len(sequence)}, sampling_steps={args.sampling_steps}")
        t0 = time.perf_counter()
        try:
            result = query_boltz2_nim(example_input, base_url=args.base_url, timeout=args.timeout)
            t1 = time.perf_counter()
            elapsed = round(t1 - t0, 2)
            print(f"  ✔ Success ({elapsed}s). Saving response.")
            out_path = out_dir / f"{seq_id}_steps{args.sampling_steps}_{int(time.time())}.json"
            out_path.write_text(json.dumps({"status": "ok", "elapsed_s": elapsed, "response": result}, indent=2))
        except requests.exceptions.HTTPError as e:
            t1 = time.perf_counter()
            elapsed = round(t1 - t0, 2)
            text = ""
            try:
                text = e.response.text
            except Exception:
                pass
            print(f"  ✖ HTTP error ({elapsed}s):", e, " response:", text)
            err_path = out_dir / f"{seq_id}_steps{args.sampling_steps}_{int(time.time())}_error.json"
            err_path.write_text(json.dumps({"status": "error", "elapsed_s": elapsed, "error": text}, indent=2))
        except Exception as e:
            t1 = time.perf_counter()
            elapsed = round(t1 - t0, 2)
            print(f"  ✖ Request failed ({elapsed}s):", e)

if __name__ == "__main__":
    main()
