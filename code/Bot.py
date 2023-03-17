import itertools

from GameStructures import *


NOT_MINE = 0
MINE = 1


class Bot:
    """
    This class corresponds to a bot that plays minesweeper.

    :ivar to_reveal: A dynamically updating list of cells the bot deems the best option(s) to reveal.
    :type to_reveal: List[Tuple[int, int]]
    :ivar to_flag: A dynamically updating list of cells the bot deems the best option(s) to flag.
    :type to_flag: List[Tuple[int, int]]
    :ivar game: A game object that provides the bot with the current game state which allows it to make decisions. This
                object updates as the game progresses, meaning the bot does not need to repeatedly pass in a game object
                as a parameter to its methods.
    :type game: Game
    """

    def __init__(self, game):

        self.to_reveal = []
        self.to_flag = []
        self.game = game

    def take_action(self):
        """
        Either reveals or flags a single cell in a game of minesweeper. More specifically, in the game of
        minesweeper stored in this class's fields. Which cell to reveal is determined by various deduction methods from
        this class.
        """

        if self.game.get_game_outcome() == GameOutcome.INCONCLUSIVE:

            # Clear out already revealed / flagged cell(s).
            self.to_reveal = [(r, c) for r, c in self.to_reveal if not self.game.is_revealed(r, c)]
            self.to_flag = [(r, c) for r, c in self.to_flag if not self.game.is_revealed(r, c)]

            # Use deduction systems to determine which cell(s) to flag / reveal.
            if self.to_reveal == [] and self.to_flag == []:
                self.basic_deduction()
            if self.to_reveal == [] and self.to_flag == []:
                self.complex_deduction()
            if self.to_reveal == [] and self.to_flag == []:
                self.random_decision()

            # Reveal / flag chosen cell.
            if self.to_reveal:
                r, c = self.to_reveal.pop()
                self.game.chain_reveal(r, c)
            elif self.to_flag:
                r, c = self.to_flag.pop()
                self.game.flag(r, c)

    def random_decision(self, printing=True):
        """
        This method chooses a random unrevealed cell on the minesweeper game included in this class's fields. This cell
        is then added to the field to_reveal.

        :param printing: A boolean parameter that determines whether this function prints a message when it adds a cell
                         to the to_reveal field of this class.
        """

        # Try to avoid revealing flagged cells.
        reveal_cell_candidates = []
        for r in range(self.game.get_rows()):
            for c in range(self.game.get_columns()):
                if not self.game.is_revealed(r, c) and not self.game.is_flagged(r, c):
                    reveal_cell_candidates.append((r, c))

        # If necessary, choose a reveal among flagged cells.
        if not reveal_cell_candidates:
            for r in range(self.game.get_rows()):
                for c in range(self.game.get_columns()):
                    if not self.game.is_revealed(r, c):
                        reveal_cell_candidates.append((r, c))

        reveal_cell = random.choice(reveal_cell_candidates)
        if printing:
            print("RANDOM DECISION MADE!")
        self.to_reveal.append(reveal_cell)

    def basic_deduction(self):
        """
        This method looks at the current game state, and decides which cell(s), if any, to reveal and/or flag. This
        decision is made by looking at all revealed (non-zero) numbered cells, and seeing if their individual number
        guarantees a cell around them to be mines or not. It will not account for dependencies.
        """

        for n_r in range(self.game.get_rows()):
            for n_c in range(self.game.get_columns()):
                if (self.game.is_revealed(n_r, n_c) and self.game.get_surrounding_count(n_r, n_c) > 0 and
                        not self.game.is_mine(n_r, n_c)):
                    surrounding = 0
                    surrounding_flagged = 0
                    for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c):
                        if not self.game.is_revealed(b_r, b_c):
                            surrounding += 1
                            if self.game.is_flagged(b_r, b_c):
                                surrounding_flagged += 1

                    if surrounding == self.game.get_surrounding_count(n_r, n_c):
                        for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c):
                            if (not self.game.is_revealed(b_r, b_c) and not self.game.is_flagged(b_r, b_c) and
                                    (b_r, b_c) not in self.to_flag):
                                self.to_flag.append((b_r, b_c))
                    elif surrounding_flagged == self.game.get_surrounding_count(n_r, n_c):
                        for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c):
                            if (not self.game.is_revealed(b_r, b_c) and not self.game.is_flagged(b_r, b_c) and
                                    (b_r, b_c) not in self.to_reveal):
                                self.to_reveal.append((b_r, b_c))

    def complex_deduction(self, printing=True, certain_only=False):
        """
        This method looks at the current game state, and uses probability tables to decide which cell(s) to reveal
        and/or flag. If the probability tables yield any certain result, all those cell(s) are added to the to_revel or
        to_flag fields of this class. Otherwise, the cell least probable to be a mine is added to the to_reveal field.

        :param printing: A boolean value that represents whether to print a message notifying the user if a risk was
                         taken in the current choice to cell to reveal. Here risk means a less than 100% probability
                         that that cell to reveal is safe.
        :param certain_only: A boolean parameter that, if set to true, prevents this function from choosing cells to
                             reveal that are not 100% not a mine. If False, this function is guaranteed to make a
                             contribution to to_reveal or to_flag.
        """

        probability_table = self.construct_probability_tables()
        if 1.0 in probability_table.values() or 0.0 in probability_table.values():
            for cell in probability_table.keys():
                if probability_table[cell] == 1.0 and cell not in self.to_reveal:
                    self.to_reveal.append(cell)
                if probability_table[cell] == 0.0 and cell not in self.to_flag:
                    self.to_flag.append(cell)
        elif not certain_only:
            best_probability = probability_table[max(probability_table.keys(), key=probability_table.get)]
            best_guesses = [cell for cell in probability_table.keys() if probability_table[cell] == best_probability]
            if printing:
                print("GUESS WITH SUCCESS CHANCE", round(best_probability, 2))
            best_guess = random.choice(best_guesses)
            self.to_reveal.append(best_guess)

    def construct_probability_tables(self, digit_rounding=8):
        """
        For every unrevealed cell in the game, this function calculates and assigns a probability to that cell. This
        corresponds to the probability that that unrevealed cell is not a mine (not mine = 1, mine = 0). This is
        calculated using only information available to the player.

        :return: A dictionary with keys as unrevealed cells (stored as 2-tuples) and values as floats between 0 and 1
        corresponding to the probability that that unrevealed cell is not a mine.
        """

        # STEP 1: Make the relevant data structures.
        number_cells = self.game.get_revealed_number_cells(include_flag_neighbours=False)
        border_cells = self.game.get_unrevealed_border_cells(include_flagged=False)
        nonborder_cells = self.game.get_unrevealed_nonborder_cells()
        number_cells_border_neighbors = {n_cell: [] for n_cell in number_cells}
        border_cells_number_neighbors = {b_cell: [] for b_cell in border_cells}
        for n_cell in number_cells:
            n_r, n_c = n_cell
            for b_cell in self.game.get_surrounding_cells(n_r, n_c):
                if b_cell in border_cells_number_neighbors:
                    number_cells_border_neighbors[n_cell].append(b_cell)
        for b_cell in border_cells:
            b_r, b_c = b_cell
            for n_cell in self.game.get_surrounding_cells(b_r, b_c):
                if n_cell in number_cells_border_neighbors:
                    border_cells_number_neighbors[b_cell].append(n_cell)
        unrevealed_cell_count = len(border_cells) + len(nonborder_cells)
        remaining_mines = self.game.get_unused_flag_count()

        # Step 2: Split cells into dependant islands and reorder them.
        def manhattan_distance(cell1, cell2):
            return abs(cell1[0] - cell2[0]) + abs(cell1[1] - cell2[1])

        cell_list = list(border_cells)
        cell_set = set(cell_list)
        border_cell_islands = []

        while cell_list:
            b_cell = cell_list.pop()
            cell_set.remove(b_cell)

            to_add_list = [b_cell]
            to_add_set = set(to_add_list)

            for b_cell in to_add_list:
                for n_cell in border_cells_number_neighbors[b_cell]:
                    for new_b_cell in number_cells_border_neighbors[n_cell]:
                        if new_b_cell in cell_set and new_b_cell not in to_add_set:
                            to_add_list.append(new_b_cell)
                            to_add_set.add(new_b_cell)
                            cell_list.remove(new_b_cell)
                            cell_set.remove(new_b_cell)

            # Sort to increase dependency between neighbouring cells to hopefully improve solution searching.
            if to_add_list:
                base_cell = min(to_add_list)
                to_add_list.sort(key=lambda x: manhattan_distance(x, base_cell))
                border_cell_islands.append(tuple(to_add_list))

        border_cell_islands.sort(key=len)
        border_cell_islands = tuple(border_cell_islands)

        # Step 3: Calculate mine arrangement possibilities.
        surrounding_mine_constraints = {(n_r, n_c): self.game.get_surrounding_count(n_r, n_c) -
                                        len([1 for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c)
                                             if not self.game.is_revealed(b_r, b_c) and self.game.is_flagged(b_r, b_c)])
                                        for n_r, n_c in number_cells}
        surrounding_unknown_constraints = {n_cell: len(number_cells_border_neighbors[n_cell])
                                           for n_cell in number_cells}

        def get_solution_arrays(border_cell_group, surrounding_mine_constraints, surrounding_unknown_constraints,
                                current_solution, solutions, mines_used=0):
            """
            This is a recursive searching function designed to find all possible underlying solutions to a group of
            unrevealed cells in a minesweeper grid.

            :param border_cell_group: An iterable of integer 2-tuples corresponding to a group of border cells in a
            minesweeper game.
            :param surrounding_mine_constraints: A dictionary with keys of integer 2-tuples corresponding to
            non-zero revealed cells in a minesweeper game. The values represent the number of surrounding mines, but
            unlike the value on the game grid, these dynamically update during simulation.
            :param surrounding_unknown_constraints: A dictionary with keys of integer 2-tuples corresponding to
            non-zero revealed cells in a minesweeper game. The values represent the number of surrounding cells who's
            mine/not mine status is not yet known. Unlike the values obtainable from the game grid,these dynamically
            update during simulation.
            :param current_solution: A list of boolean values corresponding to whether or not a particular cell is a
            mine or not. Indexes from the solution correspond to the cell at that index from border_cell_group. This
            parameter is dynamic, and frequently modified to go through all solution possibilities.
            :param solutions: A list of lists of boolean values corresponding to whether or not a particular cell is a
            mine or not. Indexes from the solution correspond to the cell at that index from border_cell_group. These
            lists correspond to mine arrangements that are consistent with the provided game constraints. This
            parameter is dynamic, it starts out empty and solutions are appended to it throughout the recursion.
            :param mines_used: An integer counting the number of mines currently assumed present in the simulation.
            """

            if len(current_solution) == len(border_cell_group):
                solutions.append(current_solution.copy())
            else:
                b_cell = tuple(border_cell_group[len(current_solution)])
                for b_cell_status in (MINE, NOT_MINE):

                    current_solution.append(b_cell_status)
                    go_deeper = True
                    for n_cell in border_cells_number_neighbors[b_cell]:
                        surrounding_unknown_constraints[n_cell] -= 1
                        if b_cell_status == MINE:
                            surrounding_mine_constraints[n_cell] -= 1
                        if (surrounding_unknown_constraints[n_cell] < surrounding_mine_constraints[n_cell] or
                                surrounding_mine_constraints[n_cell] < 0):
                            go_deeper = False
                    if b_cell_status == MINE:
                        mines_used += 1
                    if mines_used > remaining_mines:
                        go_deeper = False

                    if go_deeper:
                        get_solution_arrays(border_cell_group, surrounding_mine_constraints,
                                            surrounding_unknown_constraints, current_solution, solutions, mines_used)

                    if b_cell_status == MINE:
                        mines_used -= 1
                    for n_cell in border_cells_number_neighbors[b_cell]:
                        surrounding_unknown_constraints[n_cell] += 1
                        if b_cell_status == MINE:
                            surrounding_mine_constraints[n_cell] += 1
                    current_solution.pop()

        island_solutions = []
        for i, border_cell_island in enumerate(border_cell_islands):
            solutions = []
            get_solution_arrays(np.array(border_cell_island), surrounding_mine_constraints,
                                surrounding_unknown_constraints, current_solution=[], solutions=solutions)
            island_solutions.append(solutions)

        # Step 4: Construct probability tables for border cells.
        most_island_solutions = 0
        if island_solutions:
            most_island_solutions = max([len(island_solution) for island_solution in island_solutions])
        island_solution_likelihoods = np.zeros((len(island_solutions), most_island_solutions))

        for i, solutions in enumerate(island_solutions):
            for s, solution in enumerate(solutions):
                island_solution_likelihoods[i][s] = 1.0
                temp_remaining_mines = remaining_mines
                temp_unrevealed_cell_count = unrevealed_cell_count
                for k in solution:
                    if k == NOT_MINE:
                        island_solution_likelihoods[i][s] *= ((temp_unrevealed_cell_count - temp_remaining_mines) /
                                                              temp_unrevealed_cell_count)
                    elif k == MINE:
                        island_solution_likelihoods[i][s] *= temp_remaining_mines / temp_unrevealed_cell_count
                        temp_remaining_mines -= 1
                    temp_unrevealed_cell_count -= 1

        probability_dict = {}
        for i, solutions in enumerate(island_solutions):
            normalizer_constant = sum(island_solution_likelihoods[i])
            for j, b_cell in enumerate(border_cell_islands[i]):
                probability_dict[b_cell] = sum([island_solution_likelihoods[i][s] for s, solution in
                                                enumerate(solutions) if solution[j] == NOT_MINE])
                probability_dict[b_cell] /= normalizer_constant
                probability_dict[b_cell] = round(probability_dict[b_cell], digit_rounding)

        # Step 5: Add non-border cell's probabilities to probability table.
        if len(nonborder_cells) > 0:
            island_mine_amounts = [tuple(set([sum(s) for s in solutions])) for solutions in island_solutions]
            island_mine_amount_probabilities = [{mine_amount: sum([1 for s in solutions if sum(s) == mine_amount]) /
                                                 len(solutions) for mine_amount in island_mine_amounts[i]}
                                                for i, solutions in enumerate(island_solutions)]
            normalizer_constant = 0
            average_border_mine_amount = 0
            for comb in itertools.product(*island_mine_amounts):
                if sum(comb) <= remaining_mines and remaining_mines - sum(comb) <= len(nonborder_cells):
                    comb_probability = 1
                    for i, num in enumerate(comb):
                        comb_probability *= island_mine_amount_probabilities[i][num]
                    normalizer_constant += comb_probability
                    average_border_mine_amount += comb_probability * sum(comb)
            average_border_mine_amount /= normalizer_constant

            nb_probability = 1 - (remaining_mines - average_border_mine_amount) / len(nonborder_cells)
            nb_probability = round(nb_probability, digit_rounding)
            for nb_cell in nonborder_cells:
                probability_dict[nb_cell] = nb_probability

        return probability_dict
