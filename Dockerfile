FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

ENV DENO_INSTALL=/usr/local/deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md /app/
COPY app /app/app

RUN uv pip install --system --no-cache-dir .

COPY . /app/

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
