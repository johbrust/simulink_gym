from .observations import Observation

empty_observation = Observation('empty')


class Action:

    def __init__(self, name, linked_observation: Observation = Observation('empty'), direction=0):
        self._name = name
        self.linked_observation = linked_observation
        self.direction = direction

    def did_saturate_further(self):
        return self.linked_observation.did_saturate_further(self.direction)

    def __str__(self):
        return self._name


class Actions:

    def __init__(self, *args: Action):
        self._actions = list()
        for action in args:
            self._actions.append(action)
        self.current_action_index = None

    def update_current_action_index(self, action_idx):
        if 0 <= action_idx < len(self._actions):
            self.current_action_index = action_idx
        else:
            raise ValueError('Action index not in valid range')

    @property
    def action_names(self):
        return [str(action) for action in self._actions]

    def current_action(self):
        return self._actions[self.current_action_index]

    def current_action_name(self):
        return str(self._actions[self.current_action_index])

    def __len__(self):
        return len(self._actions)
