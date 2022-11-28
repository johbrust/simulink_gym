# Simulink Gym

A wrapper for using Simulink models as Gym environments

---

This wrapper establishes the [Gym environment interface](https://www.gymlibrary.dev/api/core/) for [Simulink](https://de.mathworks.com/products/simulink.html) models by deriving a `simulink_gym.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/v0.21.0/gym/core.py#L8).

This wrapper uses Gym version 0.21.0 for easy usage with established RL libraries such as [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/index.html) or [rllib](https://www.ray.io/rllib).

> :grey_exclamation: The Gym library currently undergoes breaking changes in the newest versions. Once the RL libraries are switching to the newer Gym interface, this wrapper will also be updated.

## Setup

Installing this package is currently only possible from source, but a distribution through PyPI is planned. Execute the following steps to install Simulink Gym.

```bash
# Clone repository with HTTPS ...
git clone https://github.com/johbrust/simulink_gym.git
# ... or SSH:
git clone git@github.com:johbrust/simulink_gym.git

cd simulink_gym

# If needed, activate some environment here!

pip install .
```

Currently, the usage of this package inside [Poetry](https://python-poetry.org/) or similarly elaborate environment management tools (e.g., [PDM](https://pdm.fming.dev/)) will break due to the dependency on the [MATLAB Engine for Python](#matlab-engine-for-python), which does not conform, i.a., to the versioning defined by PEP 440 as required by Poetry and PDM. This is no issue when using a simpler environment management tool (e.g., `virtualenv`).

The package also provides an [example implementation of the cart pole environment in Simulink](./examples/envs/cartpole_simulink/cartpole_simulink.md). Use `pip install .[examples]` to install the examples as an extra. If you are using [Weights & Biases](https://wandb.ai) for experiment tracking, you can install the `wandb` extra. 

This package is using the [Black code formatter](https://black.readthedocs.io/en/stable/) and [Ruff linter](https://github.com/charliermarsh/ruff) for development. Therefore, the `dev` extra is defining these as dependencies.

For a full installation use `pip install .[dev, examples, wandb]`.

> :grey_exclamation: Don't forget to use quotes if you are using `zsh`: e.g., `pip install ".[examples, wandb]"`

### MATLAB Engine for Python

A MATLAB instance is needed to run the Simulink models. MATLAB provides an installable Python module (`matlab.engine`) locally to interact with a background instance of a locally installed MATLAB. The installation instructions for the MATLAB module can be found [here](https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html).

When using a Python environment you can use the following steps to install the MATLAB Python engine.

```bash
<activate your environment here>
cd <matlab root>/extern/engines/python
sudo $(which python) setup.py install
```

Under Linux, `<matlab root>` usually is `/usr/local/MATLAB/<MATLAB version>`.

In the future, a PyPI package of the MATLAB engine will be available which will make setup easier.

### Simulink Gym Block Library

Shipped with this package comes a [custom Simulink block library](https://de.mathworks.com/help/simulink/libraries.html) for setting up the interface on the model side. Checkout the [respective Readme](./simulink_block_lib/Readme.md) for setup and usage instructions. 

## Preparing the Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared.

How this can be done will be described here soon!

__To Do__:

- [Set up the model](https://www.mathworks.com/help/simulink/slref/setmodelparameter.html)
  - Sample time?
  - [Solver](https://de.mathworks.com/help/simulink/gui/solver.html)?
  - [Block execution order](https://de.mathworks.com/help/simulink/ug/controlling-and-displaying-the-sorted-order.html)
    - add delays or integrators to control the execution order
  - Explain Model Explorer (`CTRL + H`) as a tool for setting up, e.g., the model workspace
- Link to Matlab docs in code where respective Matlab functions are interfaced
- Describe `model_debug` flag

### Communication Interface

Special blocks in a custom block library were prepared for the communication with the Simulink model. They will be described here soon!

__To Do__:

- simulation stepping is controlled by sending data to the simulation
- explain [addition of the simulink block library to the library browser](https://de.mathworks.com/help/simulink/ug/adding-libraries-to-the-library-browser.html)
- Block sample time?
- Block parameters?
- Byte order: Intel x86 is Little Endian, therefore the `TCP/IP Send` block is configured for Little Endian, the `TCP/IP Receive` block receives integer values and, therefore, does not need byte order configuration #TBD: this has to be changed once not only integers are send to the model
- Explain setup of the TCP/IP blocks (In and Out)
  - It is necessary to set the number of input signals. This is not done automatically because it is not unambiguous.

## Preparing the Environment File

How to describe the Simulink environment in Python will be described here soon!

- Setting the action and observation space: The action space is set as for the standard Gym environment. The observation space needs the custom `observations` parameter (TBD add link to line in code), since the observations are linked to certain blocks in the Simulink model. The order in the `observations` declaration has to match the order of the state mux in the model since it also defines the interpretation of the incoming data (which is defined by the mux). #TBD
- Get the correct name of the block parameter not from the mask but from the documentation! E.g., the integrator block has a `Initial condition` parameter in the mask, but the parameter is set by using `InitialCondition` in the `ParamBlock`.

## Running the Simulink Model

### End of Episode

`truncated` and `terminated` flags (historically `done` flag)

An environment returns the `done` flag, when the episode is finished. The Simulink simulation returns an empty TCP/IP message, when the simulation stopped. But this is only sent after the last simulation step (i.e., at time `t_end + 1`). Therefore, if the stepping through the simulation is done in a `while` loop, the return values of the last call of `env.step` (the step returning with `done` set to `true`) are no new values and, therefore, disposable.

## Example Environments

Two different implementations of the classic cart pole environment are provided under [`envs`](./simulink_gym/envs). [One implementation](./simulink_gym/envs/cartpole_simulink.md) uses the basic Simulink blocks, [the other](./simulink_gym/envs/cartpole_simscape.md) is implemented using the [Simscape](https://www.mathworks.com/products/simscape.html) toolbox family.

## Known Issues

The known issues below could not be fixed due to the lack of knowledge about the exact cause. Despite these known issues, there are fixes known to avoid these issues, which are given with each issue.

> :grey_exclamation: If you encounter issues not listed below, please create a new issue or even a pull request if you also already found the fix!

- It sometimes can be observed that after a while two sets of output data are received from the Simulink model when only one action was sent. It is assumed that this is causes by some timing issues of the TCP/IP communication in combination with the update order of the model.

  Fix: All occurrences of this issue could be mitigated by ensuring a certain [block execution order](https://de.mathworks.com/help/simulink/ug/controlling-and-displaying-the-sorted-order.html) of the Simulink model. There are different possibilities to achieve this:
  
  1. Set the priorities of the *TCP/IP In* and *TCP/IP Out* blocks to 1 and 2, respectively. Simulink then tries to come up with a block execution order according to these priorities. Unfortunately, setting these priorities does not guarantee that such a block execution order is possible.
  2. Introduce additional signals in the Simulink model to enforce a certain block execution order. E.g., add a signal of the incoming action to some (dummy) blocks close before the *TCP/IP Out* block.
