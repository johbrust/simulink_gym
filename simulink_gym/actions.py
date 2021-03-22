from .observations import Observation

empty_observation = Observation('empty')


class Action:

    def __init__(self, name, linked_observation: Observation = None, increment=0):
        self._name = name
        self.linked_observation = linked_observation
        self.increment = increment

    def __str__(self):
        return self._name


class Actions:

    def __init__(self, *args: Action):
        self._actions = list()
        for action in args:
            self._actions.append(action)
        self.current_action_index = None
        self._set_values = {}
        for action in self._actions:
            if action.linked_observation and not str(action.linked_observation) in self._set_values:
                set_value_dict = {'set_value': action.linked_observation.current_value,
                                  'lower_sat': action.linked_observation.lower_saturation,
                                  'upper_sat': action.linked_observation.upper_saturation}
                self._set_values[str(action.linked_observation)] = set_value_dict

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

    def update_set_value(self, set_value_key: str, new_value):
        if new_value < self._set_values[set_value_key]['lower_sat']:
            new_value = self._set_values[set_value_key]['lower_sat']
        elif new_value > self._set_values[set_value_key]['upper_sat']:
            new_value = self._set_values[set_value_key]['upper_sat']
        self._set_values[set_value_key]['set_value'] = new_value

    @property
    def set_values(self):
        return [self._set_values[key]['set_value'] for key in self._set_values]

    def __len__(self):
        return len(self._actions)
