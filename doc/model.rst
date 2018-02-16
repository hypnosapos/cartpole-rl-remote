Reinforcement Learning Agent
============================

The project is divided basically in three parts. Cartpole neural network model, QLearning algorithm and application runner.

Model
-----

Multilayer neural network with two hidden layers. Four dimension array as input containing information about stick position.

code-block::
    model = Sequential()
    model.add(Dense(12, activation='relu', input_dim=4))
    model.add(Dense(12, activation='relu'))
    model.add(Dense(2))
    model.compile(Adam(lr=0.001), 'mse')

QLearning Algorithm
-------------------

Select action:
This is the most import part in this project because of remote grpc call is done. In run mode we send a request to Seldon model deployed while agent is playing.

code-block::
        request, response = seldon_client.grpc_request(state)

code-block::
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

Record:
Memory used to store actions and reward to train neural network in batch process.
Size = 2000

Replay:
QLearning Algorithm implementation. We estimate the Q value using the deep neural network and manage the train process by minibatches.
.. image:: ./img/rl.png
   :alt: Reinforcement Learning


Application Runner
------------------
Main process where the most important part is the seldom feedback implementation where the process send back information about the accuracy of the model prediction.


