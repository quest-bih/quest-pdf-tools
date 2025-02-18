# Use Python 3.13 as base image for better compatibility
FROM python:3.13-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy environment and requirements files
COPY .env requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for models and uploads
RUN mkdir -p models uploads

# Load ports from .env file and expose them
ARG FASTAPI_PORT
ARG GRADIO_PORT
ARG DEPLOY_MODE
ENV FASTAPI_PORT=${FASTAPI_PORT:-8000}
ENV GRADIO_PORT=${GRADIO_PORT:-7860}
ENV DEPLOY_MODE=${DEPLOY_MODE:-"full"}
EXPOSE $FASTAPI_PORT $GRADIO_PORT

# Use run.py as the entrypoint with shell form for variable interpolation
CMD python run.py --mode $DEPLOY_MODE
