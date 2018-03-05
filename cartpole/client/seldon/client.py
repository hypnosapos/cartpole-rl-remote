# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import requests
import grpc
import json
import numpy as np
import logging

from requests.auth import HTTPBasicAuth
from cartpole.client.seldon.proto import prediction_pb2
from cartpole.client.seldon.proto import prediction_pb2_grpc


LOG = logging.getLogger(__name__)


class SeldonClient(object):

    def __init__(self, host):
        self.host = host
        self._token = None

    @property
    def token(self):
        if not self._token:
            LOG.debug("Getting auth token ...")
            payload = {'grant_type': 'client_credentials'}
            response = requests.post(
                "http://{}:8080/oauth/token".format(self.host),
                auth=HTTPBasicAuth('oauth-key', 'oauth-secret'),
                data=payload)
            self._token = response.json()["access_token"]
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    def rest_request(self, state):
        headers = {'Authorization': 'Bearer {}'.format(self.token)}
        payload = {"data": {"names": ["a"], "tensor": {"shape": [1, 4], "values": np.array(state[0]).tolist()}}}
        LOG.debug("Launching REST request with:\nHeaders:\n%s\nPayload:\n%s", headers, payload)
        response = requests.post(
            "http://{}:8080/api/v0.1/predictions".format(self.host),
            headers=headers,
            json=payload)
        LOG.debug("Response URL:\n%s\nResponse headers:\n%s\nResponse contents:\n%s",
                  response.url, response.headers, response.text)
        return payload, json.loads(response.text)

    def grpc_request(self, state):
        datadef = prediction_pb2.DefaultData(
            names=["names"],
            tensor=prediction_pb2.Tensor(
                shape=[1, 4],
                values=np.array(state[0]).tolist()
            )
        )
        request = prediction_pb2.SeldonMessage(data=datadef)
        channel = grpc.insecure_channel("{}:5000".format(self.host))
        stub = prediction_pb2_grpc.SeldonStub(channel)
        metadata = [('oauth_token', self.token)]
        response = stub.Predict(request=request, metadata=metadata)
        return request, response

    def rest_feedback(self, request, response, reward, done):
        if done:
            reward = 0
        headers = {"Authorization": "Bearer {}".format(self.token)}
        feedback = {"request": request, "response": response, "reward": reward}
        LOG.debug("Sending feedback...")
        ret = requests.post("http://{}:8080/api/v0.1/feedback".format(self.host), headers=headers, json=feedback)
        return ret.text

    def grpc_feedback(self, request, response, reward, done):
        if done:
            reward = 0
        request = prediction_pb2.Feedback(
                request=request,
                response=response,
                reward=float(reward)
        )
        channel = grpc.insecure_channel("{}:5000".format(self.host))
        stub = prediction_pb2_grpc.SeldonStub(channel)
        metadata = [('oauth_token', self.token)]
        response = stub.SendFeedback(request=request, metadata=metadata)
        return response
