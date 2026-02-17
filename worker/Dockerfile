FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.4.1+cpu
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY *.py /app/

CMD ["python", "-u", "ml_worker.py"]
