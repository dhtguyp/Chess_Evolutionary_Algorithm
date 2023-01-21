# This is a sample Python script.
import sys
import time

import chess
import chess.engine
from geno_2 import MovementCalculation, MovementGenotype
from eckity.fitness.simple_fitness import SimpleFitness
from BoardIndividual import BoardIndividual


# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def printFunc(board):
    print(f"\n\n{'white' if board.turn else 'black'}'s turn")
    print(board)


def main():
    player_turn = False # Can choose whether the player starts first or the engine with a boolean value in 2nd arg.

    FEN1 = "8/pppppP1p/3k2p1/8/8/8/PPPPP1PP/4K3 w - - 0 1"
    FEN = "3k4/ppppp2p/8/8/8/4K3/PPPPPPpP/8 w - - 0 1"
    ind = BoardIndividual(FEN=FEN, fitness=SimpleFitness(higher_is_better=True), is_white=player_turn)
    board = ind.board

    engine = chess.engine.SimpleEngine.popen_uci(r"src/stockfish_15.1_linux_x64_avx2/stockfish-ubuntu-20.04-x86-64-avx2")

    limit = chess.engine.Limit(depth = 6) #experiment with depth instead of time.
    player_input = None
    mov_calc = ind.movement

    while not board.is_game_over():
        printFunc(board)
        if player_turn:
            player_input = input("\nCalculate move, press any button to continue, 'q' to stop")
            if player_input == 'q': break

            player_input = mov_calc.calculate_next_move(-1) #TODO uncomment previous line, delete this line.
            board.push(player_input)
            print(player_input.uci())
            player_turn = not player_turn


        else:
            result = engine.play(board, limit)  # stockfish calculation and move
            board.push(result.move)
            player_turn = not player_turn

    engine.close()
    print("\n\ndone")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
