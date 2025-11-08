
# boltz-benchmark

```
git clone https://github.com/dashabalashova/boltz-benchmark.git
```

# boltz-2

run predictions
```
git clone https://github.com/jwohlwend/boltz/
cd boltz

python3 -m venv .venvs/boltz
source .venvs/boltz/bin/activate
pip install -e .[cuda]

screen -S screen1
source .venvs/boltz/bin/activate
mkdir -p runs/casp16/
cp ../boltz-benchmark/runs/casp16/run.sh runs/casp16/run.sh
cp -r ../boltz-benchmark/data/processed/examples/msa examples
cp -r ../boltz-benchmark/data/processed/examples/yamls_L1000 examples
cp -r ../boltz-benchmark/data/processed/examples/yamls_L3000 examples
chmod +x runs/casp16/run.sh
runs/casp16/run.sh
# Ctrl+a+d

deactivate
cd ..
```

# boltz-2 batched

run predictions
```
git clone https://github.com/dashabalashova/boltz-screen.git
mv boltz-screen boltz2-b
cd boltz2-b

python3 -m venv .venvs/boltz2-b
source .venvs/boltz2-b/bin/activate
pip install -e .[cuda]

screen -S screen2
source .venvs/boltz2-b/bin/activate
mkdir -p runs/casp16_b/
cp ../boltz-benchmark/runs/casp16_b/run.sh runs/casp16_b/run.sh
cp -r ../boltz-benchmark/data/processed/examples/msa examples
cp -r ../boltz-benchmark/data/processed/examples/yamls_L1000 examples
cp -r ../boltz-benchmark/data/processed/examples/yamls_L3000 examples
chmod +x runs/casp16_b/run.sh
runs/casp16_b/run.sh
# Ctrl+a+d

deactivate
cd ..
```

# boltz-2 nim

run predictions
```
mkdir boltz2-nim
cd boltz2-nim

docker login nvcr.io
export NGC_API_KEY=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
export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p $LOCAL_NIM_CACHE
chmod -R 777 $LOCAL_NIM_CACHE
docker pull nvcr.io/nim/mit/boltz2:latest

docker run -it \
  --gpus all \
  -p 8000:8000 \
  -e NGC_API_KEY \
  -v "$HOME/.cache/nim":/opt/nim/.cache \
  --name boltz2nim \
  nvcr.io/nim/mit/boltz2:latest

screen -S screen3
mkdir -p runs/casp16_nim/
cp ../boltz-benchmark/runs/casp16_nim/run.sh runs/casp16_nim/run.sh
cp ../boltz-benchmark/runs/casp16_nim/casp16.py runs/casp16_nim/casp16.py
chmod +x runs/casp16_nim/run.sh
runs/casp16_nim/run.sh
cd ..
```

# run benchmark

collect affinities
```
cd boltz-benchmark
chmod +x scripts/collect_affinities.sh
scripts/collect_affinities.sh
```

copy logs
```
cp -r ../boltz/logs results/logs
cp -r ../boltz2-b/logs results/logs_b4
cp -r ../boltz2-nim/logs results/logs_nim
```

run notebooks:
- notebooks/logs_b0.ipynb
- notebooks/logs_b4.ipynb
- notebooks/logs_nim.ipynb
- notebooks/casp16_samp_steps.ipynb
- notebooks/casp16_nbatch-batch-nim.ipynb