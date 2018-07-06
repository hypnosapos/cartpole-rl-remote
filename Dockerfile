ARG PY_VERSION="3.5"
ARG DIST="slim"

FROM python:${PY_VERSION}-${DIST}
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:${PY_VERSION}-${DIST}
COPY --from=0 /root/.cache /root/.cache

RUN apt update --yes && apt install curl --yes

WORKDIR /cartpole-rl-remote

ADD . .
RUN pip install .
RUN rm -rf /root/.cache