FROM linuxserver/ffmpeg:latest

WORKDIR /code

ENV TZ=Asia/Shanghai

RUN sed -i 's/ports.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    apt update && \
    apt install -y --no-install-recommends \
        curl \
        libjemalloc2 \
        git \
        wget \
        ca-certificates \
        openssh-client && \
    rm -rf /var/lib/apt/lists/* && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    /ffmpegwrapper.sh -version

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

ENV UV_CACHE_DIR=/code/data/.cache/uv
ENV UV_PYTHON_INSTALL_DIR=/code/data/.cache/python

RUN mkdir -p /code/data/.cache
COPY pyproject.toml uv.lock ./
COPY ./qinglong ./qinglong
ENTRYPOINT ["uv" , "run","--no-dev", "-m", "qinglong"]
