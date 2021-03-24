FROM python:3.9-slim-buster

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
RUN sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
RUN apt-get update && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt
COPY requirements.txt /opt/requirements.txt
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && rm -r /root/.cache
COPY . /opt

ENTRYPOINT [ "/opt/docker-entrypoint.sh" ]
