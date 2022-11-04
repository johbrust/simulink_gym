# Simulink Implementation of the Cart Pole Environment

This implementation of the classic cart pole environment uses the standard Simulink blocks to model the underlying differential equations of the dynamics (see [here](https://coneural.org/florian/papers/05_cart_pole.pdf)).

## Model parameters

The dynamics of the system are defined by the following physical properties of the cart and pole.

| Property                                  | Variable Name | Default Value               |
| ----------------------------------------- | ------------- | --------------------------- |
| earth's gravity                           | `g`           | 9.80665 m/s²                |
| length of pole (distance of joint to CoM) | `length_pole` | 0.5 m                       |
| mass of pole                              | `mass_pole`   | 0.1 kg                      |
| mass of cart                              | `mass_cart`   | 1 kg                        |
| initial cart position                     | `x_0`         | 0 m                         |
| initial pole angle                        | `theta_0`     | random value in [-12°, 12°] |

The model parameters are saved in the [model workspace](https://www.mathworks.com/help/simulink/ug/using-model-workspaces.html).
