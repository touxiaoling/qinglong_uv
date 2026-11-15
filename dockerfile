FROM node:24.22.3-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
RUN npm run build

FROM lscr.io/linuxserver/ffmpeg:9.0.2-cli-ls89

WORKDIR /code

ENV TZ=Asia/Shanghai

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        wget \
        ca-certificates \
        openssh-client && \
    rm -rf /var/lib/apt/lists/* && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    /ffmpegwrapper.sh -version

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

COPY .python-version pyproject.toml uv.lock README.md ./
COPY ./qinglong ./qinglong
COPY --from=frontend /build/qinglong/web_dist ./qinglong/web_dist
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy UV_PYTHON_INSTALL_DIR=/opt/panel-python uv sync --locked --no-dev --no-editable

ENV UV_CACHE_DIR=/code/data/.cache/uv
ENV UV_PYTHON_INSTALL_DIR=/code/data/.cache/python

ENTRYPOINT ["/code/.venv/bin/python", "-m", "qinglong"]
