FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv
RUN uv sync --frozen

COPY app/ app/
COPY main.py .
COPY weights/ weights/
COPY data/label_encoder.json data/

EXPOSE 8090

CMD ["python", "-m", "app.main"]