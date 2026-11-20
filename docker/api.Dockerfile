FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY scorecaster/ scorecaster/

RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "scorecaster.api.main:create_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
