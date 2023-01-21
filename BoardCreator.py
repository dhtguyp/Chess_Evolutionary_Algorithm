import sys

from eckity.creators.creator import Creator
from eckity.fitness.simple_fitness import SimpleFitness
from BoardIndividual import BoardIndividual
import chess


class BoardCreator(Creator):
    def __init__(self,
                 events=None,
                 is_white=True,
                 depth=6,
                 FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        if events is None:
            events = ["after_creation"]

        super().__init__(events)
        self.created_individuals=None
        self.type = BoardIndividual
        self.FEN = FEN
        self.is_white=is_white
        self.depth=depth


    def create_individuals(self, n_individuals, higher_is_better):
        individuals = [self.type(FEN=self.FEN,
                                 fitness=SimpleFitness(higher_is_better=higher_is_better),
                                 is_white=self.is_white,
                                 depth=self.depth) for i in range(n_individuals)]
        self.created_individuals = individuals
        return individuals
