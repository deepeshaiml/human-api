FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_MODE=demo
WORKDIR /app
COPY backend/requirements.lock /app/backend/requirements.lock
RUN pip install --no-cache-dir -r /app/backend/requirements.lock
COPY backend /app/backend
COPY data /app/data
COPY frontend/dist /app/frontend/dist
ENV PYTHONPATH=/app/backend DATABASE_URL=postgresql+psycopg://human_api:human_api@db:5432/human_api
EXPOSE 8000
CMD ["uvicorn", "human_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
