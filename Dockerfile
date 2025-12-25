FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install  -r requirements.txt

# Copy application
COPY dummy_agent.py .
COPY lambda_handler.py .

# Set Python path
ENV PYTHONPATH=/app

# Default command starts the Lexia-compatible API server with streaming
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

