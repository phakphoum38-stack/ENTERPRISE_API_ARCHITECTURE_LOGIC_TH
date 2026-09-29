FROM python:3.11-slim

WORKDIR /app

# Install runtime deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true

# Copy app
COPY app /app/app
COPY service /app/service

EXPOSE 8080

ENV RESEARCH_OS_PORT=8080

CMD ["python", "app/main.py"]
