# Simulink Gym

*A wrapper for using Simulink models as Gym environments*

This wrapper establishes the [Gym environment interface](https://www.gymlibrary.dev/api/core/) for [Simulink](https://de.mathworks.com/products/simulink.html) models by deriving a [`simulink_gym.SimulinkEnv`](./simulink_gym/environment.py#L13) subclass from [`gym.Env`](https://github.com/openai/gym/blob/v0.21.0/gym/core.py#L8).

This wrapper uses Gym version 0.21.0 for easy usage with established RL libraries such as [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/index.html) or [rllib](https://www.ray.io/rllib).

> [!NOTE]
> The Gym library currently undergoes breaking changes in the newest versions. Once the RL libraries are switching to the newer Gym interface, [this wrapper will also be updated](https://github.com/johbrust/simulink_gym/issues/11).

## How it works

This section gives a broad description of the functionality under the hood. For detailed instructions on how to wrap a simulink model, see [below](#how-to-wrap-a-simulink-model).

The wrapper is based on adding TCP/IP communication between a Simulink model running in a background instance of MATLAB Simulink and a Python wrapper class implementing the Gym interface.

The TCP/IP communication is established via respective Simulink blocks and matching [communication sockets](./simulink_gym/utils/comm_socket.py). The Simulink blocks are provided by the [Simulink block library](./simulink_block_lib/) included in this project. The input block receives the input action, which triggers the simulation of the next time step. At the end of this time step, the output block sends the output data (i.e., the observation) back to the wrapper. Check out the [Readme](./simulink_block_lib/Readme.md) of the Simulink block library for more information.

The wrapper provides the necessary methods to create this derived environment without the user having to implement the TCP/IP communication. Similar to the usual Gym environment implementations, the user only has to define the action and observation/state space as well as the individual `reset` and `step` methods.

> [!NOTE]
> Initializing an environment object takes a few seconds due to the starting of MATLAB in the background and the creation of the simulation object ([`SimulationInput` object](https://de.mathworks.com/help/simulink/slref/simulink.simulationinput-class.html)). Also, the first `reset(...)` takes substantially longer than any consecutive `reset(...)`.

## Setup

This package is controlling Simulink models in MATLAB from Python through the [MATLAB engine for Python](https://de.mathworks.com/help/matlab/matlab_external/get-started-with-matlab-engine-for-python.html), which is a Python package provided by MATLAB. Until MATLAB version `R2022b`, this Python package was not available for simple installation via `pip` from PyPI. Instead, it had to be installed manually [from source](https://de.mathworks.com/help/matlab/matlab_external/python-setup-script-to-install-matlab-engine-api.html) and, therefore, it could not be added as a dependency for automatic installation (e.g., in `requirements.txt` or `pyproject.toml`).

Since most MATLAB installations probably aren't updated to versions >= `R2022b` yet, the MATLAB engine for Python is not added as a dependency to the [pyproject.toml](./pyproject.toml) of this package. Instead, the setup process for **Simulink Gym** requires an extra step for the installation of the MATLAB engine for Python. Execute the following steps to install Simulink Gym.

```shell
# Install Simulink Gym:
pip install git+https://github.com/johbrust/simulink_gym.git

# The following step for installing the MATLAB engine depends on your MATLAB version.
# MATLAB version < R2022b:
cd <matlab root>/extern/engines/python
sudo $(which python) setup.py install
# MATLAB version >= R2022b:
pip install matlabengine
```

Under Linux, `<matlab root>` usually is `/usr/local/MATLAB/<MATLAB version>`. The macro `$(which python)` ensures the usage of the right Python executable in case you are using (and already activated) a Python environment. The `sudo` is required since MATLAB is installed with `root`.

> [!WARNING]
> For MATLAB versions < `R2022b`, the usage of this package inside [Poetry](https://python-poetry.org/) or similarly elaborate environment management tools (e.g., [PDM](https://pdm.fming.dev/)) will break due to the dependency on the [MATLAB Engine for Python](#matlab-engine-for-python), which versioning does not conform to PEP 440 as required by Poetry and PDM. This is no issue when using a simpler environment management tool (e.g., `virtualenv`).

### Extras

This package also provides [example implementations using the Simulink wrapper](./examples/Readme.md) (including example training scripts for DQN and PPO agents for the [cart pole implementation in Simulink](./examples/envs/cartpole_simulink/Readme.md)). To try them out, it is recommended to clone the repository and install from source by executing `pip install .[examples]` to install the extra packages required by the examples.

This package is using the [Black code formatter](https://black.readthedocs.io/en/stable/) and [Ruff linter](https://github.com/charliermarsh/ruff) for development. Therefore, the `dev` extra is defining these as dependencies.

For a full installation from source use `pip install .[all]`.

> [!IMPORTANT]
> Don't forget to use quotes if you are using `zsh`: e.g., `pip install ".[all]"`

### Simulink Gym Block Library

Shipped with this package comes a [custom Simulink block library](https://de.mathworks.com/help/simulink/libraries.html) for setting up the interface on the model side. Checkout the [respective Readme](./simulink_block_lib/Readme.md) for more information about setup and usage. 

## How to Wrap a Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared accordingly. This includes preparing the Simulink model file (`.slx` file) to be wrapped and writing a wrapper class for the model with [`SimulinkEnv`](./simulink_gym/environment.py#L13) as its base class.

### Prepare the Simulink Model File

For the communication with the wrapper the TCP/IP blocks provided by the [Simulink Gym block library](#simulink-gym-block-library) have to be added and setup [accordingly](./simulink_block_lib/Readme.md).

Setting parameter values of the model through the wrapper can be done in two different ways, which has consequences for the model creation process. The first possibility is to directly set block parameter values through [`SimulinkEnv.set_block_parameter(...)`](./simulink_gym/environment.py#L286). The block parameters can be set to any value and changed later through the wrapper. A second way would be to define a variable in the [model workspace](https://de.mathworks.com/help/simulink/ug/using-model-workspaces.html) and set the block parameter to this variable. The workspace variable then can be changed for changing the block parameter through [`SimulinkEnv.set_workspace_variable(...)`](./simulink_gym/environment.py#L261).

Model workspace variables are the recommended way to make general block settings, like step sizes, available for the wrapper.

> [!NOTE]
> For creating a model workspace variable, you can use the [Model Explorer](https://de.mathworks.com/help/simulink/slref/modelexplorer.html), which can be opened with `CTRL + H` from the Simulink model editor.

Check [Model Debugging](#model-debugging) for information on how to debug the Simulink model during the model creation process.

### Preparing the Environment File

The second part of the environment definition is to create an environment class derived from the [`SimulinkEnv`](./simulink_gym/environment.py#L13) base class.

This derived class has to define the action and observation space as well as the `reset(...)` and `step(...)` methods specific for the environment.

#### Action and Observation Space

While the action space is defined simply by, e.g., `self.action_space = gym.spaces.Discrete(2)`, the observation space definition needs additional information about the corresponding blocks or workspace variables in the Simulink model. This is due to the fact that the wrapper needs to be able to set these values, e.g., while resetting the environment. For this, the wrapper provides the [`Observation`](./simulink_gym/observations.py#L7) and [`Observations`](./simulink_gym/observations.py#L88) classes. For an example definition of an observation space, check the cart pole example implementations in [Simulink](./examples/envs/cartpole_simulink/cartpole_simulink.py#L64) and [Simscape](./examples/envs/cartpole_simscape/cartpole_simscape.py#L61) which set initial values directly through the block parameter values (Simulink implementation) or through workspace variables (Simscape implementation).

The `Observations` object of the environment is a list-like object with the order of its `Observation` entries matching the concatenation order of the observation signals in the Simulink model (e.g., through the [mux block](https://de.mathworks.com/help/simulink/slref/mux.html)).

Since observation values are reset after an episode, information about the corresponding blocks or workspace variable have to be provided. For block parameters, the wrapper can access these through the path of the block value which is given by the template `<model name>/<subsystem 0>/.../<subsystem n>/<block name>/<parameter name>` for a block buried in `n` subsystems.

> [!WARNING]
> Block parameter names don't always match the description in the block mask! Therefore, get the correct parameter name from the Simulink documentation and not from the mask!

#### Reset and Step Methods

The provided [`_reset()`](./simulink_gym/environment.py#L123) method is to be called in the `reset()` method of the derived environment class. This takes care of resetting the Simulink simulation. The derived class therefore only has to implement environment specific reset behavior like resampling of the initial state or only parts of it. Again, see the [cart pole example](./examples/envs/cartpole_simulink/cartpole_simulink.py#L108) for an example usage.

The basic stepping functionality is provided by the wrapper's [`sim_step(...)` method](./simulink_gym/environment.py#L160) which should be called in the `step(...)` method of the derived environment definition class (see, e.g., `step(...)` method of the [cart pole example](./examples/envs/cartpole_simulink/cartpole_simulink.py#L120)).

## Running the Simulink Model

After everything is set up just use the defined environment like any other Gym environment. See the [notebook of the cart pole Simulink implementation](./examples/envs/cartpole_simulink/cartpole_simulink.ipynb) for an example usage.

### Model Debugging

For debugging the Simulink model in combination with the wrapper, the [`model_debug`](./simulink_gym/environment.py#L24) flag is provided. Set this to `True` in the `super().__init__(...)` call in your derived environment class and start your environment. This tells the wrapper to not start a thread with a MATLAB instance running the simulation in the background. Instead, you have to manually start the simulation model in the Simulink GUI once the environment object is instantiated and resetting initially (executing `state = env.reset()` will cause the program to wait for the connection). You can then access the Simulink model's internal signals through the Simulink GUI for easy debugging.

The best way to stop the simulation is by executing `env.stop_simulation()`.

### End of Episode

An environment complying with the Gym interface returns the `done` flag when the episode is finished. The Simulink simulation returns an empty TCP/IP message after the simulation stopped (i.e., when the simulation has run for the defined duration). But this is only sent after the last simulation step (i.e., at time `t_end + 1`). Therefore, the termination of the simulation can only be detected one time step after the terminal state was already reached. Keep this in mind, when using the data from the environment, since the terminal state will be present two times! As a workaround, simply drop the last data point from the trajectory!

## Known Issues

The known issues below could not be fixed due to the lack of knowledge about the exact cause. Despite these known issues, there are fixes known to avoid these issues, which are given with each issue.

> [!IMPORTANT]
> If you encounter issues not listed below, please create a new issue or even a pull request if you also already found the fix!

- It sometimes can be observed that after a while two sets of output data are received from the Simulink model when only one action was sent. It is assumed that this is causes by some timing issues of the TCP/IP communication in combination with the update order of the model.

  Fix: All occurrences of this issue could be mitigated by ensuring a certain [block execution order](https://de.mathworks.com/help/simulink/ug/controlling-and-displaying-the-sorted-order.html) of the Simulink model. There are different possibilities to achieve this:
  
  1. Set the priorities of the *TCP/IP In* and *TCP/IP Out* blocks to 1 and 2, respectively. Simulink then tries to come up with a block execution order according to these priorities. Unfortunately, setting these priorities does not guarantee that such a block execution order is possible.
  2. Introduce additional signals in the Simulink model to enforce a certain block execution order. E.g., add a signal of the incoming action to some (dummy) blocks close before the *TCP/IP Out* block.
