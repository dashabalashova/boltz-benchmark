import subprocess
import time
from pathlib import Path
import json

out_file = Path("seconds_boltz2nim.tsv")

with out_file.open("w") as f:
    f.write("run\tsteps\tseconds\n")
    for i in range(1, 5):
        for steps in [10, 20, 50, 100, 200, 400, 600, 800]:
            start = time.time()
            payload = json.dumps({
                "data": "/app/data/yamls",
                "sampling_steps": steps,
            })
            subprocess.run(["sudo", "rm", "-rf", "results/boltz2nim/boltz_results_yamls"])
            subprocess.run(["python3", "runs/boltz2nim/run.py", "--sampling_steps", str(steps)])
            elapsed = round(time.time() - start, 2)
            print(f"Run {i}, steps {steps}: {elapsed} seconds")
            f.write(f"{i}\t{steps}\t{elapsed}\n")
            f.flush()
