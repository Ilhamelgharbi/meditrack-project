# FROM python:3.11-slim

# # Prevent Python from writing pyc files
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# # System dependencies (for ML, image processing, etc.)
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libglib2.0-0 \
#     libsm6 \
#     libxext6 \
#     libxrender-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --upgrade pip \
#     && pip install -r requirements.txt

# # Copy app
# COPY app ./app

# EXPOSE 8000

# CMD ["python", "app.main.py"]
FROM python:3.13-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

# Copy the application into the container.
COPY --chown=user . /app

# Install the application dependencies.
WORKDIR /app
ENV UV_HTTP_TIMEOUT=6000
# ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

RUN uv sync --locked

EXPOSE 8000

# Create directories with proper permissions
RUN mkdir -p /app/app/agent/uploads /app/app/agent/vectorstore && chmod -R 755 /app/app/agent/uploads /app/app/agent/vectorstore && chown -R user:user /app/app/agent/uploads /app/app/agent/vectorstore  # updated

# Run the application.
CMD ["uv","run", "python", "main.py"]