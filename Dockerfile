FROM python:3.12-slim
WORKDIR /app
COPY cloud/requirements.txt cloud/requirements.txt
RUN pip install --no-cache-dir -r cloud/requirements.txt
COPY cloud cloud
COPY dashboard dashboard
ENV CH_DB_PATH=/data/cattlehealth.db \
    CH_DASHBOARD_DIR=/app/dashboard
VOLUME /data
WORKDIR /app/cloud
EXPOSE 8000
CMD ["uvicorn", "cattlehealth.api:app", "--host", "0.0.0.0", "--port", "8000"]
