# --- BUILDER STAGE ---
FROM python:3.12 as builder

WORKDIR /app

RUN pip install "poetry==2.1.4"

RUN poetry --version

# Copy only the Poetry configuration files first
# This allows Docker to cache this layer if pyproject.toml and poetry.lock don't change
COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

# Export dependencies to a requirements.txt file
# --only main ensures only main dependencies are included (no dev)
# --without-hashes is often needed for compatibility with pip in Docker,
# though using hashes is more secure if you can manage it.
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create a virtual environment and install dependencies into it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt


# --- FINAL STAGE ---
FROM python:3.12-slim

WORKDIR /TraumaBot
ENV PYTHONPATH=/TraumaBot

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the created virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
# Set environment variables for the virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

COPY . .