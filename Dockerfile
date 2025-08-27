FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf && \
    ping -c 4 deb.debian.org || echo "DNS resolution failed"

# Установка curl с явным зеркалом
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry>=2.1.4

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-interaction --no-root

COPY . .

# Создаем симлинки для обратной совместимости
RUN ln -sf /app /TraumaBot && \
    ln -sf /app /source