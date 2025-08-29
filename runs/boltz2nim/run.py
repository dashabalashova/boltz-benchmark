import requests
import json
from typing import Dict, Any
import glob
import yaml
import os
import argparse


def query_boltz2_nim(
    input_data: Dict[str, Any],
    base_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """
    Query the Boltz2 NIM with input data.
    
    Args:
        input_data: Dictionary containing the prediction request data
        base_url: Base URL of the NIM service (default: http://localhost:8000)
    
    Returns:
        Dictionary containing the prediction response
    """
    url = f"{base_url}/biology/mit/boltz2/predict"
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=input_data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error querying NIM: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")
        raise


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--sampling_steps", type=int, default=20,
                        help="Number of sampling steps for Boltz2")
    args = parser.parse_args()

    yaml_dir = "data/yamls"
    output_dir = "data/results/boltz2nim"
    os.makedirs(output_dir, exist_ok=True)

    yaml_files = glob.glob(os.path.join(yaml_dir, "*.yaml"))

    for yaml_file in yaml_files:
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        protein_entry = next((s["protein"] for s in data.get("sequences", []) if "protein" in s), None)

        seq_id = protein_entry.get("id", "unknown")
        sequence = protein_entry.get("sequence", "")

        print(f"▶ Processing {yaml_file}, id={seq_id}, len={len(sequence)}")
        SEQUENCE = sequence

        example_input = {"polymers":[
            {
                "id": "A",
                "molecule_type": "protein",
                "sequence": SEQUENCE,
                "msa": {
                        "uniref90": {
                            "a3m": {
                                "alignment": f">seq1\n{SEQUENCE}",
                                "format": "a3m"
                            }
                        }
                    }
            },
            
        ],
        "recycling_steps": 1,
        "sampling_steps": args.sampling_steps,
        "diffusion_samples": 1,
        "step_scale": 1.5,
        "without_potentials": True
        }
        
        try:
            result = query_boltz2_nim(example_input)
            print("Prediction result:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Failed to get prediction: {e}")
