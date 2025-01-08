# Use UV's official Python image which comes with UV pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set up the application directory
WORKDIR /app

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1

# Use copy instead of linking since we're using mounted volumes
ENV UV_LINK_MODE=copy

ENV PYTHONPATH=/app

# First, install only the project dependencies using the lockfile
# This layer can be cached effectively
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then add the rest of the project source code and install it
# This separation allows for better layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Add the virtual environment's bin directory to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint
ENTRYPOINT []
