import itertools

from GameStructures import *

DIGIT_ROUNDING = 8


class Bot:

    def __init__(self, game):
        self.to_reveal = []
        self.to_flag = []
        self.game = game

        for r in range(self.game.get_rows()):
            for c in range(self.game.get_columns()):
                if self.game.is_flagged(r, c):
                    self.game.unflag(r, c)

    def take_action(self):

        if self.game.get_game_outcome() == GameOutcome.INCONCLUSIVE:

            self.to_reveal = [(r, c) for r, c in self.to_reveal if not self.game.is_revealed(r, c)]
            self.to_flag = [(r, c) for r, c in self.to_flag if not self.game.is_revealed(r, c)]

            if self.to_reveal == [] and self.to_flag == []:
                self.basic_deduction()
            if self.to_reveal == [] and self.to_flag == []:
                self.complex_deduction()
            if self.to_reveal == [] and self.to_flag == []:
                self.random_decision()


            if self.to_reveal:
                r, c = self.to_reveal.pop()
                self.game.chain_reveal(r, c)
            elif self.to_flag:
                r, c = self.to_flag.pop()
                self.game.flag(r, c)

    def random_decision(self, printing=True):
        reveal_cell_candidates = []
        for r in range(self.game.get_rows()):
            for c in range(self.game.get_columns()):
                if not self.game.is_revealed(r, c) and not self.game.is_flagged(r, c):
                    reveal_cell_candidates.append((r, c))

        if not reveal_cell_candidates:
            for r in range(self.game.get_rows()):
                for c in range(self.game.get_columns()):
                    if not self.game.is_revealed((r, c)):
                        reveal_cell_candidates.append((r, c))

        reveal_cell = random.choice(reveal_cell_candidates)
        if printing:
            print("RANDOM DECISION MADE!")
        self.to_reveal.append(reveal_cell)

    def basic_deduction(self):
        for n_r in range(self.game.get_rows()):
            for n_c in range(self.game.get_columns()):
                if (self.game.is_revealed(n_r, n_c) and self.game.get_surrounding_count(n_r, n_c) > 0 and
                        not self.game.is_mine(n_r, n_c)):
                    surrounding = 0
                    surrounding_flagged = 0
                    for s_r, s_c in self.game.get_surrounding_cells(n_r, n_c):
                        if not self.game.is_revealed(s_r, s_c):
                            surrounding += 1
                            if self.game.is_flagged(s_r, s_c):
                                surrounding_flagged += 1

                    if surrounding == self.game.get_surrounding_count(n_r, n_c):
                        for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c):
                            if not self.game.is_revealed(b_r, b_c) and not self.game.is_flagged(b_r, b_c):
                                if (b_r, b_c) not in self.to_flag:
                                    self.to_flag.append((b_r, b_c))
                    elif surrounding_flagged == self.game.get_surrounding_count(n_r, n_c):
                        for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c):
                            if not self.game.is_revealed(b_r, b_c) and not self.game.is_flagged(b_r, b_c):
                                if (b_r, b_c) not in self.to_reveal:
                                    self.to_reveal.append((b_r, b_c))

    def complex_deduction(self, printing=True):
        probability_dict = self.construct_probability_tables()

        if 1.0 in probability_dict.values() or 0.0 in probability_dict.values():
            for cell in probability_dict.keys():
                if probability_dict[cell] == 1.0:
                    if cell not in self.to_reveal:
                        self.to_reveal.append(cell)
                if probability_dict[cell] == 0.0:
                    if cell not in self.to_flag:
                        self.to_flag.append(cell)
        else:
            best_probability = probability_dict[max(probability_dict.keys(), key=probability_dict.get)]
            best_guesses = [cell for cell in probability_dict.keys() if probability_dict[cell] == best_probability]
            if printing:
                print("GUESS WITH SUCCESS CHANCE", round(best_probability, 2))
            best_guess = random.choice(best_guesses)
            self.to_reveal.append(best_guess)

    def construct_probability_tables(self):

        # STEP 1: Make the relevant data structures.
        number_cells = self.game.get_revealed_number_cells(include_flag_neighbours=False)
        border_cells = self.game.get_unrevealed_border_cells(include_flagged=False)
        nonborder_cells = self.game.get_unrevealed_nonborder_cells()
        number_cells_dict = {n_cell: [] for n_cell in number_cells}
        border_cells_dict = {b_cell: [] for b_cell in border_cells}
        unrevealed_cell_count = len(border_cells) + len(nonborder_cells)
        remaining_mines = self.game.get_unused_flag_count()

        for n_cell in number_cells:
            n_r, n_c = n_cell
            for b_cell in self.game.get_surrounding_cells(n_r, n_c):
                if b_cell in border_cells_dict:
                    number_cells_dict[n_cell].append(b_cell)
        for b_cell in border_cells:
            b_r, b_c = b_cell
            for n_cell in self.game.get_surrounding_cells(b_r, b_c):
                if n_cell in number_cells_dict:
                    border_cells_dict[b_cell].append(n_cell)

        # Step 2: Split & Sort Cells into dependant islands.
        # O(nlog(n))
        def path_sorted(cell_list):
            if not cell_list: return tuple()
            base_row, base_column = min(cell_list)

            def d(cell):
                return abs(cell[0] - base_row) + abs(cell[1] - base_column)

            return tuple(sorted(cell_list, key=d))

        border_cells = path_sorted(border_cells)

        # O(n^2 * log(n))
        def island_split(cell_list, path_sorting=False):
            cell_list = list(cell_list)
            cell_set = set(cell_list)
            split_cell_list = []

            while cell_list:
                b_cell = cell_list.pop()
                to_add_list = [b_cell]
                to_add_set = set(to_add_list)
                cell_set.remove(b_cell)
                for cell in to_add_list:
                    for n_cell in border_cells_dict[cell]:
                        for b_cell in number_cells_dict[n_cell]:
                            if b_cell in cell_set and b_cell not in to_add_set:
                                to_add_list.append(b_cell)
                                to_add_set.add(b_cell)
                                cell_list.remove(b_cell)
                                cell_set.remove(b_cell)
                if path_sorting:
                    to_add_list = path_sorted(to_add_list)
                split_cell_list.append(tuple(to_add_list))
            split_cell_list.sort(key=len)
            return tuple(split_cell_list)

        border_cell_islands = island_split(border_cells, path_sorting=True)

        # Step 3: Calculate Mine Arrangement Possibilities.
        surrounding_mine_constraints = {(n_r, n_c): self.game.get_surrounding_count(n_r, n_c) -
                                                    len([1 for b_r, b_c in self.game.get_surrounding_cells(n_r, n_c)
                                                         if not self.game.is_revealed(b_r, b_c)
                                                         and self.game.is_flagged(b_r, b_c)])
                                        for n_r, n_c in number_cells}
        surrounding_unknown_constraints = {n_cell: len(number_cells_dict[n_cell]) for n_cell in number_cells}
        not_mine = 0
        mine = 1

        # O(2^n)
        def get_solutions(border_cell_array, surrounding_mine_constraints, surrounding_unknown_constraints,
                          current_solution, solutions, mines_used=0):
            if len(current_solution) == len(border_cell_array):
                solutions.append(current_solution.copy())
            else:
                b_cell = tuple(border_cell_array[len(current_solution)])
                for status in (mine, not_mine):

                    current_solution.append(status)
                    go_deeper = True
                    for n_cell in border_cells_dict[b_cell]:
                        surrounding_unknown_constraints[n_cell] -= 1
                        if status == mine:
                            surrounding_mine_constraints[n_cell] -= 1
                        if (surrounding_unknown_constraints[n_cell] < surrounding_mine_constraints[n_cell] or
                                surrounding_mine_constraints[n_cell] < 0):
                            go_deeper = False
                    if status == mine:
                        mines_used += 1
                    if mines_used > remaining_mines:
                        go_deeper = False

                    if go_deeper:
                        get_solutions(border_cell_array, surrounding_mine_constraints, surrounding_unknown_constraints,
                                      current_solution, solutions, mines_used)

                    if status == mine:
                        mines_used -= 1
                    for n_cell in border_cells_dict[b_cell]:
                        surrounding_unknown_constraints[n_cell] += 1
                        if status == mine:
                            surrounding_mine_constraints[n_cell] += 1
                    current_solution.pop()

        island_solutions = []
        for i, island in enumerate(border_cell_islands):
            solutions = []
            get_solutions(np.array(island), surrounding_mine_constraints, surrounding_unknown_constraints,
                          current_solution=[], solutions=solutions)
            island_solutions.append(solutions)

        # Step 4: Construct Probability Tables for Border Cells.
        def get_solution_likelihood(solution, remaining_mines=remaining_mines,
                                    unrevealed_cell_count=unrevealed_cell_count):
            result = 1
            for s in solution:
                if s == not_mine:
                    result *= (unrevealed_cell_count - remaining_mines) / unrevealed_cell_count
                elif s == mine:
                    result *= remaining_mines / unrevealed_cell_count
                    remaining_mines -= 1
                unrevealed_cell_count -= 1
            return result

        island_solution_likelihoods = [[get_solution_likelihood(s) for s in solutions]
                                       for solutions in island_solutions]

        probability_dict = {}
        for i, solutions in enumerate(island_solutions):
            normalizer_constant = sum(island_solution_likelihoods[i])
            for j, b_cell in enumerate(border_cell_islands[i]):
                probability_dict[b_cell] = sum([island_solution_likelihoods[i][s] for s, solution in
                                                enumerate(solutions) if solution[j] == not_mine])
                probability_dict[b_cell] /= normalizer_constant
                probability_dict[b_cell] = round(probability_dict[b_cell], DIGIT_ROUNDING)

        # Step 5: Add non-Border Cell probabilities to Probability Table.
        if len(nonborder_cells) > 0:
            island_mine_amounts = [tuple(sorted(set([sum(s) for s in solutions]))) for solutions in island_solutions]

            def get_mine_amount(solutions, mine_amount):
                amount = 0
                for s in solutions:
                    if sum(s) == mine_amount:
                        amount += 1
                return amount

            island_mine_probabilities = [{mine_amount: get_mine_amount(solutions, mine_amount) / len(solutions)
                                          for mine_amount in island_mine_amounts[i]}
                                         for i, solutions in enumerate(island_solutions)]

            normalizer_constant = 0
            average_border_mine_amount = 0
            for comb in itertools.product(*island_mine_amounts):
                if sum(comb) <= remaining_mines:
                    k = 1
                    for i, num in enumerate(comb):
                        k *= island_mine_probabilities[i][num]
                    normalizer_constant += k
                    average_border_mine_amount += k * sum(comb)
            average_border_mine_amount /= normalizer_constant

            nb_probability = 1 - (remaining_mines - average_border_mine_amount) / len(nonborder_cells)
            nb_probability = round(nb_probability, DIGIT_ROUNDING)
            for nb_cell in nonborder_cells:
                probability_dict[nb_cell] = nb_probability

        return probability_dict
