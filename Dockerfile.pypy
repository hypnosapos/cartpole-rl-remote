ARG PY_ORG="pypy"
ARG PY_VERSION="3-6"
ARG DIST="slim-stretch"

FROM ${PY_ORG}:${PY_VERSION}-${DIST}
COPY requirements.txt .
RUN apt-get update && apt-get install cmake build-essential --yes && pypy3 -m ensurepip
RUN pip install -r requirements.txt

FROM ${PY_ORG}:${PY_VERSION}-${DIST}
COPY --from=0 /root/.cache /root/.cache

RUN apt-get update && apt install curl cmake --yes

WORKDIR /cartpole-rl-remote

ADD . .
RUN pypy3 -m ensurepip && pip install .
RUN rm -rf /root/.cache