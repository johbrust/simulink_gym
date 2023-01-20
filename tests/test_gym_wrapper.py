import sys

sys.path.insert(0, "..")
from examples.envs import CartPoleSimulink  # noqa: E402
from simulink_gym import logger  # noqa: E402

logger.setLevel(10)


def test_gym_wrapper():
    env = CartPoleSimulink(stop_time=30, model_debug=False)
    state = env.reset()
    assert state is not None
    assert env.simulation_time == 0

    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    assert not done
    state, reward, done, info = env.step(action)
    assert env.simulation_time > 0

    env.stop_simulation()
    env.close()
    assert env.recv_socket.connection is None
    assert env.send_socket.connection is None
