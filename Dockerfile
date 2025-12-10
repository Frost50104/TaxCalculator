# Base image
FROM python:3.11-slim

# Ensure stdout/stderr are unbuffered for timely logs
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install dependencies first (leverage Docker layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose runtime port (informational)
EXPOSE 8000

# Run the FastAPI app with multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
