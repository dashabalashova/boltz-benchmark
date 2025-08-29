FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y git python3-pip && pip3 install uv

WORKDIR /app

RUN git clone https://github.com/dashabalashova/boltz.git /app/boltz

WORKDIR /app/boltz

RUN uv pip install --system -e .[cuda]

RUN uv pip install --system fastapi uvicorn

COPY runs/boltz2b/serve.py /app/serve.py

WORKDIR /app
ENTRYPOINT ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
