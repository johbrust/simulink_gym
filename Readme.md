# Wrapper for using Simulink models as Gym Environments

This wrapper establishes the [gym environment interface](https://www.gymlibrary.dev/api/core/) for [Simulink](https://de.mathworks.com/products/simulink.html) models by deriving a `simulink_gym.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/master/gym/core.py#L8) as a base class.

The wrapper implements the [`step`](https://www.gymlibrary.dev/api/core/#gym.Env.step), [`reset`](https://www.gymlibrary.dev/api/core/#gym.Env.reset), and [`close`](https://www.gymlibrary.dev/api/core/#gym.Env.close) methods of the interface.

Rendering is done by this wrapper since it is environment specific.

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
$HOME/.local/share/virtualenvs/<virtualenv name>/bin/python setup.py install
```

Under Linux, `<matlab root>` usually is `/usr/local/MATLAB/<MATLAB version>`.

Recently, a [MATLAB engine PyPI package](https://pypi.org/project/matlabengine/) has become available, but it requires MATLAB version R2022a. Such a package would be beneficial if it would work with a wider range of installed MATLAB versions. As long as only one version is supported, a manual install of the MATLAB engine seems advantageous.

## Preparing the Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared.

How this can be done will be described here soon!

### Communication Interface

Special blocks in a custom block library were prepared for the communication with the Simulink model. They will be described here soon!

## Preparing the Environment File

- Setting the action and observation space: The action space is set as for the standard gym environment. The observation space needs the custom `observations` parameter (TBD add link to line in code), since the observations are linked to certain blocks in the Simulink model. The order in the `observations` declaration has to match the order of the state mux in the model since it also defines the interpretation of the incoming data (which is defined by the mux). #TBD
- Get the correct name of the block parameter not from the mask but from the documentation! E.g., the integrator block has a `Initial condition` parameter in the mask, but the parameter is set by using `InitialCondition` in the `ParamBlock`.
