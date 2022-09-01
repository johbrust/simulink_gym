# Wrapper for using Simulink models as Gym Environments

## To Do

- How to define `actions` and `observations`?
- How to implement the `render` method?

---

This wrapper establishes the gym environment interface for Simulink models by deriving a `simulink_gym.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/master/gym/core.py#L8) as a base class.

The wrapper implements the `step`, `reset`, `render`, `close` and `seed` methods of the interface.

## Setup

Installing the package is currently only possible from source:

```bash
# Clone repository with HTTPS:
git clone https://github.com/johbrust/simulink_gym.git
# or SSH:
git clone git@github.com:johbrust/simulink_gym.git

cd simulink_gym

# If needed, activate some environment here!

pip install -e .
```

Currently, the usage of this package inside a [Poetry](https://python-poetry.org/) or similarly elaborate environment management tool (e.g., [PDM](https://pdm.fming.dev/)) will break due to the dependency on the [MATLAB Engine for Python](#matlab-engine-for-python), which does not conform, i.a., to the versioning defined by PEP 440 as required by Poetry and PDM. This is no issue when using a simpler environment management tool (e.g., `virtualenv`).

### MATLAB Engine for Python

A MATLAB instance is needed to run the Simulink models. MATLAB provides an installable Python module (`matlab.engine`) locally to interact with a background instance of a locally installed MATLAB. The installation instructions for the MATLAB module can be found [here](https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html).

When, e.g., `virtualenv` is used, run the installation with the full path of the respective python interpreter, e.g.:

```bash
cd <matlab root>/extern/engines/python
$HOME/.local/share/virtualenvs/<virtualenv name>/bin/python setup.py install
```

Under Linux `<matlab root>` usually is `/usr/local/MATLAB/<MATLAB version>`.

Recently, a [MATLAB engine PyPI package](https://pypi.org/project/matlabengine/) has become available, but it requires MATLAB version R2022a. Such a package would be beneficial if it would work with a wider range of installed MATLAB versions. As long as only one version is supported, a manual install of the MATLAB engine seems advantageous.

## Preparing the Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared.

__To Do__:

- [Set up the model](https://www.mathworks.com/help/simulink/slref/setmodelparameter.html)
  - Sample time?
  - Solver?

### TCP/IP Communication

The wrapper communicates with the model via TCP/IP. The _Instrument Control Toolbox_ provides the [`TCP/IP Send`](https://www.mathworks.com/help/instrument/tcpipsend.html) and [`TCP/IP Receive`](https://www.mathworks.com/help/instrument/tcpipreceive.html) blocks for this communication. By specifying the _Priority_ of the blocks, the execution order of the blocks can be controlled. It is necessary that the _TCP/IP Send_ block is executed before the _TCP/IP Receive_ block, because the initial observation is received before any simulation is done.

__To Do__:

- Block sample time?
- Block parameters?
- Byte order: Intel x86 is Little Endian, therefore the `TCP/IP Send` block is configured for Little Endian, the `TCP/IP Receive` block receives integer values and, therefore, does not need byte order configuration

## Running the Simulink Model

### `done` Flag

An environment returns the `done` flag, when the episode is finished. The Simulink simulation returns an empty TCP/IP message, when the simulation stopped. But this is only sent after the last simulation step (i.e., at time `t_end + 1`). Therefore, if the stepping through the simulation is done in a `while` loop, the return values of the last call of `env.step` (the step returning with `done` set to `true`) are no new values and, therefore, disposable.

## Example Environments

Two different implementations of the classic cart pole environment are provided under [`envs`](./simulink_gym/envs). [One implementation](./simulink_gym/envs/cartpole_simulink.md) uses the basic Simulink blocks, [the other](./simulink_gym/envs/cartpole_simscape.md) is implemented using the [Simscape](https://www.mathworks.com/products/simscape.html) toolbox family.
