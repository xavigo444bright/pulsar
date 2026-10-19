FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE DISCLAIMER.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .
COPY .env.example ./.env
ENV PULSAR_HOST=0.0.0.0 PULSAR_PORT=8000
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "pulsar.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
