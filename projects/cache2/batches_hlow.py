import subprocess
from pathlib import Path

dir_in = Path('data/cache2/processed/yamls/')
dir_out = Path('test_results/')
num_of_repeats = 1
batch_size_lst = [1, 2, 4]

for repeat in range(num_of_repeats):
    for batch_size in batch_size_lst:
        
        yamls_in = dir_in / f"balanced_64_r{repeat}"
        out_name = f'hlow_b{batch_size}_r{repeat}'
        
        aff_out = dir_out / out_name
        aff_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "boltz", "predict", str(yamls_in),
            "--use_msa_server", "--screening_mode",
            "--batch_size", str(batch_size),
            "--recycling_steps", "2",
            "--sampling_steps", "2",
            "--diffusion_samples", "2",
            "--recycling_steps_affinity", "2",
            "--sampling_steps_affinity", "2",
            "--diffusion_samples_affinity", "2",
            "--out_dir", str(aff_out)
        ]

        print(f"\nRunning: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)