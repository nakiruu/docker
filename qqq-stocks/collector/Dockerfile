# --- build stage: compile native extensions ---
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- runtime stage: no compiler, non-root user ---
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

RUN useradd --no-create-home --shell /bin/false appuser

COPY collector.py .

USER appuser

CMD ["python", "-u", "collector.py"]
