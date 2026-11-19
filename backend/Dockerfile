FROM python:3.14-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV TZ=Asia/Shanghai

# 确保系统命令、Python 本地时间和日志都有东八区时区数据。
# 云服务器位于中国大陆，使用阿里云 Debian 镜像避免 deb.debian.org 下载超时。
RUN sed -i \
    -e 's|deb.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' \
    -e 's|deb.debian.org/debian|mirrors.aliyun.com/debian|g' \
    /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=3 update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/


# 先复制依赖文件
COPY pyproject.toml uv.lock ./

# 创建项目虚拟环境并安装依赖
RUN uv sync --frozen --no-dev


# 复制代码
COPY . .


EXPOSE 8000


CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
