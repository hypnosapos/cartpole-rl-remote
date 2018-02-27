#!/usr/bin/env python
import requests
from build.proto import prediction_pb2
from build.proto import prediction_pb2_grpc
import grpc
from requests.auth import HTTPBasicAuth

KUBERNETES_IP = "35.192.141.146"


def get_token():
    payload = {'grant_type': 'client_credentials'}
    response = requests.post(
        "http://{}:8080/oauth/token".format(KUBERNETES_IP),
        auth=HTTPBasicAuth('oauth-key', 'oauth-secret'),
        data=payload)
    token = response.json()["access_token"]
    return token


def rest_request():
    token = get_token()
    headers = {'Authorization': 'Bearer ' + token}
    payload = {"data": {"names": ["names"], "tensor": {"shape": [1, 4], "values": [0, 0, 1, 1]}}}
    response = requests.post(
        "http://{}:8080/api/v0.1/predictions".format(KUBERNETES_IP),
        headers=headers,
        json=payload)
    print(response.text)


def grpc_request():
    token = get_token()
    datadef = prediction_pb2.DefaultData(
        names=["names"],
        tensor=prediction_pb2.Tensor(
            shape=[1, 4],
            values=[0., 0., 1.0, 1.0]
        )
    )
    request = prediction_pb2.SeldonMessage(data=datadef)
    channel = grpc.insecure_channel(KUBERNETES_IP + ":5000")
    stub = prediction_pb2_grpc.SeldonStub(channel)
    metadata = [('oauth_token', token)]
    response = stub.Predict(request=request, metadata=metadata)
    print(response)
