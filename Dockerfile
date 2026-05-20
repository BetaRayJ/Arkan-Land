FROM python:3.11-slim

WORKDIR /app

# Install deps first (layer-cached)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source
COPY backend/ ./backend/
COPY index.html ./

# Portfolio data persists via a named volume mounted at runtime
VOLUME ["/app/backend"]

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
