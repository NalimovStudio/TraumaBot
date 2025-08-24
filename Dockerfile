FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Устанавливаем системные зависимости (используем правильное имя пакета)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry>=2.1.4

# Копируем зависимости
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости Python
RUN poetry install --no-interaction --no-root

# Копируем весь код
COPY . .

# Создаем симлинки для обратной совместимости
RUN ln -sf /app /TraumaBot && \
    ln -sf /app /source