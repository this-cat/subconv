FROM debian:10

COPY requirements.txt /tmp/requirements.txt
COPY subconv.py /usr/local/bin/subconv.py

RUN apt update -y && \
    apt install -y python3 python3-pip && \
    python3 -m pip install -r /tmp/requirements.txt && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["python3", "/usr/local/bin/subconv.py"]
