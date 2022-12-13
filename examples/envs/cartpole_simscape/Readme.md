# Simscape Implementation of the Cart Pole Environment

Implementation of the classic cart pole environment using [Simscape](https://www.mathworks.com/products/simscape.html) blocks.

The environment is modelled in `cartpole_simscape.slx` and wrapped in [`cartpole_simscape.py`](./cartpole_simscape.py).

## Solver

Like the [Gym implementation](https://github.com/openai/gym/blob/v0.21.0/gym/envs/classic_control/cartpole.py), this model uses a fixed step-size of 0.02 s and the Euler integration method (*ode1 (Euler)* solver).

## Action and Observation Space

Like the Gym implementation, this environment has a discrete action space with two actions allowing the agent to push the cart in both directions with a force of 10 N.

The observation space consists of the cart's position and velocity as well as the pole's angle and its angular velocity.

## Model parameters

The dynamics of the system are defined by the physical properties of the cart and pole. These parameters are defined in the [model workspace](https://www.mathworks.com/help/simulink/ug/using-model-workspaces.html). The step size of the solver is also setup as a workspace variable. The following table lists all workspace variables and their default value. In the case of the initial cart position/velocity and pole angle/angular velocity the default values will be overwritten by the Simulink Gym wrapper.

| Property                                  | Variable Name | Default Value | Unit  |
| ----------------------------------------- | ------------- | ------------- | ----- |
| earth's gravity                           | `g`           | 9.80665       | m/s²  |
| length of pole (distance of joint to CoM) | `length_pole` | 0.5           | m     |
| mass of pole                              | `mass_pole`   | 0.1           | kg    |
| mass of cart                              | `mass_cart`   | 1             | kg    |
| initial cart position                     | `x_0`         | 0             | m     |
| initial cart velocity                     | `v_0`         | 0             | m/s   |
| initial pole angle                        | `theta_0`     | 0             | rad   |
| initial angular velocity of the pole      | `omega_0`     | 0             | rad/s |
| step size                                 | `step_size`   | 0.02          | s     |

## Try it out!

Check out the [notebook](./cartpole_simscape.ipynb) to play around with the environment.
