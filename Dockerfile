# Stage 1 — build the UI bundle
FROM node:20-alpine AS ui-builder
WORKDIR /ui

# Install deps first for layer caching
COPY ui/package.json ui/package-lock.json ./
RUN npm ci

# VITE_API_KEY is baked into the bundle at build time
ARG VITE_API_KEY=""
ENV VITE_API_KEY=$VITE_API_KEY

COPY ui/ ./
RUN npm run build

# Stage 2 — Python runtime that also serves the UI
FROM python:3.11-slim
WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Bring the built UI in as static assets
COPY --from=ui-builder /ui/dist /app/static

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
