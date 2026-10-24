FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt \
    && useradd --system --uid 10001 --create-home agent
COPY src/ ./src/
COPY --from=frontend /frontend/dist/ ./web/dist/
USER agent
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn src.api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
