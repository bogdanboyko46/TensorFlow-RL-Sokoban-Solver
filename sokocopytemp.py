import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

import time


# Initialize pygame modules
pygame.init()

font = pygame.font.Font('arial.ttf', 25)

# Enum for player movement directions
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


# Point structure to store x and y coordinates
Point = namedtuple('Point', 'x, y')

# RGB color definitions
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
PINK = (255, 0, 255)

# Size of each player block
BLOCK_SIZE = 80

class Sokoban:
    def __init__(self, w=720, h=720):
        # Screen width and height
        self.w = w
        self.h = h
        self.player = None
        self.blocks = None
        self.holes = None
        self.in_hole = 0
        self.paths = None
        self.tot_block_ct = 0
        self.block_hole_pairs = None

        # Initialize game window
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Sokoban')

        self.reset()

    def paired(self, point):
        return point in self.block_hole_pairs

    def reset(self):
        x_p = random.randint(0, 8) * BLOCK_SIZE
        y_p = random.randint(0, 8) * BLOCK_SIZE
        self.moves_made = 0
        self.block_hole_pairs = set()
        self.player = Point(x_p, y_p)
        self.in_hole = 0
        self.blocks = set()
        self.holes = set()
        self.paths = dict()

        while len(self.blocks) < 2:
            x = random.randint(0, 7) * BLOCK_SIZE
            y = random.randint(0, 7) * BLOCK_SIZE

            if Point(x, y) != self.player:
                self.blocks.add(Point(x, y))

        self.tot_block_ct = len(self.blocks)

        while len(self.holes) < 2:
            x = random.randint(0, 8) * BLOCK_SIZE
            y = random.randint(0, 8) * BLOCK_SIZE

            if Point(x, y) != self.player and Point(x, y) not in self.blocks:
                self.holes.add(Point(x, y))

        for block in self.blocks:
            self.paths[block] = dict()

            for hole in self.holes:
                self.paths[block][hole] = abs(block.x - hole.x) / BLOCK_SIZE + abs(block.y - hole.y) / BLOCK_SIZE

    def _get_min_total_distance(self):
        """
        For each unpaired block, find its distance to its nearest unpaired hole
        Returns the sum of those minimum distances
        This avoids conflicting signals from multiple holes
        """
        unpaired_blocks = [b for b in self.paths]
        unpaired_holes = [h for h in self.holes if not self.paired(h)]

        if not unpaired_blocks or not unpaired_holes:
            return 0

        total = 0
        used_holes = set()

        assignments = []
        for block in unpaired_blocks:
            best_hole = None
            best_dist = float('inf')
            for hole in unpaired_holes:
                dist = self.paths[block].get(hole, float('inf'))
                if dist < best_dist:
                    best_dist = dist
                    best_hole = hole
            assignments.append((block, best_hole, best_dist))

        # Sort by distance so closest pairs get assigned first
        assignments.sort(key=lambda x: x[2])

        for block, hole, dist in assignments:
            if hole not in used_holes:
                total += dist
                used_holes.add(hole)
            else:
                # Find next closest unused hole
                for h in unpaired_holes:
                    if h not in used_holes:
                        total += self.paths[block].get(h, float('inf'))
                        used_holes.add(h)
                        break

        return total

    def update_paths(self, old_pos, new_pos, old_in_hole):
        """
        2. Check if the number of block-hole pairs changed. If so, update tot_reward, add block and hole to dict
        3. If the above condition didn't occur, update paths and return reward based off move made
        """

        # Block pushed from one hole to another (net in_hole change is 0)
        if old_in_hole == self.in_hole and old_pos in self.block_hole_pairs and new_pos in self.holes:
            self.block_hole_pairs.remove(old_pos)
            self.block_hole_pairs.add(new_pos)

            # Hole at old_pos is now free
            for block in self.paths:
                self.paths[block][old_pos] = abs(block.x - old_pos.x) / BLOCK_SIZE + abs(block.y - old_pos.y) / BLOCK_SIZE

            # Hole at new_pos is now occupied
            for block in self.paths:
                if new_pos in self.paths[block]:
                    del self.paths[block][new_pos]

            print("PUSHED FROM HOLE TO HOLE!")
            return 35

        if old_in_hole < self.in_hole:

            self.block_hole_pairs.add(new_pos)

            # delete the old block's positions
            del self.paths[old_pos]

            # a block was pushed into a hole, delete the hole's dist from each block to essentially ignore it
            for block in self.paths:
                if new_pos in self.paths[block]:
                    del self.paths[block][new_pos]

            print("PUSHED INTO HOLE!")
            return 35

        elif old_in_hole > self.in_hole:
            # a block was pushed off a hole, add the block and the previously paired hole to "paths"

            self.block_hole_pairs.remove(old_pos)

            self.paths[new_pos] = dict()

            for hole in self.holes:

                # skip hole if its occupied by a block
                if self.paired(hole):
                    continue

                self.paths[new_pos][hole] = abs(new_pos.x - hole.x) / BLOCK_SIZE + abs(new_pos.y - hole.y) / BLOCK_SIZE

            for block in self.paths:

                self.paths[block][old_pos] = abs(block.x - old_pos.x) / BLOCK_SIZE + abs(block.y - old_pos.y) / BLOCK_SIZE

            print("PUSHED OFF HOLE")
            return -20

        # use distance-delta reward
        # Snapshot old total min distance before updating paths
        old_total_dist = self._get_min_total_distance()

        # Update paths dict for the moved block
        self.paths[new_pos] = dict()
        for hole in self.holes:
            if self.paired(hole):
                continue
            new_dist = abs(new_pos.x - hole.x) / BLOCK_SIZE + abs(new_pos.y - hole.y) / BLOCK_SIZE
            self.paths[new_pos][hole] = new_dist

        del self.paths[old_pos]

        # Snapshot new total min distance after updating paths
        new_total_dist = self._get_min_total_distance()

        # Reward is proportional to how much closer blocks got to their best holes
        # Positive if total distance decreased, negative if it increased
        # Bounded: max change per step is ~2 (one block moves one tile)
        distance_delta = old_total_dist - new_total_dist  # positive = improvement

        if distance_delta > 0:
            return distance_delta * 3  # reward for getting closer
        else:
            return distance_delta * 2  # penalty for moving away

    def immovable_block_detect(self):
        # create a dict denoting the number of blocks / holes in each border
        block_ct_borders = [0, 0, 0, 0] # UP, DOWN, LEFT, RIGHT
        hole_ct_borders = [0, 0, 0, 0] # UP, DOWN, LEFT, RIGHT

        for block in self.blocks:
            # hole in occupied
            if block in self.holes:
                continue
            if block in (Point(0, 0),
                         Point(self.w - BLOCK_SIZE, 0),
                         Point(0, self.h - BLOCK_SIZE),
                         Point(self.w - BLOCK_SIZE, self.h - BLOCK_SIZE)):
                return True

            # border presence check
            if block.x == 0:
                block_ct_borders[2] += 1
            elif block.x == self.w - BLOCK_SIZE:
                block_ct_borders[3] += 1
            elif block.y == 0:
                block_ct_borders[0] += 1
            elif block.y == self.h - BLOCK_SIZE:
                block_ct_borders[1] += 1

        # get the border count for each hole
        for hole in self.holes:
            # hole is occupied
            if hole in self.blocks:
                continue

            if hole.x == 0:
                hole_ct_borders[2] += 1
            elif hole.x == self.w - BLOCK_SIZE:
                hole_ct_borders[3] += 1
            elif hole.y == 0:
                hole_ct_borders[0] += 1
            elif hole.y == self.h - BLOCK_SIZE:
                hole_ct_borders[1] += 1

        # compare arrays
        for i in range(0, len(block_ct_borders)):
            if block_ct_borders[i] > hole_ct_borders[i]:
                return True

        return False

    def play_step(self, action):

        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # action is [up, down, left, right]
        if isinstance(action, (list, tuple, np.ndarray)):
            idx = int(np.argmax(action))
            action = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT][idx]

        self.moves_made += 1

        game_over = False
        reward = -0.1  # small time penalty

        # get old player states
        old_x, old_y = self.player.x, self.player.y
        old_block_hole_pairs = self.in_hole

        # execute move from agent action
        old_pushed_block_pos, new_pushed_block_pos = self._move(action)

        if old_pushed_block_pos and new_pushed_block_pos:
            reward += self.update_paths(old_pushed_block_pos, new_pushed_block_pos, old_block_hole_pairs)
        elif old_x == self.player.x and old_y == self.player.y:
            reward -= 5  # walked into wall

        # check if agent completed the game
        if self.in_hole == len(self.holes):
            reward += 200
            game_over = True
            return reward, game_over, True

        # check if agent moved a block into an immovable state
        if self.immovable_block_detect():
            reward -= 50  # much harsher penalty for dead state
            game_over = True
            return reward, game_over, False

        if self.moves_made > 1600:
            reward -= 25  # timeout penalty
            game_over = True
            return reward, game_over, False

        self._update_ui()

        return reward, game_over, False

    # Moves the player, Returns old/new block positions if a block is pushed
    def _move(self, direction):
        x = self.player.x
        y = self.player.y
        old_pushed_block_pos = None
        new_pushed_block_pos = None

        if direction == Direction.RIGHT and self.can_move_right():
            if Point(x + BLOCK_SIZE, y) in self.blocks:
                old_pushed_block_pos = Point(x + BLOCK_SIZE, y)
                if old_pushed_block_pos in self.holes:
                    self.in_hole -= 1
                new_pushed_block_pos = Point(x + BLOCK_SIZE * 2, y)
                if new_pushed_block_pos in self.holes:
                    self.in_hole += 1
            x += BLOCK_SIZE

        elif direction == Direction.LEFT and self.can_move_left():
            if Point(x - BLOCK_SIZE, y) in self.blocks:
                old_pushed_block_pos = Point(x - BLOCK_SIZE, y)
                if old_pushed_block_pos in self.holes:
                    self.in_hole -= 1
                new_pushed_block_pos = Point(x - BLOCK_SIZE * 2, y)
                if new_pushed_block_pos in self.holes:
                    self.in_hole += 1
            x -= BLOCK_SIZE

        elif direction == Direction.DOWN and self.can_move_down():
            if Point(x, y + BLOCK_SIZE) in self.blocks:
                old_pushed_block_pos = Point(x, y + BLOCK_SIZE)
                if old_pushed_block_pos in self.holes:
                    self.in_hole -= 1
                new_pushed_block_pos = Point(x, y + BLOCK_SIZE * 2)
                if new_pushed_block_pos in self.holes:
                    self.in_hole += 1
            y += BLOCK_SIZE

        elif direction == Direction.UP and self.can_move_up():
            if Point(x, y - BLOCK_SIZE) in self.blocks:
                old_pushed_block_pos = Point(x, y - BLOCK_SIZE)
                if old_pushed_block_pos in self.holes:
                    self.in_hole -= 1
                new_pushed_block_pos = Point(x, y - BLOCK_SIZE * 2)
                if new_pushed_block_pos in self.holes:
                    self.in_hole += 1
            y -= BLOCK_SIZE

        self.player = Point(x, y)

        if old_pushed_block_pos and new_pushed_block_pos:
            self.blocks.remove(old_pushed_block_pos)
            self.blocks.add(new_pushed_block_pos)

        return old_pushed_block_pos, new_pushed_block_pos

    def _update_ui(self):
        self.display.fill(BLACK)

        p_pt = self.player
        pygame.draw.rect(self.display, BLUE,
                         pygame.Rect(p_pt.x, p_pt.y, BLOCK_SIZE, BLOCK_SIZE))
        for b_pt in self.blocks:
            pygame.draw.rect(self.display, RED,
                             pygame.Rect(b_pt.x, b_pt.y, BLOCK_SIZE, BLOCK_SIZE))

        for h_pt in self.holes:
            if h_pt in self.blocks:
                pygame.draw.rect(self.display, GREEN,
                                 pygame.Rect(h_pt.x, h_pt.y, BLOCK_SIZE, BLOCK_SIZE))
            elif h_pt == p_pt:
                pygame.draw.rect(self.display, CYAN,
                                 pygame.Rect(h_pt.x, h_pt.y, BLOCK_SIZE, BLOCK_SIZE))
            else:
                pygame.draw.rect(self.display, WHITE,
                                 pygame.Rect(h_pt.x, h_pt.y, BLOCK_SIZE, BLOCK_SIZE))

        pygame.display.flip()

    def can_move_right(self) -> bool:
        x = self.player.x
        y = self.player.y

        if (x + BLOCK_SIZE) < self.w:
            new_x = x + BLOCK_SIZE
            if Point(new_x, y) in self.blocks:
                if new_x + BLOCK_SIZE >= self.w or Point(new_x + BLOCK_SIZE, y) in self.blocks:
                    return False
            return True
        return False

    def can_move_left(self) -> bool:
        x = self.player.x
        y = self.player.y
        if (x - BLOCK_SIZE) >= 0:
            new_x = x - BLOCK_SIZE
            if Point(new_x, y) in self.blocks:
                if new_x - BLOCK_SIZE < 0 or Point(new_x - BLOCK_SIZE, y) in self.blocks:
                    return False
            return True
        return False

    def can_move_down(self) -> bool:
        x = self.player.x
        y = self.player.y
        if (y + BLOCK_SIZE) < self.h:
            new_y = y + BLOCK_SIZE
            if Point(x, new_y) in self.blocks:
                if new_y + BLOCK_SIZE >= self.w or Point(x, new_y + BLOCK_SIZE) in self.blocks:
                    return False
            return True
        return False

    def can_move_up(self) -> bool:
        x = self.player.x
        y = self.player.y
        if (y - BLOCK_SIZE) >= 0:
            new_y = y - BLOCK_SIZE
            if Point(x, new_y) in self.blocks:
                if new_y - BLOCK_SIZE < 0 or Point(x, new_y - BLOCK_SIZE) in self.blocks:
                    return False
            return True
        return False

    def player_state(self):
        return [self.player.x / BLOCK_SIZE, self.player.y / BLOCK_SIZE]

    def block_state(self):
        res = []
        x1 = self.player.x
        y1 = self.player.y
        for block in self.blocks:
            x2 = block.x
            y2 = block.y
            res.append((x1 - x2) / BLOCK_SIZE)
            res.append((y1 - y2) / BLOCK_SIZE)
        return res

    def hole_state(self):
        res = []
        x1 = self.player.x
        y1 = self.player.y
        for hole in self.holes:
            x2 = hole.x
            y2 = hole.y
            res.append((x1 - x2) / BLOCK_SIZE)
            res.append((y1 - y2) / BLOCK_SIZE)
        return res