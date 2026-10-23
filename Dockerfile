FROM python:3.13-slim
WORKDIR /app

# Headless OpenCV does not require the graphical dependencies from opencv-python.
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt \
    && useradd --system --uid 10001 --create-home agent

COPY src/ ./src/
USER agent
EXPOSE 8000
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
