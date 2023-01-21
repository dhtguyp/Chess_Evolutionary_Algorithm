import sys
import logging
import time
from BoardCreator import BoardCreator
from Communicator import Communicator
from overrides import overrides
from BoardEvolution import BoardEvolution
from MutateStrategyFactor import MutateStrategyFactor
from eckity.breeders.simple_breeder import SimpleBreeder
from ElitismAndRepopulatingSelection import ElitismAndRepopulatingSelection
from eckity.statistics.best_average_worst_statistics import BestAverageWorstStatistics
from eckity.subpopulation import Subpopulation
from eckity.evaluators.simple_individual_evaluator import SimpleIndividualEvaluator
from ChessTerminationChecker import ChessTerminationChecker
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

class BoardEvaluator(SimpleIndividualEvaluator):

    def __init__(self, FEN, communicator):
        super().__init__()
        self.FEN= FEN
        self.communicator = communicator

    @overrides
    def _evaluate_individual(self, individual):
        return self.communicator.send_evaluation_request(ind=individual)




def main(): #main may accept arguments in such order: [{0-black, 1-white}, Fen1,...,Fen7], where FEN =Fen1,...,Fen7 is a FEN representation of a chess board

    start = time.time() #timer


    FEN = "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1" #Default board, with only kings and pawns.
    alg_is_white = FEN.split()[1] == 'w'


    n = len(sys.argv)
    if  1 < n < 8: # There is a FEN representation given in argv
        alg_is_white = sys.argv[2] == 'w'
        FEN = (' '.join(sys.argv[1:]))

    logging.error(f"FEN inserted is: {FEN}\n\n")
    alg_start = True # Will always start first
    is_stalemate_good = True
    calculation_depth = 9 #In each generation, all boards make 6 moves - 3 of the algorithm, 3 of the engine, which calculates with the depth inserted here.
    evaluation_depth = 9 #After each generation the algorithm checks all boards and evaluates the fitness, related to the score of the alg's color.
    amm_engines = 10 # Number of engines being used by the algorithm as well as communicator
    amm_pop = 200
    max_iter = 30
    elitism_rate = 0.01
    alg_depth = 6 #How many moves are made in every generation
    cutoff = 0.5 # Odds of any individual changing it's dependence on MovementCalculation.
    num_elites = int(amm_pop * elitism_rate)
    communicator = Communicator(is_starting=alg_start,
                                is_stalemate_good=is_stalemate_good,
                                alg_depth = alg_depth,
                                calculation_depth=calculation_depth,
                                evaluation_depth=evaluation_depth,
                                amm_engines=amm_engines,
                                amm_pop=amm_pop,
                                engine_file="stockfish_15.1_linux_x64_avx2/stockfish-ubuntu-20.04-x86-64-avx2")


    # Initialize the evolutionary algorithm
    algo = BoardEvolution(
        Subpopulation(creators=BoardCreator(FEN=FEN, is_white=alg_is_white, depth=alg_depth),
                      population_size=amm_pop,
                      # user-defined fitness evaluation method
                      evaluator=BoardEvaluator(FEN, communicator),
                      # maximization problem (fitness is sum of values), so higher fitness is better
                      higher_is_better=True,
                      elitism_rate=0,
                      # genetic operators sequence to be applied in each generation
                      operators_sequence=[
                          MutateStrategyFactor(probability=1, arity=1, probability_cutoff=cutoff)
                      ],
                      selection_methods=[
                          # (selection method, selection probability) tuple
                          [ElitismAndRepopulatingSelection(num_elites=num_elites, higher_is_better=True), 1]  #Only this elitism will work
                      ]
                      ),
        communicator=communicator,
        breeder=SimpleBreeder(),
        max_generation=max_iter,
        termination_checker=ChessTerminationChecker(),
        statistics=BestAverageWorstStatistics()
    )

    algo.evolve()

    #logging.error("closing_engines...")
    communicator.close_engines()

    print(f"Evolutionary algorithm done in {int(time.time() - start)} seconds.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

