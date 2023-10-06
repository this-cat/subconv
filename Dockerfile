FROM debian:10

RUN apt update -y && \
    apt install python -y && \
    wget -O /tmp/requirements.txt https://... && \
    wget -O /usr/local/bin/subconv.py https://... && \
    pip install -r /tmp/requirements.txt

CMD ["python", "/usr/local/bin/subconv.py"]
