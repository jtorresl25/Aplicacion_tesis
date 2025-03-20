# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

EXPOSE 8080

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir && \
    rm -rf /root/.cache/pip

# Install pytorch
# RUN pip install torch torchvision torchaudio

# Install production dependencies.
RUN pip install -r requirements.txt


CMD streamlit run --server.port 8080 --server.enableCORS false app.py