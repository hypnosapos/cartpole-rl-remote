# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import requests
import grpc
import json
import numpy as np
import logging

from cartpole.metrics import get_visdom_conn

from requests.auth import HTTPBasicAuth
from cartpole.client.seldon.proto import prediction_pb2
from cartpole.client.seldon.proto import prediction_pb2_grpc


class SeldonClient(object):

    def __init__(self, host):
        self.host = host
        self.session = None
        self.token = None
        self.log = logging.getLogger(__name__)

    def http_log(self, r, *args, **kwargs):
        self.log.debug(r)
        self.log.debug(r.url)
        self.log.debug('RESPONSE HEADERS << %s', r.headers)
        self.log.debug('RESPONSE BODY << %s', r.text)

    def get_session(self, pool_connections=10, poll_maxsize=100, max_retries=3):
        if not self.session:
            self.log.debug("Getting http session ...")
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=poll_maxsize,
                max_retries= max_retries
            )
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)
            session.headers = {'Authorization': 'Bearer {}'.format(self.get_token())}
            session.hooks['response'].append(self.http_log)
            self.session = session
        return self.session

    def get_token(self):
        if not self.token:
            self.log.debug("Getting auth token ...")
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
        self.log.debug("GRPC Request: %s", request)
        self.log.debug("GRPC Response: %s", response)
        return request, response

    def rest_feedback(self, request, response, reward, done):
        if done:
            reward = 0
        feedback = {"request": request, "response": response, "reward": reward}
        self.log.debug("Sending feedback...")
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
        self.log.debug("GRPC Feedback Request: %s", request)
        self.log.debug("GRPC Feedback Response: %s", response)
        return response

    def force_branch_router(self, state, pref_branch=0, iters=100, routing_name='eg-router', vis_config={}):

        routes_history = []
        feedback_history = []
        vis_routes_win = None
        vis_feedback_win = None

        for i in range(iters):
            request, response = self.rest_request(state)
            route = response.get("meta").get("routing").get(routing_name)
            reward = 1 if route == pref_branch else 0
            print('\n Iter num. : %s  -- Route: %s -- Reward: %s' % (i, route, reward))
            self.rest_feedback(request, response, reward=reward, done=False)
            routes_history.append((i, route,))
            feedback_history.append((i, reward,))
            if vis_config:
                if i == 0:
                    vis = get_visdom_conn(**vis_config)
                    vis_routes_win = vis.scatter(
                        np.array([[i, route]]),
                        opts=dict(
                            title="Route selected (pref: {})".format(pref_branch),
                            xlabels='Req.',
                            ylabel='Route'))
                    vis_feedback_win = vis.scatter(
                        np.array([[i, route]]),
                        opts=dict(
                            title="Feedback",
                            xlabels='Req.',
                            ylabel='Reward'))
                elif vis and i >= 0:
                    vis.scatter(
                        np.array([[i, route]]),
                        win=vis_routes_win,
                        update='append')
                    vis.scatter(
                        np.array([[i, reward]]),
                        win=vis_feedback_win,
                        update='append')
            routes_history.append((i, route,))
            feedback_history.append((i, reward,))
