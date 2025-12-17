FROM python:3.10-slim-buster

RUN groupadd -g 10001 -r pyapp && useradd --no-log-init -r -u 10001 -g pyapp pyapp

COPY ./cmd/pyapp /cmd/pyapp
COPY /cmd/local.env.docker /cmd/local.env
COPY /cmd/requirements.txt.freeze /cmd/
WORKDIR /cmd

RUN true \
    && pip install --upgrade pip \
    && pip install --no-cache-dir  -r requirements.txt.freeze

USER pyapp

ENTRYPOINT ["python3", "-m", "pyapp"]
