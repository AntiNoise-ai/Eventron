FROM python:3.11-slim

WORKDIR /app

# System dependencies for weasyprint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 && \
    rm -rf /var/lib/apt/lists/*

# Step 1: Install dependencies only (cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN mkdir -p app agents tools channels && \
    touch app/__init__.py agents/__init__.py tools/__init__.py channels/__init__.py && \
    pip install --no-cache-dir . && \
    rm -rf app agents tools channels

# Step 2: Copy actual source code
COPY . .

# Step 3: Re-install in editable mode so app/agents/tools/channels are on sys.path
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
