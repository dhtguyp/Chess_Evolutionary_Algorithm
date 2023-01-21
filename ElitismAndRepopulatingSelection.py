from eckity.genetic_operators.selections.selection_method import SelectionMethod
import random

class ElitismAndRepopulatingSelection(SelectionMethod): #A selection class that also fills back the sub population with the elites selected.
    def __init__(self, num_elites, higher_is_better=True, events=None):
        super().__init__(events=events, higher_is_better=higher_is_better)
        self.num_elites = num_elites
        self.higher_is_better = higher_is_better

    def select(self, source_inds, dest_inds):
        if(self.num_elites == 0):
            self.selected_individuals = source_inds
            dest_inds = source_inds
            return dest_inds


        amm_pop = len(source_inds)
        elites = sorted(source_inds,
                        key=lambda ind: ind.get_augmented_fitness(),
                        reverse=True)[:self.num_elites]

        for i in range(amm_pop):
            clone_ind = random.choice(elites).clone() #Pick a random individual out of the elites and clone it
            clone_ind.update_id()
            if(clone_ind.fitness.is_fitness_evaluated()): clone_ind.fitness.set_not_evaluated()
            dest_inds.append(clone_ind)
        self.selected_individuals = dest_inds
        # TODO shouldn't it be after_operator? why is this needed?
        # self.publish("after_selection")
        return dest_inds
