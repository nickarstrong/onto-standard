# ONTO-Bench Leaderboard Docker Setup

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-leaderboard.txt .
RUN pip install --no-cache-dir -r requirements-leaderboard.txt

# Copy application
COPY leaderboard/ ./leaderboard/
COPY data/ ./data/

# Create data directories
RUN mkdir -p leaderboard_data/submissions

# Expose port
EXPOSE 8080

# Seed baseline results and run
CMD ["sh", "-c", "python leaderboard/api.py --seed && uvicorn leaderboard.api:app --host 0.0.0.0 --port 8080"]
