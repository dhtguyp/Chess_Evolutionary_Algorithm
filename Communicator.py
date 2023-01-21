import multiprocessing
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import chess
import chess.engine
import logging
from multiprocessing import Pool, Value

class Communicator:

    def __init__(self, is_starting=True, is_stalemate_good=False, alg_depth=6,  calculation_depth=10, evaluation_depth=20, amm_engines=10, amm_pop=100, engine_file="src/stockfish_15.1_linux_x64_avx2/stockfish-ubuntu-20.04-x86-64-avx2"):
        self.is_stalemate_good = is_stalemate_good
        self.done = 0
        self.calculation_limit = chess.engine.Limit(depth = calculation_depth)
        self.evaluation_limit = chess.engine.Limit(depth = evaluation_depth)
        self.count = amm_engines
        self.population = amm_pop
        self.engines = [chess.engine.SimpleEngine.popen_uci(engine_file) for _ in range(amm_engines)]
        self.single_pool = ThreadPoolExecutor(1) #A pool of one thread dedicated for genotype calculation, in order to let the algo's threadpool to swiftly communicate with the engines
        self.is_starting = is_starting # 1 for algo's turn to go first, 0 for engines' turn.
        self.alg_depth=alg_depth
        self.caller = None
    def initialize_movements_done(self, caller):
        self.done = 0
        self.caller = caller

    def send_evaluation_request(self, ind): # In the evaluation, the algorithm will do it's first of the 3 moves and let stockfish do it's move as well.
        if(ind.move_num == 0): #First evaluation only, all boards are the same.
            return 0

        engine = self.engines.pop(0)
        info = engine.analyse(ind.board, limit=self.calculation_limit) #else we calculate the ongoing board's fitness.
        self.engines.append(engine)
        score = info["score"].white().score(mate_score=100000)
        #logging.error(f"finished evaluating board no.{ind.id}")
        return score if ind.is_white else -score;

    def send_move_request(self, ind, threadpool): # id used for logging purposes
        board = ind.board
        ind.movement.board = ind.board
        def algorithm_calculation(iter):
            if not board.is_game_over():
                if iter < self.alg_depth:
                    ind.move_num += 1
                    move = ind.movement.calculate_next_move(ind.bonus_arr[ int( (iter-1)/2) ] )
                    board.push(move)
                    ind.insert_move_to_stack(move)
                    threadpool.submit(engine_communicate, iter + 1)

                else:
                    self.done += 1
                    #logging.error(f"finished calculation for algorithm in ind. no {ind.id} in iteration {self.alg_depth}")
                    if self.done == self.population:
                        #logging.error(f"{self.alg_depth} turns finished across all boards.")
                        self.caller.set()

            else:
                self.done += 1
                if self.done == self.population:
                    #logging.error(f"{self.alg_depth} turns finished across all boards.")
                    self.caller.set()

            #logging.error(f"finished alg calculation for {ind.id} in iteration {iter}")
        def engine_communicate(iter):
            if not board.is_game_over():
                limit = self.calculation_limit if iter % 2 == 0 else self.evaluation_limit #Our side's has better depth.

                ind.move_num += 1
                engine = self.engines.pop(0)
                move = engine.play(board, limit).move #blocking method, for self.duration seconds
                self.engines.append(engine)
                board.push(move)
                ind.insert_move_to_stack(move)


            self.single_pool.submit(algorithm_calculation, iter + 1)
            #logging.error(f"finished engine calculation {ind.id} in iteration {iter}")
            #finish def

        self.single_pool.submit(algorithm_calculation, 1)


    def close_engines(self):
        for engine in self.engines:
            engine.close();
        self.single_pool.shutdown()
