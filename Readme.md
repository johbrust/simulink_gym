# Wrapper for using Simulink models as Gym Environments

[[_TOC_]]

---

## To Do

- How to define `actions` and `observations`?
- How to implement the `render` method?

---

This wrapper establishes the gym environment interface for Simulink models by deriving a `simulink_gym.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/master/gym/core.py#L8) as a base class.

The wrapper implements the `step`, `reset`, `render`, `close` and `seed` methods of the interface.

## Setup

``` bash
conda activate <env>
cd simulink_gym
python setup.py develop
```

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