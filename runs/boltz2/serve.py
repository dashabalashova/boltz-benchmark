from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import urllib.request

import time
import json

import os

from boltz.main import *
from boltz.model.models.boltz2 import Boltz2
from dataclasses import asdict, dataclass

app = FastAPI()


CCD_URL = "https://huggingface.co/boltz-community/boltz-1/resolve/main/ccd.pkl"
MOL_URL = "https://huggingface.co/boltz-community/boltz-2/resolve/main/mols.tar"

BOLTZ1_URL_WITH_FALLBACK = [
    "https://model-gateway.boltz.bio/boltz1_conf.ckpt",
    "https://huggingface.co/boltz-community/boltz-1/resolve/main/boltz1_conf.ckpt",
]

BOLTZ2_URL_WITH_FALLBACK = [
    "https://model-gateway.boltz.bio/boltz2_conf.ckpt",
    "https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_conf.ckpt",
]

BOLTZ2_AFFINITY_URL_WITH_FALLBACK = [
    "https://model-gateway.boltz.bio/boltz2_aff.ckpt",
    "https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_aff.ckpt",
]


cache = Path("/app/.boltz")
cache = Path(cache).expanduser()

mols = cache / "mols"
tar_mols = cache / "mols.tar"
if not tar_mols.exists():
    print(
        f"Downloading the CCD data to {tar_mols}. "
        "This may take a bit of time. You may change the cache directory "
        "with the --cache flag."
    )
    urllib.request.urlretrieve(MOL_URL, str(tar_mols))
if not mols.exists():
    print(
        f"Extracting the CCD data to {mols}. "
        "This may take a bit of time. You may change the cache directory "
        "with the --cache flag."
    )
    with tarfile.open(str(tar_mols), "r") as tar:
        tar.extractall(cache)

model = cache / "boltz2_conf.ckpt"
if not model.exists():
    print(
        f"Downloading the Boltz-2 weights to {model}. You may "
        "change the cache directory with the --cache flag."
    )
    for i, url in enumerate(BOLTZ2_URL_WITH_FALLBACK):
        try:
            urllib.request.urlretrieve(url, str(model))
            break
        except Exception as e:
            if i == len(BOLTZ2_URL_WITH_FALLBACK) - 1:
                msg = f"Failed to download model from all URLs. Last error: {e}"
                raise RuntimeError(msg) from e
            continue

affinity_model = cache / "boltz2_aff.ckpt"
if not affinity_model.exists():
    print(
        f"Downloading the Boltz-2 affinity weights to {affinity_model}. You may "
        "change the cache directory with the --cache flag."
    )
    for i, url in enumerate(BOLTZ2_AFFINITY_URL_WITH_FALLBACK):
        try:
            urllib.request.urlretrieve(url, str(affinity_model))
            break
        except Exception as e:
            if i == len(BOLTZ2_AFFINITY_URL_WITH_FALLBACK) - 1:
                msg = f"Failed to download model from all URLs. Last error: {e}"
                raise RuntimeError(msg) from e
            continue

checkpoint = cache / "boltz2_conf.ckpt"
model_cls = Boltz2

predict_args = {
    "recycling_steps": 1,
    "sampling_steps": 20,
    "diffusion_samples": 1,
    "max_parallel_samples": 1,
    "write_confidence_summary": True
}

@dataclass
class PairformerArgsV2:
    """Pairformer arguments."""
    num_blocks: int = 64
    num_heads: int = 16
    dropout: float = 0.0
    activation_checkpointing: bool = False
    offload_to_cpu: bool = False
    v2: bool = True

@dataclass
class Boltz2DiffusionParams:
    """Diffusion process parameters."""
    gamma_0: float = 0.8
    gamma_min: float = 1.0
    noise_scale: float = 1.003
    rho: float = 7
    step_scale: float = 1.5
    sigma_min: float = 0.0001
    sigma_max: float = 160.0
    sigma_data: float = 16.0
    P_mean: float = -1.2
    P_std: float = 1.5
    coordinate_augmentation: bool = True
    alignment_reverse_diff: bool = True
    synchronize_sigmas: bool = True

diffusion_params = Boltz2DiffusionParams()
step_scale = 1.5
diffusion_params.step_scale = step_scale
pairformer_args = PairformerArgsV2()

@dataclass
class MSAModuleArgs:
    """MSA module arguments."""
    msa_s: int = 64
    msa_blocks: int = 4
    msa_dropout: float = 0.0
    z_dropout: float = 0.0
    use_paired_feature: bool = True
    pairwise_head_width: int = 32
    pairwise_num_heads: int = 4
    activation_checkpointing: bool = False
    offload_to_cpu: bool = False
    subsample_msa: bool = False
    num_subsampled_msa: int = 1024

msa_args = MSAModuleArgs(
    subsample_msa=False,
    num_subsampled_msa=1024,
    use_paired_feature=True)

@dataclass
class BoltzSteeringParams:
    """Steering parameters."""
    fk_steering: bool = False
    num_particles: int = 3
    fk_lambda: float = 4.0
    fk_resampling_interval: int = 3
    physical_guidance_update: bool = False
    contact_guidance_update: bool = True
    num_gd_steps: int = 20

steering_args = BoltzSteeringParams()
model_module = model_cls.load_from_checkpoint(
    checkpoint,
    strict=True,
    predict_args=predict_args,
    map_location="cpu",
    diffusion_process_args=asdict(diffusion_params),
    ema=False,
    use_kernels=True,
    pairformer_args=asdict(pairformer_args),
    msa_args=asdict(msa_args),
    steering_args=asdict(steering_args),
)
model_module.eval()

class PredictRequest(BaseModel):
    data: str
    sampling_steps: int = 20

@app.post("/predict")
async def predict(req: PredictRequest):
    start = time.time()
    data = Path(req.data).expanduser()
    out_dir = Path("/app/results")
    out_dir = Path(out_dir).expanduser()
    out_dir = out_dir / f"boltz_results_{data.stem}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path('/app/results/').expanduser()
    out_dir = out_dir / f"boltz_results_{data.stem}"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = check_inputs(data)
    ccd_path = cache / "ccd.pkl"
    mol_dir = cache / "mols"
    process_inputs(
        data=data,
        out_dir=out_dir,
        ccd_path=ccd_path,
        mol_dir=mol_dir,
        boltz2=True, 
        use_msa_server=True,
        msa_server_url="https://api.colabfold.com",
        msa_pairing_strategy="greedy"
    )

    manifest = Manifest.load(out_dir / "processed" / "manifest.json")
    filtered_manifest = filter_inputs_structure(
        manifest=manifest,
        outdir=out_dir,
        override=False
    )

    processed_dir = out_dir / "processed"
    processed = BoltzProcessedInput(
        manifest=filtered_manifest,
        targets_dir=processed_dir / "structures",
        msa_dir=processed_dir / "msa",
        constraints_dir=(
            (processed_dir / "constraints")
            if (processed_dir / "constraints").exists()
            else None
        ),
        template_dir=(
            (processed_dir / "templates")
            if (processed_dir / "templates").exists()
            else None
        ),
        extra_mols_dir=(
            (processed_dir / "mols") if (processed_dir / "mols").exists() else None
        ),
    )

    strategy = "auto"
    diffusion_params = Boltz2DiffusionParams()
    step_scale = 1.5
    diffusion_params.step_scale = step_scale
    pairformer_args = PairformerArgsV2()

    msa_args = MSAModuleArgs()

    pred_writer = BoltzWriter(
        data_dir=processed.targets_dir,
        output_dir=out_dir / "predictions",
        output_format="mmcif",
        boltz2=True,
        write_embeddings=True,
    )

    trainer = Trainer(
        default_root_dir=out_dir,
        strategy=strategy,
        callbacks=[pred_writer],
        accelerator="gpu",
        devices=1,
        precision="bf16-mixed",
    )

    if filtered_manifest.records:
        msg = f"Running structure prediction for {len(filtered_manifest.records)} input"
        msg += "s." if len(filtered_manifest.records) > 1 else "."
        print(msg)
    else:
        msg = "No valid inputs found. Please check your input data."
        print(msg)
        return {
            "status": "error",
            "message": msg,
        }

    data_module = Boltz2InferenceDataModule(
        manifest=processed.manifest,
        target_dir=processed.targets_dir,
        msa_dir=processed.msa_dir,
        mol_dir=mol_dir,
        num_workers=1,
        constraints_dir=processed.constraints_dir,
        template_dir=processed.template_dir,
        extra_mols_dir=processed.extra_mols_dir,
        override_method=None,
    )

    checkpoint = cache / "boltz2_conf.ckpt"

    model_module.predict_args["sampling_steps"] = req.sampling_steps
    trainer.predict(
        model_module,
        datamodule=data_module,
        return_predictions=False,
    )

    elapsed = time.time() - start
    result = {
        "status": "ok",
        "out_dir": str(out_dir),
        "elapsed_s": round(elapsed, 2),
    }
    print(json.dumps(result, indent=2), "\n")
    return result