import numpy as np
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step as ts
from tf_agents.specs import array_spec


class PipsEnv(py_environment.PyEnvironment):
    def __init__(self):
        super().__init__()

        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32, minimum=0, maximum=2314
        )

        # EXAMPLE: replace with your real observation shape
        self._observation_spec = array_spec.ArraySpec(
            shape=(4,), dtype=np.float32
        )

        self._state = np.zeros(self._observation_spec.shape, dtype=np.float32)
        self._episode_ended = False

    
    def action_spec(self):  # type: ignore[override]
        return self._action_spec

    def observation_spec(self):  # type: ignore[override]
        return self._observation_spec

    def _reset(self):
        self._state = np.zeros(self._observation_spec.shape, dtype=np.float32)
        self._episode_ended = False
        return ts.restart(self._state)

    def _step(self, action):
        if self._episode_ended:
            return self._reset()

        reward = 0.0
        terminal = False

        if terminal:
            self._episode_ended = True
            return ts.termination(self._state, reward)
        else:
            return ts.transition(self._state, reward, discount=1.0)