import tensorflow as tf
import numpy as np
import random
from simulink_gym import Environment, logger

# Set the logging level:
logger.set_level(logger.DEBUG)


class DQNAgent:
    """Implementation of the DQN training algorithm.

    This class implements the Deep Q-Network algorithm (https://www.nature.com/articles/nature14236).
    """
    def __init__(self,
                 env: Environment,
                 num_states,
                 num_actions,
                 gamma,
                 learning_rate,
                 buffer_size=10000,
                 batch_size=32,
                 tau=0.001,
                 train_step=1,
                 copy_step=25,
                 optimizer='Adam',
                 update_method='smooth'):
        if update_method == 'smooth':
            self.update_method = 'smooth'  # Weight update method
        else:
            self.update_method = 'step'
        self.batch_size = batch_size
        self.gamma = gamma
        self.env = env
        self.num_states = num_states
        self.num_actions = num_actions
        self.learning_rate = learning_rate
        self.tau = tau  # Factor for smooth weight update
        self.copy_step = copy_step  # Copy step for step weight update
        self.train_step = train_step
        self.max_experiences = buffer_size
        self.optimizer = optimizer
        self.experience = list()

        # Initialize networks:
        self.model = self.create_model()
        self.target_model = self.create_model()

    def create_model(self):
        """Function for setting up of a neural network model.

        The network consists of 2 fully connected hidden layers with ReLU activation functions.
        """
        # Connect the model layers:
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Dense(24, input_dim=self.num_states, activation='relu'))
        model.add(tf.keras.layers.Dense(48, activation="relu"))
        model.add(tf.keras.layers.Dense(24, activation='relu'))
        model.add(tf.keras.layers.Dense(self.num_actions))

        # Set the learning optimizer:
        if self.optimizer == 'Adam':
            optimizer = tf.optimizers.Adam(self.learning_rate)
        else:
            raise ValueError('Specified optimizer not available.')

        # Create model object:
        model.compile(optimizer=optimizer,
                      loss='mean_squared_error',
                      metrics=['mean_squared_error'])

        return model

    def train(self):
        """Training of the neural network.

        This method implements the Bellman update for the DQN algorithm.
        """
        if (len(self.experience) - 1) < self.batch_size:
            # Not enough experiences gathered for a training. Skip training.
            return -1
        logger.debug('Training model')
        # Select random batch from experience. Ignore the last added entry, because it is not yet clear if it was a
        # terminal state. This is due to the behaviour of the Simulink environment, which is detected to be finished,
        # when an empty TCP/IP message was received from it. Therefore, only after the next step it is clear if it was a
        # terminal state.
        samples = random.sample(self.experience[0:-1], self.batch_size)
        states = np.empty([self.batch_size, self.num_states])
        target_values = np.empty([self.batch_size, self.num_actions])
        counter = 0
        # Iterate through samples:
        for sample in samples:
            state, action, reward, next_state, done = sample
            states[counter] = state
            # Get current action values of current state:
            target_values[counter] = self.target_model.predict(state)
            if done:
                # For terminal states:
                target_values[counter][action] = reward
            else:
                # Get max action value of next state:
                value_target = max(self.target_model.predict(next_state)[0])
                # Calculate target value:
                target_values[counter][action] = reward + self.gamma * value_target
            counter += 1

        # Perform neural network update:
        history = self.model.fit(states, target_values, verbose=0)

        return np.mean(history.history['mean_squared_error'])

    def get_action(self, observation, epsilon):
        """Get action for state given the observations."""
        legal_mask = self.env.actions.mask  # Valid/Legal action mask
        if np.random.random() <= epsilon:
            # With epsilon chance perform random action:
            legal_actions = np.array(range(self.num_actions))[legal_mask]
            action = int(np.random.choice(legal_actions))
            logger.debug('Choosing random action {}'.format(action))
        else:
            # Get optimal action:
            predicted_values = self.model.predict(observation)[0]
            masked_values = [value if mask else float('-inf') for (value, mask) in zip(predicted_values, legal_mask)]
            action = int(np.argmax(masked_values))
            logger.debug('Choosing action {} from values {}'.format(action, masked_values))
        return action

    def add_experience(self, new_experience):
        """Add experience (state, action, reward, next_state, done) to replay buffer."""
        self.experience.append(new_experience)
        # Discard oldest experiences:
        while len(self.experience) >= self.max_experiences:
            self.experience.pop(0)

    def smooth_update_target(self):
        """Smooth update of the target network.

        The target network weights are updated with the update rate tau.
        """
        weights = self.model.get_weights()
        target_weights = self.target_model.get_weights()
        for i in range(len(target_weights)):
            target_weights[i] = self.tau * weights[i] + (1 - self.tau) * target_weights[i]
        self.target_model.set_weights(target_weights)

    def copy_weights(self):
        """Copy network weights to the target network."""
        self.target_model.set_weights(self.model.get_weights())

    def run_episode(self, env: Environment, epsilon):
        """Run one episode of the DQN training.

        This performs one whole simulation run of the environment and trains the network with the collected data.
        """
        cum_reward = 0  # Cumulative reward
        sim_step_counter = 0  # Simulation step counter
        done = False

        # Reset the environment to the start state:
        state = env.reset()
        # Preallocate the list for the losses:
        losses = list()

        # Run the simulation until done:
        while not done:
            sim_step_counter += 1
            logger.debug('Simulation step {}'.format(sim_step_counter))

            # Get the next action and step the environment:
            action = self.get_action(state, epsilon)
            previous_state = state
            state, reward, done, _ = env.step(action)
            if done:
                # Ignore values of the last step (see above for reasons), but set last experience entry to 'done'.
                self.experience[-1][-1] = done
                continue
            # Sum the reward:
            cum_reward += reward
            # Add the experience to the replay buffer:
            new_experience = [previous_state, action, reward, state, done]
            self.add_experience(new_experience)

            # Train the network:
            if sim_step_counter % self.train_step == 0:
                loss = self.train()
                if loss >= 0:
                    losses.append(loss)
                    # Smooth target network weight update (only of update_method=='smooth'):
                    if self.update_method == 'smooth':
                        self.smooth_update_target()
            # Full target network weight update (only of update_method=='step'):
            if self.update_method == 'step' and sim_step_counter % self.copy_step == 0:
                self.copy_weights()

        return cum_reward, np.mean(losses)
