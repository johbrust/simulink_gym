# Wrapper for using Simulink models as Gym Environments

This wrapper establishes the [gym environment interface](https://www.gymlibrary.dev/api/core/) for [Simulink](https://de.mathworks.com/products/simulink.html) models by deriving a `simulink_gym.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/master/gym/core.py#L8) as a base class.

The wrapper implements the [`step`](https://www.gymlibrary.dev/api/core/#gym.Env.step), [`reset`](https://www.gymlibrary.dev/api/core/#gym.Env.reset), and [`close`](https://www.gymlibrary.dev/api/core/#gym.Env.close) methods of the interface.

Rendering is not done by this wrapper since it is environment specific.

## Gym Interface

The Gym project is currently revisited with breaking changes in the interface. *Simulink Gym* already uses the updated interface, but Reinforcement Learning algorithm libraries, like [Stable Baselines 3](https://github.com/DLR-RM/stable-baselines3) or [rllib](https://www.ray.io/rllib), have not been updated yet. Using *Simulink Gym* in combination with learning algorithms from such libraries, therefore, is not possible until the ongoing efforts of these libraries to update to the newest interface version is completed.

## Setup

Installing this package is currently only possible from source:

```bash
# Clone repository with HTTPS:
git clone https://github.com/johbrust/simulink_gym.git
# or SSH:
git clone git@github.com:johbrust/simulink_gym.git

cd simulink_gym

# If needed, activate some environment here!

pip install -e .
```

Currently, the usage of this package inside [Poetry](https://python-poetry.org/) or similarly elaborate environment management tool (e.g., [PDM](https://pdm.fming.dev/)) will break due to the dependency on the [MATLAB Engine for Python](#matlab-engine-for-python), which does not conform, i.a., to the versioning defined by PEP 440 as required by Poetry and PDM. This is no issue when using a simpler environment management tool (e.g., `virtualenv`).

Providing a package, e.g., installable via PyPI is a future goal.

### MATLAB Engine for Python

A MATLAB instance is needed to run the Simulink models. MATLAB provides an installable Python module (`matlab.engine`) locally to interact with a background instance of a locally installed MATLAB. The installation instructions for the MATLAB module can be found [here](https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html).

When, e.g., `virtualenv` is used, run the installation with the full path of the respective python interpreter, e.g.:

```bash
cd <matlab root>/extern/engines/python
sudo <path to virtual env>/<virtualenv name>/bin/python setup.py install
```

Under Linux, `<matlab root>` usually is `/usr/local/MATLAB/<MATLAB version>`.

Recently, a [MATLAB engine PyPI package](https://pypi.org/project/matlabengine/) has become available, but it requires MATLAB version R2022a. Such a package would be beneficial if it would work with a wider range of installed MATLAB versions. As long as only one version is supported, a manual install of the MATLAB engine seems advantageous.

## Preparing the Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared.

How this can be done will be described here soon!

__To Do__:

- [Set up the model](https://www.mathworks.com/help/simulink/slref/setmodelparameter.html)
  - Sample time?
  - Solver?
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

- Setting the action and observation space: The action space is set as for the standard gym environment. The observation space needs the custom `observations` parameter (TBD add link to line in code), since the observations are linked to certain blocks in the Simulink model. The order in the `observations` declaration has to match the order of the state mux in the model since it also defines the interpretation of the incoming data (which is defined by the mux). #TBD
- Get the correct name of the block parameter not from the mask but from the documentation! E.g., the integrator block has a `Initial condition` parameter in the mask, but the parameter is set by using `InitialCondition` in the `ParamBlock`.

## Running the Simulink Model

### End of Episode

`truncated` and `terminated` flags (historically `done` flag)

An environment returns the `done` flag, when the episode is finished. The Simulink simulation returns an empty TCP/IP message, when the simulation stopped. But this is only sent after the last simulation step (i.e., at time `t_end + 1`). Therefore, if the stepping through the simulation is done in a `while` loop, the return values of the last call of `env.step` (the step returning with `done` set to `true`) are no new values and, therefore, disposable.

## Example Environments

Two different implementations of the classic cart pole environment are provided under [`envs`](./simulink_gym/envs). [One implementation](./simulink_gym/envs/cartpole_simulink.md) uses the basic Simulink blocks, [the other](./simulink_gym/envs/cartpole_simscape.md) is implemented using the [Simscape](https://www.mathworks.com/products/simscape.html) toolbox family.
