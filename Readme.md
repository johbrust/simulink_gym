# Wrapper for using Simulink models as Gym Environments

---

## To Do

- How to define `actions` and `observations`?
- How to implement the `render` method?

---

This wrapper establishes the gym environment interface for Simulink models by deriving a `gym_env_simulink_wrapper.Environment` subclass from [`gym.Env`](https://github.com/openai/gym/blob/master/gym/core.py#L8) as a base class.

The wrapper implements the `step`, `reset`, `render`, `close` and `seed` methods of the interface.

## Preparing the Simulink Model

In order to use a Simulink model with this wrapper the model has to be prepared.

__To Do__:

- [Set up the model](https://www.mathworks.com/help/simulink/slref/setmodelparameter.html)
  - Sample time?
  - Solver?

### TCP/IP Communication

The wrapper communicates with the model via TCP/IP. The _Instrument Control Toolbox_ provides the [`TCP/IP Send`](https://www.mathworks.com/help/instrument/tcpipsend.html) and [`TCP/IP Receive`](https://www.mathworks.com/help/instrument/tcpipreceive.html) blocks for this communication. By specifying the _Priority_ of the blocks, the execution order of the blocks can be controlled. It is necessary that the _TCP/IP Receive_ block is executed before the _TCP/IP Send_ block, because the model receives the action first and then simulates the model and sends the observations back to the wrapper.

__To Do__:

- Block sample time?
- Block parameters?
- Byte order: Intel x86 is Little Endian, therefore the `TCP/IP Send` block is configured for Little Endian, the `TCP/IP Receive` block receives integer values and, therefore, does not need byte order configuration