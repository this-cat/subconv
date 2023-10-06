FROM debian:10

COPY requirements.txt /tmp/requirements.txt
COPY subconv.py /usr/local/bin/subconv.py

RUN apt update -y && \
    apt install python -y && \
    apt install python-pip -y && \
    pip install -r /tmp/requirements.txt &&\
    apt clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["python", "/usr/local/bin/subconv.py"]
