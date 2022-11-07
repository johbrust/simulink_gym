import os
import argparse
import string
import random
from envs import CartPoleSimulink
from stable_baselines3 import DQN
from pathlib import Path
from datetime import datetime

def main():
    """Training the DQN agent.

    Run 'python train_dqn_agent.py -h' for function documentation.
    """
    # Parameters:
    parser = define_parser()
    args = parser.parse_args()
    # General:
    save_policy = args.save_policy
    verbose = args.verbose
    wb = args.wandb
    benchmark = args.benchmark
    # Training:
    total_timesteps = args.total_timesteps
    # DQN:
    batch_size = args.batch_size
    epsilon_0 = args.epsilon_0
    train_freq = args.train_freq
    discount_factor = args.gamma
    learning_rate = args.learning_rate
    epsilon_min = args.eps_min
    exploration_fraction = args.exploration_fraction
    buffer_size = args.buffer_size
    tau = args.tau
    update_interval = args.update_interval
    gradient_steps = args.gradient_steps
    min_exp = args.min_exp
    
    timestamp = datetime.now().strftime('%Y%m%d.%H%M%S')
    random_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    run_id = f"{timestamp}-{random_tag}"

    # Define path for logs:
    log_dir = Path(args.log_dir).resolve().joinpath(run_id)
    # Create directory if not already existing:
    log_dir.mkdir(parents=True, exist_ok=True)

    config = {"total_timesteps": total_timesteps,
              "batch_size": batch_size,
              "buffer_size": buffer_size,
              "min_exp": min_exp,
              "target_update_interval": update_interval,
              "exploration_fraction": exploration_fraction,
              "epsilon_0": epsilon_0,
              "epsilon_min": epsilon_min,
              "train_freq": (train_freq, "episode"),
              "discount_factor": discount_factor,
              "learning_rate": learning_rate,
              "tau": tau,
              "gradient_steps": gradient_steps,
              }

    # Weights & Biases (https://wandb.ai):
    if wb:
        import wandb
        from wandb.integration.sb3 import WandbCallback
        os.environ['WANDB_DISABLE_GIT'] = 'True'
        run = wandb.init(project='simulink_gym',
                         group='simulink_cartpole_env' if not benchmark else 'gym_cartpole_env',
                         job_type='examples',
                         tags=['DQN'],
                         sync_tensorboard=True,
                         config=config,
                         dir=log_dir,
                         save_code=False,
                         id=run_id
                         )
        callback = WandbCallback()
    else:
        callback = None

    # Create training environment:
    if not benchmark:
        env = CartPoleSimulink()
    else:
        import gym
        env = gym.make("CartPole-v1")

    # Create learning agent:
    agent = DQN("MlpPolicy",
                env,
                buffer_size=config["buffer_size"],
                batch_size=config["batch_size"],
                gamma=config["discount_factor"],
                learning_rate=config["learning_rate"],
                learning_starts=config["min_exp"],
                target_update_interval=config["target_update_interval"],
                exploration_fraction=config["exploration_fraction"],
                exploration_initial_eps=config["epsilon_0"],
                exploration_final_eps=config["epsilon_min"],
                train_freq=config["train_freq"],
                tau=config["tau"],
                gradient_steps=config["gradient_steps"],
                verbose=verbose,
                tensorboard_log=str(log_dir)
                )

    # Train agent:
    agent.learn(total_timesteps=config["total_timesteps"], log_interval=4, callback=callback, progress_bar=True)

    # Save policy:
    if save_policy:
        policy = agent.policy
        policy.save(f"{log_dir}/learned_policy")

    env.close()

    if wb:
        run.finish()

def define_parser():
    """Define the function interface."""
    parser = argparse.ArgumentParser(description='Training a DQN agent on the Simulink Cartpole environment',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-b', '--batch_size', metavar='batch_size', type=int, default=32,
                        help='Minibatch size for gradient update')
    parser.add_argument('-B', '--benchmark', action='store_true',
                        help='Flag for training in gym implementation CartPole-v1')
    parser.add_argument('-d', '--log_dir', metavar='log_dir', type=str, default='./logs',
                        help='Path for logs and optional saved policy')
    parser.add_argument('-e', '--epsilon_0', metavar='epsilon_0', type=float, default=1.0,
                        help='Initial epsilon value')
    parser.add_argument('-f', '--train_freq', metavar='train_freq', type=int, default=1,
                        help='Times to train per episode')
    parser.add_argument('-g', '--gamma', metavar='discount_factor', type=float, default=0.99,
                        help='Discount factor of the Bellman update')
    parser.add_argument('-l', '--learning_rate', metavar='learning_rate', type=float, default=1e-4,
                        help='Learning rate')
    parser.add_argument('-m', '--eps_min', metavar='epsilon_min', type=float, default=0.05,
                        help='Minimum epsilon value')
    parser.add_argument('-p', '--exploration_fraction', metavar='exploration_fraction', type=float, default=0.1,
                        help='Fraction of entire training period over which the exploration rate is reduced')
    parser.add_argument('-r', '--buffer_size', metavar='buffer_size', type=int, default=10000,
                        help='Size of replay buffer')
    parser.add_argument('-s', '--save_policy', action='store_true',
                        help='Flag for saving the trained policy')
    parser.add_argument('-S', '--gradient_steps', metavar='gradient_steps', type=int, default=1,
                        help='How many gradient steps to do after each rollout')
    parser.add_argument('-t', '--total_timesteps', metavar='total_timesteps', type=int, default=500000,
                        help='Number of total timesteps to train')
    parser.add_argument('-T', '--tau', metavar='tau', type=float, default=1.0,
                        help='Soft update coefficient (Polyak update), 1.0 for hard update')
    parser.add_argument('-u', '--update_interval', metavar='update_interval', type=int, default=5000,
                        help='Timesteps between update of target network')
    parser.add_argument('-v', '--verbose', metavar='verbose', type=int, default=0,
                        help='Verbosity level: 0 for no output, 1 for info messages (such as device or wrappers used), 2 for debug messages')
    parser.add_argument('-w', '--wandb', action='store_true',
                        help='Flag indicating the use of wandb (Weights & Biases)')
    parser.add_argument('-x', '--min_exp', metavar='min_experiences', type=int, default=5000,
                        help='Minimum experiences in buffer to start with training')

    return parser


if __name__ == '__main__':
    main()
