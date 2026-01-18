import torch
import random
import numpy as np
from sokobangamepy import Sokoban
from collections import deque

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001 # learning rate

class Agent:

    def __init__(self):
        
        self.number_of_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft when memory is reached
        # TODO: model, trainer

    def get_state(self, game):

        # State array is as follows:
        """"
        A ‘state’ array consisting of # boolean values (0, 1): (4 + n*5 + m*4)

        N = amount of blocks
        M = amount of holes

	    User ability to move:
		    UP, DOWN, LEFT, RIGHT

        Each block:
		    Availability to user:
            UP, DOWN, LEFT, RIGHT

        Danger value (when user is in contact with block and next to unmovable pos)

        Each hole:
	        Availability of user:
	        UP, DOWN, LEFT, RIGHT

        """
        pass

    def remember(self, state, action, reward, next_state, game_over):
        pass

    def train_long_memory(self):
        pass

    def train_short_memory(self, state, action, reward, next_state, game_over):
        pass

    def get_action(self, state):
        pass

def train():
    steps_taken = [] # the # of steps the agent takes to win
    current_steps = 0
    number_of_games = 0
    agent = Agent()
    game = Sokoban()


    while True:
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)
                                
        # perform move and get state
        reward, game_over, game_win = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short mem
        agent.train_short_memory(state_old, final_move, reward, state_new, game_over)

        # remember
        agent.remember(state_old, final_move, reward, state_new, game_over)
        
        current_steps += 1

        if game_over:
            # train long term mem
            game.reset()
            number_of_games += 1
            agent.train_long_memory() 
            
            if game_win:
                steps_taken.append(current_steps)

            # reset current steps
            current_steps = 0
            
            print(f'Game {number_of_games}, Record: {max(steps_taken)}')

if __name__ == '__main__':
    train()
