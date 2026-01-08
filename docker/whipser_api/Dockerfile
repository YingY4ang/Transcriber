FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir openai boto3 requests

COPY worker_openai.py .

CMD ["python", "worker_openai.py"]
