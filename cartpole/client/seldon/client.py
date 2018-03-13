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
        self.session = None
        self.token = None

    def http_log(self, r, *args, **kwargs):
        LOG.debug(r)
        LOG.debug(r.url)
        LOG.debug('RESPONSE HEADERS << %s', r.headers)
        LOG.debug('RESPONSE BODY << %s', r.text)

    def get_session(self, pool_connections=10, poll_maxsize=100):
        if not self.session:
            LOG.debug("Getting http session ...")
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=poll_maxsize)
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)
            session.headers = {'Authorization': 'Bearer {}'.format(self.get_token())}
            session.hooks['response'].append(self.http_log)
            self.session = session
        return self.session

    def get_token(self):
        if not self.token:
            LOG.debug("Getting auth token ...")
            payload = {'grant_type': 'client_credentials'}
            response = requests.post(
                    "http://{}:8080/oauth/token".format(self.host),
                    auth=HTTPBasicAuth('oauth-key', 'oauth-secret'),
                    data=payload)
            self.token = response.json()["access_token"]
        return self.token

    def rest_request(self, state):
        payload = {"data": {"names": ["a"], "tensor": {"shape": [1, 4], "values": np.array(state[0]).tolist()}}}
        response = self.get_session().post(
            "http://{}:8080/api/v0.1/predictions".format(self.host),
            json=payload)
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
        metadata = [('oauth_token', self.get_token())]
        response = stub.Predict(request=request, metadata=metadata)
        return request, response

    def rest_feedback(self, request, response, reward, done):
        if done:
            reward = 0
        feedback = {"request": request, "response": response, "reward": reward}
        LOG.debug("Sending feedback...")
        ret = self.get_session().post("http://{}:8080/api/v0.1/feedback".format(self.host), json=feedback)
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
        metadata = [('oauth_token', self.get_token())]
        response = stub.SendFeedback(request=request, metadata=metadata)
        return response

    def switch_branch_router(self, state, pref_branch=0, iters=100, routing_name='eg-router', show_plot=True):
        routes_history = []
        for _ in range(iters):
            request, response = self.rest_request(state)
            route = response.get("meta").get("routing").get(routing_name)
            LOG.debug('Route: %s', route)
            if route == pref_branch:
                self.rest_feedback(request, response, reward=1, done=False)
            else:
                self.rest_feedback(request, response, reward=0, done=False)
            routes_history.append(route)

        if show_plot:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(15, 6))
            ax = plt.scatter(range(len(routes_history)), routes_history)
            ax.axes.xaxis.set_label_text("Incoming Requests over Time")
            ax.axes.yaxis.set_label_text("Selected Branch")
            plt.yticks([0, 1, 2])
            _ = plt.title("Branch Chosen for Incoming Requests")