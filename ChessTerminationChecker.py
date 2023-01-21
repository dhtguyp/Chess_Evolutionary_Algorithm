from abc import abstractmethod
import functools
class ChessTerminationChecker:
    """
    Abstract TerminationChecker class.

    This class is responsible of checking if the evolutionary algorithm should perform early termination.
    This class can be expanded depending on the defined termination condition.
    For example - threshold from target fitness, small change in fitness over a number of generations etc.
    """

    def should_terminate(self, population, best_individual, gen_number):
        """
        Determines if the algorithm should perform early termination.

        Parameters
        ----------
        population: Population
            The population of the experiment.

        best_individual: Individual
            The best individual in the current generation of the algorithm.

        gen_number: int
            Current generation number.

        Returns
        -------
        bool
            True if the algorithm should terminate early, False otherwise.
            THe algorithm will terminate early if either 1. There exists a board in which the algorithm won.
            2. Every single individual lost.
        """
        #TODO add reduce that checks whether all boards have ended in stalemate

        if functools.reduce(lambda y, ind: y and ind.board.is_game_over(), population.sub_populations[0].individuals, True): return True

        return best_individual.fitness.get_pure_fitness() > 99999 or best_individual.fitness.get_pure_fitness() < -99999