import pygame
import sys

from GameStructures import *
from Bot import *


# Set Parameters
ROWS = 40
COLUMNS = 40
MINE_RATE = 0.15

MINES = ROWS*COLUMNS // int(1/MINE_RATE)
IMAGE_SIZE = 20

MINE = -1.0
NOT_MINE = -2.0

# Initialize Pygame.
pygame.init()
screen = pygame.display.set_mode((COLUMNS*IMAGE_SIZE, ROWS*IMAGE_SIZE))
pygame.display.set_caption("Minesweeper")
pygame.display.set_icon(pygame.image.load('../skins/icon.png'))


# Load Skins.
NUM_DICT = {i: pygame.image.load(f'../skins/numbers/{i}.png') for i in range(1, 9)}
REVEALED_CELL = pygame.image.load('../skins/revealed_square.png')
BOMB = pygame.image.load('../skins/bomb.png')
COVERED_CELL = pygame.image.load('../skins/covered_square.png')
COVERED_CELL_HIGHLIGHTED = pygame.image.load('../skins/covered_square_highlighted.png')
FLAG = pygame.image.load('../skins/flag.png')
LOST_REVEALED_CELL = pygame.image.load('../skins/lost_square_highlighted.png')

probability_skins = {NOT_MINE: pygame.image.load('../skins/probabilities/1.png'),
                     MINE: pygame.image.load('../skins/probabilities/0.png'),
                     1.0: pygame.image.load('../skins/probabilities/10.png'),
                     0.9: pygame.image.load('../skins/probabilities/09.png'),
                     0.8: pygame.image.load('../skins/probabilities/08.png'),
                     0.7: pygame.image.load('../skins/probabilities/07.png'),
                     0.6: pygame.image.load('../skins/probabilities/06.png'),
                     0.5: pygame.image.load('../skins/probabilities/05.png'),
                     0.4: pygame.image.load('../skins/probabilities/04.png'),
                     0.3: pygame.image.load('../skins/probabilities/03.png'),
                     0.2: pygame.image.load('../skins/probabilities/02.png'),
                     0.1: pygame.image.load('../skins/probabilities/01.png'),
                     0.0: pygame.image.load('../skins/probabilities/00.png')}


# Initialize Game Variables.
game = Game(ROWS, COLUMNS, MINES)
selected_cell = 0, 0
probability_tables = {}
bot = Bot(game)


# Main Loop
while True:
    for event in pygame.event.get():
        selected_cell = pygame.mouse.get_pos()[1] // IMAGE_SIZE, pygame.mouse.get_pos()[0] // IMAGE_SIZE

        # Exit Game
        if event.type == pygame.QUIT:
            sys.exit()

        # Make Moves
        pressed_keys = pygame.key.get_pressed()
        if event.type == pygame.MOUSEBUTTONDOWN:
            r, c = selected_cell
            if event.button == 1:
                game.chain_reveal(r, c)
            elif event.button == 3:
                if game.is_flagged(r, c):
                    game.unflag(r, c)
                elif not game.is_flagged(r, c):
                    game.flag(r, c)
            probability_tables.clear()

        # Undo Moves
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            game.undo_reveal()
            bot.to_flag.clear()
            bot.to_reveal.clear()
            probability_tables.clear()

        # Restart
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            game = Game(ROWS, COLUMNS, MINES)
            bot = Bot(game)

        # Quit
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            sys.exit()

        # Fast chain deduction Bot.
        if pressed_keys[pygame.K_SPACE] and pressed_keys[pygame.K_b]:
            bot.take_action()
            for r, c in bot.to_reveal:
                if not game.is_revealed(r, c):
                    game.chain_reveal(r, c)
            for r, c in bot.to_flag:
                game.flag(r, c)
            probability_tables.clear()

        # Single Deduction Bot.
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            bot.take_action()
            probability_tables.clear()

        # Chain deduction Bot.
        elif pressed_keys[pygame.K_b]:
            bot.take_action()
            probability_tables.clear()

        # Probability Display.
        if pressed_keys[pygame.K_p]:
            if game.get_game_outcome() == GameOutcome.INCONCLUSIVE:
                if probability_tables == {}:
                    probability_tables = bot.construct_probability_tables()
        else:
            if probability_tables:
                probability_tables.clear()

    # Display Everything.
    for row in range(ROWS):
        for column in range(COLUMNS):
            if game.is_revealed(row, column):
                if game.is_mine(row, column):
                    screen.blit(LOST_REVEALED_CELL, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                    screen.blit(BOMB, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                else:
                    screen.blit(REVEALED_CELL, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                    surrounding_mines = game.get_surrounding_count(row, column)
                    if surrounding_mines > 0:
                        screen.blit(NUM_DICT[surrounding_mines], (column * IMAGE_SIZE, row * IMAGE_SIZE))
            else:
                if (row, column) == selected_cell:
                    screen.blit(COVERED_CELL_HIGHLIGHTED, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                else:
                    screen.blit(COVERED_CELL, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                if game.get_game_outcome() == GameOutcome.INCONCLUSIVE:
                    if game.is_flagged(row, column):
                        screen.blit(FLAG, (column * IMAGE_SIZE, row * IMAGE_SIZE))
                else:
                    if game.is_mine(row, column):
                        screen.blit(BOMB, (column * IMAGE_SIZE, row * IMAGE_SIZE))

    # Display Probabilities.
    for r, c in probability_tables:
        prob = probability_tables[(r, c)]
        if prob == 1.0:
            screen.blit(probability_skins[NOT_MINE], (c * IMAGE_SIZE, r * IMAGE_SIZE))
        elif prob == 0.0:
            screen.blit(probability_skins[MINE], (c * IMAGE_SIZE, r * IMAGE_SIZE))
        else:
            screen.blit(probability_skins[round(prob, 1)], (c * IMAGE_SIZE, r * IMAGE_SIZE))

    pygame.display.update()
