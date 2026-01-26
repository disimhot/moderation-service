FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy app code
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

# Expose port
EXPOSE 8000

# Run the app
CMD ["python", "-m", "app.main"]
