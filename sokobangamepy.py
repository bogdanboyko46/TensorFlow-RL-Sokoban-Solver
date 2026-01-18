import pygame              # Game library for graphics, input, and timing
import random              # Used to randomly place food
from enum import Enum      # Used for direction enum
from collections import namedtuple  # Lightweight data structure for points

# Initialize pygame modules
pygame.init()

# Load font for displaying score
font = pygame.font.Font('arial.ttf', 25)
# font = pygame.font.SysFont('arial', 25)  # Alternative system font

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

# Size of each player block
BLOCK_SIZE = 80

class Sokoban:
    def __init__(self, w=720, h=720):
        # Screen width and height
        self.w = w
        self.h = h

        # Initialize game window
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Sokoban')

        # Initial player position (center of screen)
        self.player = Point(0,0)

        block1 = Point(BLOCK_SIZE, BLOCK_SIZE)
        block2 = Point(BLOCK_SIZE * 4, BLOCK_SIZE)
        self.blocks = set()
        self.blocks.add(block1)
        self.blocks.add(block2)

        hole1 = Point(240, 400)
        hole2 = Point(320, w- BLOCK_SIZE * 4)
        self.holes = set()
        self.holes.add(hole1)
        self.holes.add(hole2)



    def play_step(self):
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self._move(Direction.LEFT)
                elif event.key == pygame.K_RIGHT:
                    self._move(Direction.RIGHT)
                elif event.key == pygame.K_UP:
                    self._move(Direction.UP)
                elif event.key == pygame.K_DOWN:
                    self._move(Direction.DOWN)

        # Update display and control speed
        self._update_ui()

    def _update_ui(self):
        # Clear screen
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



        # Update the screen
        pygame.display.flip()

    def _move(self, direction):
        x = self.player.x
        y = self.player.y

        if direction == Direction.RIGHT and (x + BLOCK_SIZE) < self.w:
            new_x = x + BLOCK_SIZE
            if Point(new_x, y) in self.blocks:
                # Checks if block cant be pushed (out of bounds, or another block to blocks right)
                if new_x + BLOCK_SIZE >= self.w or Point(new_x + BLOCK_SIZE, y) in self.blocks:
                    return
                self.blocks.remove((new_x, y))
                self.blocks.add(Point(new_x + BLOCK_SIZE, y))
            x += BLOCK_SIZE
        elif direction == Direction.LEFT and (x - BLOCK_SIZE) >= 0:
            new_x = x - BLOCK_SIZE
            if Point(new_x, y) in self.blocks:
                # Checks if block cant be pushed (out of bounds, or another block to blocks left)
                if new_x - BLOCK_SIZE < 0 or Point(new_x - BLOCK_SIZE, y) in self.blocks:
                    return
                self.blocks.remove((new_x, y))
                self.blocks.add(Point(new_x - BLOCK_SIZE, y))
            x -= BLOCK_SIZE

        elif direction == Direction.DOWN and (y + BLOCK_SIZE) < self.h:
            new_y = y + BLOCK_SIZE
            if Point(x, new_y) in self.blocks:
                # Checks if block cant be pushed (out of bounds, or another block to blocks left)
                if new_y + BLOCK_SIZE >= self.w or Point(x, new_y + BLOCK_SIZE) in self.blocks:
                    return
                self.blocks.remove((x, new_y))
                self.blocks.add(Point(x, new_y + BLOCK_SIZE))
            y += BLOCK_SIZE
        elif direction == Direction.UP and (y - BLOCK_SIZE) >= 0:
            new_y = y - BLOCK_SIZE
            if Point(x, new_y) in self.blocks:
                # Checks if block cant be pushed (out of bounds, or another block to blocks left)
                if new_y - BLOCK_SIZE < 0 or Point(x, new_y - BLOCK_SIZE) in self.blocks:
                    return
                self.blocks.remove((x, new_y))
                self.blocks.add(Point(x, new_y - BLOCK_SIZE))
            y -= BLOCK_SIZE

        self.player = Point(x, y)


# Main program
if __name__ == '__main__':
    game = Sokoban()

    # Game loop
    while True:
        game.play_step()
