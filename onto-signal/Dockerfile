FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY server.py .
COPY streamer.py .

# Создаём папку для сигналов
RUN mkdir -p /app/signal

# Порт (Railway задаёт через $PORT)
ENV PORT=8081

# Запуск
CMD ["python", "server.py"]
# force rebuild v1.1
