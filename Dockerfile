FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default: run scheduler every 24 hours
CMD ["python", "run.py", "--schedule", "--interval", "24"]
