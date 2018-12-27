ARG PY_VERSION="3.5"
ARG DIST="slim-stretch"

FROM python:${PY_VERSION}-${DIST}
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:${PY_VERSION}-${DIST}
COPY --from=0 /root/.cache /root/.cache

RUN apt-get update && apt-get install curl cmake --yes

WORKDIR /cartpole-rl-remote

ADD . .
RUN pip install .
RUN rm -rf /root/.cache