from observations import Observation

empty_observation = Observation('empty')


class Action:

    def __init__(self, name, linked_observation: Observation = empty_observation, direction=0):
        self.name = name
        self.linked_observation = linked_observation
        self.direction = direction

    def did_saturate_further(self):
        return self.linked_observation.did_saturate_further(self.direction)


class Actions:

    def __init__(self, *args: Action):
        self.actions = list()
        for action in args:
            self.actions.append(action)
        self.current_action_index = None

    def update_current_action_index(self, index):
        self.current_action_index = index

    def get_action(self, index):
        return self.actions[index]

    def current_action(self):
        return self.actions[self.current_action_index]

    def current_action_name(self):
        return self.actions[self.current_action_index].name

    def __len__(self):
        return len(self.actions)
