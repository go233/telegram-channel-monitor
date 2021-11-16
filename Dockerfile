FROM python:alpine3.14

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

RUN mkdir -p /app
WORKDIR /app

ADD pip.cn.conf /root/.config/pip/pip.conf
COPY requirements.txt .

COPY main.py .
RUN python -m pip install --upgrade pip
# 安装支持
RUN pip install -r requirements.txt

CMD ["python", "/app/main.py"]