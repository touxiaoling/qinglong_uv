FROM linuxserver/ffmpeg:latest
COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

WORKDIR /code

RUN sed -i 's/ports.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt update; apt install -y --no-install-recommends curl libjemalloc2 git wget ca-certificates ;rm -rf /var/lib/apt/lists/*

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

ENV TZ=Asia/Shanghai
ENV UV_CACHE_DIR=/code/data/.cache/uv
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY pyproject.toml uv.lock ./
COPY ./qinglong ./qinglong
RUN mkdir -p /code/data/.cache
RUN /ffmpegwrapper.sh -version
ENTRYPOINT ["uv" , "run","--no-dev" ,"uvicorn", "qinglong.main:app", "--host", "0.0.0.0", "--port", "80" ,"--loop","uvloop","--http","httptools"]