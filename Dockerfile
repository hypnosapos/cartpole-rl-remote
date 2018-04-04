FROM python:3.6-jessie as python-reqs
COPY requirements.txt .
RUN pip install -U pip &&\
    pip install -r requirements.txt

FROM python:3.6-jessie
COPY --from=python-reqs /root/.cache /root/.cache

RUN mkdir /cartpole

ADD . /cartpole

RUN pip install -U pip &&\
    pip install /cartpole &&\
    rm -rf /root/.cache
