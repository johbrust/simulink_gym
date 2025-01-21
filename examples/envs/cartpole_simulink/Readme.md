# Simulink Implementation of the Cart Pole Environment

Implementation of the classic cart pole environment using standard Simulink blocks to model the underlying differential equations of the [dynamics](https://coneural.org/florian/papers/05_cart_pole.pdf).

The environment is modelled in `cartpole_simulink.slx` and wrapped in [`cartpole_simulink.py`](./cartpole_simulink.py).

## Solver

Like the [Gymnasium implementation](https://github.com/Farama-Foundation/Gymnasium/blob/08a28d38dab17cb4656cd73517bf894575ce6f1a/gymnasium/envs/classic_control/cartpole.py), this model uses a fixed step-size of 0.02 s and the Euler integration method (*ode1 (Euler)* solver).

## Action and Observation Space

Like the Gymnasium implementation, this environment has a discrete action space with two actions allowing the agent to push the cart in both directions with a force of 10 N.

The observation space consists of the cart's position and velocity as well as the pole's angle and its angular velocity.

## Model parameters

The dynamics of the system are defined by the physical properties of the cart and pole. These parameters are defined in the [model workspace](https://www.mathworks.com/help/simulink/ug/using-model-workspaces.html). The step size of the solver is also setup as a workspace variable. The following table lists all workspace variables and their default value. In the case of the initial cart position and pole angle the default values will be overwritten by the Simulink Gym wrapper.

| Property                                  | Variable Name | Default Value             | Unit |
| ----------------------------------------- | ------------- | ------------------------- | ---- |
| earth's gravity                           | `g`           | 9.80665                   | m/s² |
| length of pole (distance of joint to CoM) | `length_pole` | 0.5                       | m    |
| mass of pole                              | `mass_pole`   | 0.1                       | kg   |
| mass of cart                              | `mass_cart`   | 1                         | kg   |
| initial cart position                     | `x_0`         | 0                         | m    |
| initial pole angle                        | `theta_0`     | $\mathcal{U}_{[-12, 12]}$ | °    |
| step size                                 | `step_size`   | 0.02                      | s    |

## Try it out!

Check out the [notebook](./cartpole_simulink.ipynb) to play around with the environment.

## Training RL Agents

Also included in this directory are two example scripts for training a DQN ([`train_dqn_cartpole.py`](./train_dqn_cartpole.py)) and a PPO ([`train_ppo_cartpole.py`](./train_ppo_cartpole.py)) agent on the cart pole environment implemented in Simulink. The scripts use [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/v2.4.1/) for the RL algorithms. For additional information on the usage of the example scripts just call them with the `-h` flag (`python train_<algorithm>_cartpole.py -h`).
