from eckity.individual import Individual
from eckity.fitness.fitness import Fitness
from MovementCalculation import MovementCalculation, MovementFactor

import random
import chess






class BoardIndividual(Individual):
    counter = 0 # First population is irrelevant to the overall calculation.
    list_of_mov_fact = [MovementFactor.RightDefence, MovementFactor.LeftDefence, MovementFactor.RightAttack, MovementFactor.LeftAttack]
    def __init__(self, FEN, fitness: Fitness, is_white=True, depth=6):
        self.FEN = FEN
        self.fitness = fitness
        self.board = chess.Board(FEN)
        self.temp_board = chess.Board(FEN)
        self.id = BoardIndividual.counter % 200
        BoardIndividual.counter += 1
        self.is_white=is_white
        self.depth = int(depth / 2)
        self.bonus_arr = [random.choice(BoardIndividual.list_of_mov_fact) for _ in range(self.depth)] #Randomly decided the genotype at the start - 3 choices of 'strategies'
        self.move_num = 0
        self.move_stack = []
        self.movement = MovementCalculation(self.board)


    def insert_move_to_stack(self, move):
        self.move_stack.append(move)
    def update_id(self):
        self.id = BoardIndividual.counter
        BoardIndividual.counter = (BoardIndividual.counter + 1) % 200
    def change_strategy_factor(self):
        self.bonus_arr = [random.choice(BoardIndividual.list_of_mov_fact) for _ in range(self.depth)]
    def get_augmented_fitness(self):
        return self.fitness.get_augmented_fitness(self)
    #
    def show(self):
        print(self.board)
        print(f"FEN representation of the board is {self.FEN}")
        print(f"Moves were: {' '.join([move.uci() for move in self.move_stack])}")
        print(f"alg finished in {self.move_num} moves.")
