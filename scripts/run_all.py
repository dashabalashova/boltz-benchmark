#!/usr/bin/env python3
import subprocess
import sys

scripts = [
    "runs/boltz2nim/loop_boltz2nim.py",
    "runs/boltz2/loop_boltz2.py",
    "runs/boltz2b/loop_boltz2b.py",
]

def run_scripts():
    for script in scripts:
        print(f"\n▶▶▶ Running {script}\n")
        try:
            subprocess.run([sys.executable, script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {script} ({e})")
            break

if __name__ == "__main__":
    run_scripts()
