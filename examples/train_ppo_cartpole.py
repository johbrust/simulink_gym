import os
import argparse
import string
import random
from envs import CartPoleSimulink
from stable_baselines3 import PPO
from pathlib import Path
from datetime import datetime

def main():
    """Training the PPO agent.

    Run 'python train_ppo_agent.py -h' for function documentation.
    """
    # Parameters:
    parser = define_parser()
    args = parser.parse_args()
    # General:
    save_policy = args.save_policy
    verbose = args.verbose
    wb = args.wandb
    # Training:
    total_timesteps = args.total_timesteps
    # PPO:
    batch_size = args.batch_size
    discount_factor = args.gamma
    learning_rate = args.learning_rate
    num_steps = args.num_steps
    num_epochs = args.num_epochs
    gae_lambda = args.gae_lambda
    
    timestamp = datetime.now().strftime('%Y%m%d.%H%M%S')
    random_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    run_id = f"{timestamp}-{random_tag}"

    # Define path for logs:
    log_dir = Path(args.log_dir).resolve().joinpath(run_id)
    # Create directory if not already existing:
    log_dir.mkdir(parents=True, exist_ok=True)

    config = {"total_timesteps": total_timesteps,
              "batch_size": batch_size,
              "discount_factor": discount_factor,
              "learning_rate": learning_rate,
              "num_steps": num_steps,
              "num_epochs": num_epochs,
              "gae_lambda": gae_lambda,
              }

    # Weights & Biases (https://wandb.ai):
    if wb:
        import wandb
        from wandb.integration.sb3 import WandbCallback
        os.environ['WANDB_DISABLE_GIT'] = 'True'
        run = wandb.init(project='simulink_gym',
                         group='simulink_cartpole_env',
                         job_type='examples',
                         tags=['PPO'],
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
    env = CartPoleSimulink(stop_time=20)

    # Create learning agent:
    agent = PPO("MlpPolicy",
                env,
                batch_size=config["batch_size"],
                gamma=config["discount_factor"],
                learning_rate=config["learning_rate"],
                n_steps=config["num_steps"],
                n_epochs=config["num_epochs"],
                gae_lambda=config["gae_lambda"],
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
    parser = argparse.ArgumentParser(description='Training a PPO agent on the Simulink Cartpole environment',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-a', '--gae_lambda', metavar='gae_lambda', type=float, default=0.95,
                        help='Factor for trade-off of bias vs variance for Generalized Advantage Estimator')
    parser.add_argument('-b', '--batch_size', metavar='batch_size', type=int, default=64,
                        help='Minibatch size for gradient update')
    parser.add_argument('-d', '--log_dir', metavar='log_dir', type=str, default='./logs',
                        help='Path for logs and optional saved policy')
    parser.add_argument('-e', '--num_epochs', metavar='num_epochs', type=int, default=10,
                        help='Number of epochs when optimizing the surrogate loss')
    parser.add_argument('-g', '--gamma', metavar='discount_factor', type=float, default=0.99,
                        help='Discount factor of the Bellman update')
    parser.add_argument('-l', '--learning_rate', metavar='learning_rate', type=float, default=3e-4,
                        help='Learning rate')
    parser.add_argument('-n', '--num_steps', metavar='num_steps', type=int, default=2048,
                        help='The number of steps to run for each environment per update (rollout length)')
    parser.add_argument('-s', '--save_policy', action='store_true',
                        help='Flag for saving the trained policy')
    parser.add_argument('-t', '--total_timesteps', metavar='total_timesteps', type=int, default=300000,
                        help='Number of total timesteps to train')
    parser.add_argument('-v', '--verbose', metavar='verbose', type=int, default=0,
                        help='Verbosity level: 0 for no output, 1 for info messages (such as device or wrappers used), 2 for debug messages')
    parser.add_argument('-w', '--wandb', action='store_true',
                        help='Flag indicating the use of wandb (Weights & Biases)')

    return parser


if __name__ == '__main__':
    main()
