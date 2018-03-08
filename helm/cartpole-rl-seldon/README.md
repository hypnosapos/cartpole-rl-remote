# Cartpole RL Remote

Deploy a cartpole-rl-remote as seldon deployment

## Prerequisites Details

* Kubernetes 1.6+
* SeldonDeployment resources

## Chart Details
This chart will do the following:

* Deploy a cartpole reinforcement learning remote agent as seldon deployment

## Installing the Chart

To install the chart with the release name `cartpole-rl-remote`:

```bash
$ helm install --name cartpole hypnosapos/cartpole-rl-remote
```

## Configuration

The following tables lists the configurable parameters of the artifactory chart and their default values.

|         Parameter         |           Description             |        Default    |
|---------------------------|-----------------------------------|-------------------|
| `project`       | Project name | `Cartpole RL Remote Agent` |
| `name`          | Name of deployment  |  `keras-cartpole`       |
| `oauth_key`     | OAuth key           | `oauth_key`   |
| `oauth_secret`  | OAuth Secret        | `oauth_secret`          |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.