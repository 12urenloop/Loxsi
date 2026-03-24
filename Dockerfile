FROM python:3.14.3-alpine3.23

# Install uv.
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=yes

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN pip3 install --no-cache-dir uv && \
    uv sync --frozen --no-cache && \
    pip3 uninstall uv --yes

