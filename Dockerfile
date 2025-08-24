# Многоэтапная сборка для оптимизации размера контейнера
FROM python:3.11-slim as builder

# Устанавливаем системные зависимости для сборки в одном слое
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ВАЖНО: Копируем только requirements.txt для кеширования
COPY requirements.txt .

# Устанавливаем Python зависимости с оптимизацией
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Производственный образ
FROM python:3.11-slim as production

# Устанавливаем runtime зависимости и создаем пользователя в одном слое
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создаем рабочую директорию и директории для данных
WORKDIR /app
RUN mkdir -p /app/logs /app/data

# Копируем код приложения (это должно быть последним для лучшего кеширования)
COPY --chown=appuser:appuser . .
RUN chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Открываем порт для FastAPI
EXPOSE 8000

# Health check для мониторинга состояния (оптимизированный)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["python", "main.py"]

# Метаданные
LABEL maintainer="FACEIT CS2 Bot Team"
LABEL description="Telegram bot for FACEIT CS2 player statistics"
LABEL version="1.0.0"