FROM node:24-bookworm-slim AS frontend
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/index.html web/tsconfig*.json web/vite.config.ts ./
COPY web/src ./src
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.lock /app/backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock
COPY backend/app /app/backend/app
COPY scripts/serve.py /app/scripts/serve.py
COPY --from=frontend /build/web/dist /app/web/dist
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend DATA_DIR=/var/data
EXPOSE 8000
CMD ["python", "scripts/serve.py"]
