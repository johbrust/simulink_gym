# Custom Simulink Block Library for Simulink Gym

This Simulink block library provides the blocks necessary for communication and control of the Simulink models.

## Content

The block library consists of two blocks defining the communication of the model and the wrapper over TCP/IP.

### TCP/IP In Block

This block receives the desired input signal(s). The received data comes in the form of a vector according to the action space definition. Check the [spaces definition of the Gymnasium library](https://gymnasium.farama.org/api/spaces/) for compatible spaces.

Depicted below is the block composition inside of the block. The TCP/IP receive block receives the data, which is split afterwards into the input data and a stop signal, which can be used to stop the simulation prematurely.

![TCP-IP-In](https://user-images.githubusercontent.com/16197185/204263287-b422802f-4d65-4540-ae40-8b3e0cd03759.png)

The input block comes with a mask for specifying all necessary parameters:

- **Port**: TCP/IP port to communicate over
- **Number of input signals**: Size of input data, e.g., size of action space
- **Sample time**: Sample time setting for the Simulink blocks

![TCP-IP-In](https://user-images.githubusercontent.com/16197185/204263662-4458b099-97db-4c9b-b5b0-51e752f2e160.png)

### TCP/IP Out Block

This block sends the desired data back to the wrapper. The data is expected to be in vector form, which, e.g., can be accomplished by [muxing](https://www.mathworks.com/help/simulink/slref/mux.html) all desired signals into the `state` input port.

The block is composed of a function block packing the input data and the simulation time stamp and the TCP/IP send block.

![TCP-IP-Out](https://user-images.githubusercontent.com/16197185/204263337-873a8a0d-c125-4176-ab79-739f96e2428f.png)

The output block also provides a mask to set all necessary parameters:

- **Port**: TCP/IP port to communicate over
- **Sample time**: Sample time setting for the Simulink blocks

![TCP-IP-Out](https://user-images.githubusercontent.com/16197185/204263691-8f63a277-4650-4473-b06c-8f99c43fd82f.png)

## Setup

When simulating a Simulink model through the Python interface provided by this wrapper the block library is added automatically to the path of the MATLAB session running in the background.

To make it also available in the Simulink Library Browser as *Simulink Gym* simply add the [`simulink_block_lib` directory](./) to the MATLAB path.

## Usage

After [making the block available to Simulink](#setup) just add the input and output block to your Simulink model and specify the parameters as needed.

Check the [Simulink implementation of the cart pole environment](../examples/envs/cartpole_simulink/) for an example usage.
