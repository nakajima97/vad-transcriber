FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /api

# PYTHONPATHを設定して絶対インポートを可能にする
ENV PYTHONPATH=/api/src

CMD uv help

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]