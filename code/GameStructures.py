import enum
import random
import numpy as np


class Cell:

    def __init__(self, revealed=False, mine=False, flagged=False, surrounding_count=0):
        self.revealed = revealed
        self.mine = mine
        self.flagged = flagged
        self.surrounding_count = surrounding_count


class GameOutcome(enum.Enum):
    WIN = 1
    INCONCLUSIVE = 0
    LOSS = -1


class Game:

    def __init__(self, rows, columns, mine_count):

        # Record basic game parameters.
        self.__rows__ = rows
        self.__columns__ = columns
        self.__mine_count__ = mine_count

        self.__revealed_cell_count__ = 0
        self.__game_outcome__ = GameOutcome.INCONCLUSIVE
        self.__unused_flag_count__ = mine_count

        # Create minesweeper grid.
        self.__grid__ = np.empty((rows, columns), dtype=Cell)
        self.__prev_moves__ = []
        for r in range(rows):
            for c in range(columns):
                self.__grid__[r][c] = Cell()

        # Add mines.
        self.__mine_locations__ = np.array([(k // columns, k - (k // columns) * columns)
                                            for k in random.sample(range(0, rows*columns), mine_count)])
        for r, c in self.__mine_locations__:
            self.__grid__[r][c].mine = True
        for r in range(rows):
            for c in range(columns):
                for r2, c2 in self.get_surrounding_cells(r, c):
                    if self.__grid__[r2][c2].mine:
                        self.__grid__[r][c].surrounding_count += 1

    # Getters
    def get_rows(self):
        return self.__rows__

    def get_columns(self):
        return self.__columns__

    def get_mine_count(self):
        return self.__mine_count__

    def get_unused_flag_count(self):
        return self.__unused_flag_count__

    def get_game_outcome(self):
        return self.__game_outcome__

    def is_revealed(self, row, column):
        return self.__grid__[row][column].revealed

    def get_surrounding_count(self, row, column):
        if self.is_revealed(row, column) or self.__game_outcome__ != GameOutcome.INCONCLUSIVE:
            return self.__grid__[row][column].surrounding_count
        else:
            return 0

    def is_flagged(self, row, column):
        return self.__grid__[row][column].flagged

    def is_mine(self, row, column):
        if self.is_revealed(row, column) or self.__game_outcome__ != GameOutcome.INCONCLUSIVE:
            return self.__grid__[row][column].mine
        else:
            return False

    def get_surrounding_cells(self, row, column):
        return iter([(r2, c2) for r2 in range(row - 1, row + 1 + 1) for c2 in range(column - 1, column + 1 + 1)
                     if 0 <= r2 < self.__rows__ and 0 <= c2 < self.__columns__ and not (r2 == row and c2 == column)])

    def get_revealed_number_cells(self, include_flag_neighbours=True):
        number_cells = set()
        for r in range(self.__rows__):
            for c in range(self.__columns__):
                if (self.__grid__[r][c].revealed and self.__grid__[r][c].surrounding_count > 0 and
                        not self.__grid__[r][c].mine):
                    if include_flag_neighbours:
                        number_cells.add((r, c))
                    else:
                        nonflagged_around = False
                        for r2, c2 in self.get_surrounding_cells(r, c):
                            if not self.__grid__[r2][c2].flagged and not self.__grid__[r2][c2].revealed:
                                nonflagged_around = True
                                break
                        if nonflagged_around:
                            number_cells.add((r, c))
        return tuple(number_cells)

    def get_unrevealed_border_cells(self, include_flagged=True):
        border_cells = set()
        for n_r in range(self.__rows__):
            for n_c in range(self.__columns__):
                if self.__grid__[n_r][n_c].revealed and not self.__grid__[n_r][n_c].mine:
                    for b_r, b_c in self.get_surrounding_cells(n_r, n_c):
                        if ((include_flagged or not self.__grid__[b_r][b_c].flagged) and
                                not self.__grid__[b_r][b_c].revealed):
                            border_cells.add((b_r, b_c))
        return tuple(border_cells)

    def get_unrevealed_nonborder_cells(self, include_flagged=True):
        border_cells = set(self.get_unrevealed_border_cells())

        nonborder_cells = set()
        for r in range(self.__rows__):
            for c in range(self.__columns__):
                if not self.__grid__[r][c].revealed and (include_flagged or not self.__grid__[r][c].flagged):
                    if (r, c) not in border_cells:
                        nonborder_cells.add((r, c))
        return tuple(nonborder_cells)

    # Actions / Game Interactions
    def __single_reveal__(self, row, column):
        if not self.__grid__[row][column].revealed and self.__game_outcome__ == GameOutcome.INCONCLUSIVE:
            self.__grid__[row][column].revealed = True
            self.__revealed_cell_count__ += 1
            if self.__grid__[row][column].flagged:
                self.unflag(row, column)

            if self.__grid__[row][column].mine:
                self.__game_outcome__ = GameOutcome.LOSS
            elif self.__revealed_cell_count__ == self.__rows__ * self.__columns__ - self.__mine_count__:
                self.__game_outcome__ = GameOutcome.WIN
            else:
                self.__game_outcome__ = GameOutcome.INCONCLUSIVE
            return True
        return False

    def __single_unreveal__(self, row, column):
        if self.__grid__[row][column].revealed:
            self.__grid__[row][column].revealed = False
            self.__revealed_cell_count__ -= 1

            if self.__game_outcome__ == GameOutcome.WIN:
                self.__game_outcome__ = GameOutcome.INCONCLUSIVE
            elif self.__game_outcome__ == GameOutcome.LOSS:
                lost = False
                for r, c in self.__mine_locations__:
                    if self.__grid__[r][c].revealed and self.__grid__[r][c].mine:
                        lost = True
                        break
                if not lost:
                    self.__game_outcome__ = GameOutcome.INCONCLUSIVE
            return True
        return False

    def chain_reveal(self, row, column):
        to_reveal_list = [(row, column)]
        to_reveal_set = {(row, column)}
        for r, c in to_reveal_list:
            self.__single_reveal__(r, c)
            to_reveal_set.remove((r, c))
            if self.__grid__[r][c].surrounding_count == 0:
                for r2, c2 in self.get_surrounding_cells(r, c):
                    if not self.__grid__[r2][c2].revealed and (r2, c2) not in to_reveal_set:
                        to_reveal_list.append((r2, c2))
                        to_reveal_set.add((r2, c2))
        self.__prev_moves__.append(tuple(to_reveal_list))

    def undo_reveal(self):
        if self.__prev_moves__:
            for r, c in self.__prev_moves__.pop():
                self.__single_unreveal__(r, c)

    def flag(self, row, column):
        if (self.__unused_flag_count__ > 0 and not self.__grid__[row][column].revealed and
                not self.__grid__[row][column].flagged):
            self.__grid__[row][column].flagged = True
            self.__unused_flag_count__ -= 1

    def unflag(self, row, column):
        if self.__grid__[row][column].flagged:
            self.__grid__[row][column].flagged = False
            self.__unused_flag_count__ += 1
