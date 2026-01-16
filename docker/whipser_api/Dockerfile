FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    openai \
    boto3 \
    requests \
    librosa \
    soundfile \
    numpy \
    reportlab

# Copy project modules
COPY ../../shared /app/shared
COPY ../../analysis /app/analysis
COPY ../../storage /app/storage
COPY ../../pdf /app/pdf

# Copy worker script
COPY worker_openai.py .

CMD ["python", "worker_openai.py"]
