#!/usr/bin/env python
import requests
import grpc
import json
import numpy as np

from requests.auth import HTTPBasicAuth
from proto import prediction_pb2
from proto import prediction_pb2_grpc

MINIKUBE_IP = "35.226.173.5"


def get_token():
    payload = {'grant_type': 'client_credentials'}
    response = requests.post(
        "http://" + MINIKUBE_IP + ":8080/oauth/token",
        auth=HTTPBasicAuth('oauth-key', 'oauth-secret'),
        data=payload)
    token = response.json()["access_token"]
    return token


TOKEN = get_token()


def rest_request(state):
    headers = {'Authorization': 'Bearer ' + TOKEN}
    payload = {"data": {"names": ["a"], "tensor": {"shape": [1, 4], "values": np.array(state[0]).tolist()}}}
    response = requests.post(
        "http://" + MINIKUBE_IP + ":8080/api/v0.1/predictions",
        headers=headers,
        json=payload)
    return payload, json.loads(response.text)


def grpc_request(state):
    datadef = prediction_pb2.DefaultData(
        names=["names"],
        tensor=prediction_pb2.Tensor(
            shape=[1, 4],
            values=np.array(state[0]).tolist()
        )
    )
    request = prediction_pb2.SeldonMessage(data=datadef)
    channel = grpc.insecure_channel(MINIKUBE_IP + ":5000")
    stub = prediction_pb2_grpc.SeldonStub(channel)
    metadata = [('oauth_token', TOKEN)]
    response = stub.Predict(request=request, metadata=metadata)
    return response


def send_feedback_rest(request, response, reward):
    headers = {"Authorization": "Bearer " + TOKEN}
    feedback = {"request": request, "response": response, "reward": reward}
    ret = requests.post("http://{}:8080/api/v0.1/feedback".format(MINIKUBE_IP), headers=headers, json=feedback)
    return ret.text
