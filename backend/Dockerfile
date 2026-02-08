FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py onto_bridge.py signal_packet.py ./

ENV PORT=8080

CMD ["python", "app.py"]
