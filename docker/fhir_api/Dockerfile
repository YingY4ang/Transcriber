FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install flask flask-cors boto3

# Copy API server
COPY ec2_api.py .

# Expose port
EXPOSE 5000

# Run Flask app
CMD ["python", "ec2_api.py"]
