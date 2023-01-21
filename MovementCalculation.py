import chess
from enum import Enum
import random

# global
GOODMOVE = 2
OKMOVE = 1
BADMOVE = -1
GREATMOVE = 3
WINGAME = 10000


class MovementFactor(Enum):  # Right/Left * Defence/Attack, Rd=0, Ld=1, Ra=2, La=3
    RightDefence = 0
    LeftDefence = 1
    RightAttack = 2
    LeftAttack = 3


class MovementCalculation:

    def __init__(self, board):
        self.board = board
        if board.turn:
            color = chess.WHITE
            Opcolor = chess.BLACK
        else:
            color = chess.BLACK
            Opcolor = chess.WHITE

        self.color = color
        self.Ocolor = Opcolor
        self.pieces = None
        self.legal_moves = None
        self.weightList = None

    def get_move_from_string(self, from_square,
                             to_square):  # This function will find the move (of Move class) out of self.legal_moves that corresponds to the two args given, if such move exists.
        moves = [i for i in
                 filter(lambda move: move.to_square == to_square and move.from_square == from_square, self.legal_moves)]
        return None if len(moves) == 0 else moves[0]

    def inc_ListWeight(self, listM, num):
        for i in listM:
            if i in self.legal_moves:
                index_wight = (self.legal_moves).index(i)
                self.wightList[index_wight] += num

    def inc_MoveWeight(self, move, num):
        if move in self.legal_moves:
            self.weightList[(self.legal_moves).index(move)] += num

    def makeMove(self, startSq, endSq):  # create move
        return chess.Move.from_uci(chess.square_name(startSq) + chess.square_name(endSq))

    def check_IfYourPiece(self, square):
        if (self.board).color_at(square) == self.color:
            return True
        return False

    def not_defendedPiece(self, square):
        co = self.board.color_at(square)
        if len(self.board.attackers(co, square)) > 0:
            return True
        return False

    def good_trade(self, myPieceSquare):
        # chess.Board.piece_at
        piece1 = (self.board.piece_at(myPieceSquare)).piece_type
        # protected attacks
        List_attacks = self.board.attacks(myPieceSquare)  # squares piece attacks
        positive_targetL = []  # squares we should attack
        for i in List_attacks:
            if self.board.piece_at(i) and self.board.color_at(i):
                piece2 = (self.board.piece_at(i)).piece_type
                if piece1 <= piece2 or self.not_defendedPiece(i):
                    positive_targetL.append(i)
        return positive_targetL

        # should capture->piece worth as much/more Or piece is not defended

    def pawn_protector(self, square):
        list_pawn_attacked = self.board.attacks(square)
        listprotected = []
        for i in list_pawn_attacked:
            # check if i is your piece
            if self.check_IfYourPiece(i):
                # check if you are the only protector and if it is under attack
                if len(self.board.attackers(self.Ocolor, i)) >= len(self.board.attackers(self.color, i)) - 1:
                    # good_trade checks if piece can capture another that is worth as much
                    listprotected.append(i)

        return listprotected

        # ======================================== Guy added functions START ========================================

    def initialize(self):  # Initalize the weight list according to the legal moves (without non-queen promotions).
        self.pieces = self.board.pieces(chess.PAWN, self.color)
        self.legal_moves = self.filter_non_queen_promotions()
        self.weightList = [5] * len(self.legal_moves)

    def filter_non_queen_promotions(self):  # Gets a list (not iterable) of all legal moves with not non-queen promotion
        return [i for i in
                filter(lambda move: move.promotion == chess.QUEEN or move.promotion is None, self.board.legal_moves)]

    def calculate_next_move(self,
                            geno_val):  # Main function that will be used by Communicator, will receive the individual's genotype for the appropriate move.
        mirrored = False

        if (self.color == chess.BLACK):
            mirrored = True
            self.board.apply_mirror()
            self.color = chess.WHITE
            self.Ocolor = chess.BLACK

        self.initialize()
        self.bonus_weights_for_geno(geno_val)  # increases weight for all moves related to the geno_val value.

        i = 0
        for move in self.legal_moves:

            piece_type = self.board.piece_at(move.from_square).piece_type
            if piece_type == chess.PAWN:
                self.calculate_pawn_move(move, i)
            elif piece_type == chess.QUEEN:
                self.calculate_queen_move(move, i)
            elif piece_type == chess.KING:
                self.calculate_king_move(move, i)
            # TODO add more pieces logic?
            i += 1
        self.checkingCheckOption()
        self.king_in_danger()
        self.buildPawnStructure()
        self.king_move_to_protect()
        # Choose the next move with the updated weights
        chosen_move = random.choices(self.legal_moves, weights=self.weightList, k=1)[0]
        if mirrored:  # TODO maybe just have a boolean value for if the board should be mirrored or not, self.color will always be white...
            str = chess.square_name(chess.square_mirror(chosen_move.from_square)) + chess.square_name(
                chess.square_mirror(chosen_move.to_square))
            str = str + 'q' if chosen_move.promotion == chess.QUEEN else str  # Only promotions to queen are allowed.
            chosen_move = chess.Move.from_uci(str)
            self.board.apply_mirror()
            self.color = chess.BLACK
            self.Ocolor = chess.WHITE
            return chosen_move
        return chosen_move

    def calculate_pawn_move(self, pawn_move, i):  # TODO insert all weight-changing functions related to pawn here
        self.advances_of_pawn(pawn_move, i)
        self.PawncaptureAnotherPiece(pawn_move)

    def calculate_queen_move(self, queen_move, i):  # TODO insert all weight-changing functions related to queen here
        self.queenMove(queen_move)

    def calculate_king_move(self, king_move, i):  # TODO insert all weight-changing functions related to king here
        self.kingMove(king_move)

    def advances_of_pawn(self, pawn_move, i):  # change
        num = 0
        # chess.square_distance, chess.king(king_color)

        pawn_pos = pawn_move.from_square
        pawn_to_pos = pawn_move.to_square

        if len(self.enemies_blocking_route(pawn_pos)) > 2 or chess.square_distance(pawn_to_pos,
                                                                                   self.board.king(self.Ocolor)) < 3:
            num += BADMOVE

        elif len(self.enemies_blocking_route(pawn_pos)) > 0:
            if chess.square_distance(pawn_to_pos, self.board.king(self.Ocolor)) < 2:
                num += BADMOVE
            else:
                closest = self.enemies_blocking_route(pawn_pos)[0]
                if (self.get_row(self.board.king(self.color)) == self.get_row(closest)):
                    if pawn_pos == max(self.pieces):
                        if (chess.square_distance(pawn_to_pos, self.board.king(self.Ocolor)) > 8 - self.get_row(
                                pawn_pos)):
                            num += GOODMOVE + self.advancing_bonus(pawn_pos) + GOODMOVE

                    num += GOODMOVE
                elif (self.board.king(self.color) % 8 == self.get_row(closest) % 8 and self.get_row(
                        self.board.king(self.color)) < self.get_row(closest)):
                    num += BADMOVE



        elif pawn_to_pos == pawn_pos + 16:  # pawn_pos is in second raw and is moving 2 blocks
            if (not self.is_cornered_to_left(pawn_pos)):

                if self.board.color_at(pawn_pos + 15) != self.Ocolor:  # occupied by team piece
                    num += OKMOVE
                else:
                    num += BADMOVE  # occupied by enemy piece

                if self.board.color_at(pawn_pos + 7) == self.Ocolor:  # en passant danger
                    num += BADMOVE

            if (not self.is_cornered_to_right(pawn_pos)):

                if self.board.color_at(pawn_pos + 17) != self.Ocolor:
                    num += OKMOVE
                else:
                    num += BADMOVE
                if self.board.color_at(pawn_pos + 9) == self.Ocolor:  # en passant danger
                    num += BADMOVE


        elif (pawn_move.promotion == chess.QUEEN):
            if (chess.square_distance(pawn_to_pos, self.board.king(self.Ocolor)) > 1):
                num += WINGAME
            elif (len(self.pawn_protector(pawn_to_pos)) > 0):
                num += WINGAME
            else:
                num += BADMOVE

        else:
            if (not self.is_cornered_to_left(pawn_pos)):

                if self.get_row(pawn_pos) < 8 and self.board.color_at(pawn_pos + 7) == self.color:
                    num += GREATMOVE
                if self.get_row(pawn_pos) < 7 and self.board.color_at(pawn_pos + 15) == self.Ocolor:
                    num += BADMOVE

            if (not self.is_cornered_to_right(pawn_pos)):

                if self.get_row(pawn_pos) < 8 and self.board.color_at(pawn_pos + 9) == self.color:
                    num += GREATMOVE
                if self.get_row(pawn_pos) < 7 and self.board.color_at(pawn_pos + 17) == self.Ocolor:
                    num += BADMOVE
            if (chess.square_distance(pawn_to_pos, self.board.king(self.Ocolor)) > 8 - self.get_row(
                    pawn_pos)): num += GOODMOVE + self.advancing_bonus(pawn_pos)

        self.weightList[i] += num

    def advancing_bonus(self, pawn_pos):
        return max(0, self.get_row(pawn_pos) - 3) * 2  # No bonues till getting to fifth row

    def enemies_blocking_route(self, pawn_pos):
        arr = []
        i = 8
        while (pawn_pos + i < 64):
            if (self.board.color_at(pawn_pos + i) == self.Ocolor): arr.append(pawn_pos + i)
            i += 8
        return arr

    def get_row(self, pos):
        return int(pos / 8) + 1  # int(0/8) +1 = 1 <= row <= int(63/8) +1 = 8

    def is_left_side(self, pos):
        return pos % 8 < 4

    def is_right_side(self, pos):
        return not self.is_left_side(pos)

    def is_cornered_to_left(self, pos):
        return pos % 8 == 0

    def is_cornered_to_right(self, pos):
        return pos % 8 == 7

    def is_attacking_move(self, move):
        return self.get_row(move.from_square) <= self.get_row(move.to_square)

    def is_defending_move(self, move):
        return self.get_row(move.from_square) >= self.get_row(move.to_square)

    def bonus_weights_for_geno(self, geno_val):

        func = lambda mov: False
        if (geno_val == MovementFactor.RightDefence):
            func = lambda mov: self.is_right_side(mov.to_square) and self.is_defending_move(mov)
        elif (geno_val == MovementFactor.LeftDefence):
            func = lambda mov: self.is_left_side(mov.to_square) and self.is_defending_move(mov)
        elif (geno_val == MovementFactor.RightAttack):
            func = lambda mov: self.is_right_side(mov.to_square) and self.is_attacking_move(mov)
        elif (geno_val == MovementFactor.LeftAttack):
            func = lambda mov: self.is_left_side(mov.to_square) and self.is_attacking_move(mov)

        filtered_moves = filter(func, self.legal_moves)
        for move in filtered_moves:
            self.weightList[self.legal_moves.index(move)] += GOODMOVE

    def count_attacking_pieces(self, square, turn):
        # Find all the squares that attack the given square
        attacking_squares = []
        for square in chess.SQUARES:
            if self.board.is_attacked_by(not self.color, square):
                attacking_squares.append(square)

        return len(attacking_squares)

    def check_mateIn2(self):
        if 1 <= chess.get_dtm(self.board) <= 3:
            legalcheck = self.board.legal_moves
            OPKsquare = chess.Board.king(self.Ocolor)

    def gives_mate(self, move):
        moveForPush = chess.Move.from_uci(move.uci())
        self.board.push(moveForPush)
        is_move_mate = self.board.is_checkmate()
        self.board.pop()
        if is_move_mate:
            return True  # TODO exit  movement with move
        else:
            return False

    def list_of_legal_moves(self):  # Gets a list (not iterable) of all legal moves with not non-queen promotion
        return [i for i in filter(lambda move: move, self.board.legal_moves)]

        # get check moves.than check if giving check puts my piece in danger if yes can i negate danger by capture(good trade)

    def checkingCheckOption(self):
        OKingSquare = self.board.king(self.Ocolor)

        legalMoveList = self.list_of_legal_moves()
        checkMove = filter(self.board.gives_check, legalMoveList)  # TODO check how to get array of moves

        for move in checkMove:
            if self.gives_mate(move):
                self.inc_MoveWeight(move, WINGAME)
                # might want to end here return True TODO

            # check if safty of attacking piece
            # if self.count_attacking_pieces(move.to_square,self.color) < self.count_attacking_pieces(move.to_square,self.Ocolor):
            if (self.color != 0 and self.color != 1): print("fuck1")
            if (self.Ocolor != 0 and self.Ocolor != 1): print("fuck2")
            if len(self.board.attackers(self.color, move.to_square)) < len(
                    self.board.attackers(self.Ocolor, move.to_square)):
                # check saftey of defended piece
                protecting = self.pawn_protector(move.from_square)
                check_all_Protected = []
                if len(protecting) > 0:
                    for i in protecting:
                        if self.good_trade(i):
                            check_all_Protected.append(True)
                        else:
                            check_all_Protected.append(False)
                if all(check_all_Protected):
                    self.inc_MoveWeight(move, GREATMOVE)
                else:
                    true_count = sum([1 for x in check_all_Protected if x])
                    if true_count / len(check_all_Protected) > 0.5:
                        self.inc_MoveWeight(move, OKMOVE)

    # def coverdSquare (square):
    #     if chess.attack_ers()

    # check back row

    def backRow_king(self, backrow):
        return True if self.board.king(self.color) == backrow else False

    def Opawn_closeToPromote(self, backRow):
        def pRow(psquare):
            OpawnCloseToPromote = []
            for i in range(8, 17):
                if self.board.color_at(i) == self.Ocolor:
                    if self.board.piece_type_at(i) == chess.PAWN:
                        OpawnCloseToPromote.append(i)
            return OpawnCloseToPromote

    def squareOcuppied(self, list):  # check if square is occupied by your piece or attacked by enemy TODO
        ocupiedlist = []
        for i in list:
            if self.board.piece_at(i) or self.board.is_attacked_by(self.Ocolor, i):
                ocupiedlist.append(True)
        return all(ocupiedlist)
        # p = self.piece_at(i)
        # check if piece is pawn

    def piece_can_move(self, pref):  # not in use
        pieceMoves = []
        for s in self.legal_moves:
            if s.from_square == pref:
                pieceMoves.append(s)
        return pieceMoves

    def king_in_danger(self):
        MyKsquare = self.board.king(self.color)
        if self.color == chess.WHITE:
            backRow = 1
        else:
            backRow = 8

        if self.board.is_check():
            return True
        # check is there a pawn or queen that can get to back row
        danger_piece1Move = self.Opawn_closeToPromote(backRow)
        if danger_piece1Move and len(danger_piece1Move) == 1 and chess.square_distance(danger_piece1Move[0],
                                                                                       MyKsquare) > 2:
            if backRow == 1:

                if MyKsquare == 1:
                    if self.squareOcuppied([MyKsquare + 8, MyKsquare + 9]):
                        self.Find_king_escape(danger_piece1Move)
                elif MyKsquare == 8:
                    if self.squareOcuppied([MyKsquare + 8, MyKsquare + 7]):
                        self.Find_king_escape(danger_piece1Move[0])
                else:
                    if self.squareOcuppied([MyKsquare + 8, MyKsquare + 7, MyKsquare + 9]):
                        self.Find_king_escape(danger_piece1Move[0])

                # case 8:#black case TODO
                #     if danger_piece1Move and len(danger_piece1Move) == 1 and chess.square_distance(danger_piece1Move[0],MyKsquare) <= 2:
            # need to find move to danger piece

            # check king traped back row 3 cases
            # both squares attacked and closed but at least on can capture and open escape
            # one square can move and give king escape
            # all escapes are closed  both pawns are under attack and king cant escape

            # if backRow == 1 :
            #     if MyKsquare == 1 and self.squareOcuppied([MyKsquare+8,MyKsquare+9])

            return True

        def second_raw_check(num):  # check if square in second raw
            if 8 < num < 16:
                return True
            return False

        def Find_king_escape(EnemyPiecesquare):  # enemy about to promote and mate you
            def king_run():
                if chess.square_distance(EnemyPiecesquare, MyKsquare) > 3:
                    if MyKsquare < (EnemyPiecesquare % 8):
                        if self.KLeft_escape():
                            self.KRight_escape()

                    elif self.KRight_escape():
                        self.KLeft_escape()

                    # escape_squares():
                    def KLeft_escape():  # find move king left and increase its probabilty
                        if second_raw_check(MyKsquare + 6) and not self.squareOcuppied[MyKsquare + 6]:

                            KLmove = chess.Move.from_uci(
                                chess.square_name(MyKsquare) + chess.square_name(MyKsquare - 1))
                            if KLmove in self.legal_moves:
                                self.inc_MoveWeight(KLmove, GREATMOVE)
                                return True

                        return False

                    def KRight_escape():  # find move king right and increase its probabilty
                        if second_raw_check(MyKsquare + 10) and not self.squareOcuppied[MyKsquare + 10]:

                            KLmove = chess.Move.from_uci(
                                chess.square_name(MyKsquare) + chess.square_name(MyKsquare + 1))
                            if KLmove in self.legal_moves:
                                self.inc_MoveWeight(KLmove, GREATMOVE)
                                return True

                        return False

            ##**functions for piece_move_for_escape
            def move_capture(move):  # gets move and checks if it is a capture

                if self.board.is_capture(move):
                    return move

            def incCaptureWightFirst(pieceMoves):  # inc wight to capture or move farward

                captures = filter(move_capture(), pieceMoves)
                if captures:
                    self.inc_ListWeight(captures, GOODMOVE)
                else:
                    self.inc_ListWeight(pieceMoves, OKMOVE)

            ##**
            def piece_move_for_escape():  # check if can open escape by by moving piece that blocks the king

                if MyKsquare == 1:
                    for i in range(2):
                        pieceMoves = self.piece_can_move((MyKsquare + 8 + i))
                        incCaptureWightFirst(pieceMoves)
                elif MyKsquare == 1:
                    for i in range(2):
                        pieceMoves = self.piece_can_move((MyKsquare + 7 + i))
                        incCaptureWightFirst(pieceMoves)
                else:
                    for i in range(3):
                        pieceMoves = self.piece_can_move((MyKsquare + 7 + i))
                        incCaptureWightFirst(pieceMoves)

            king_run()
            piece_move_for_escape()

        # 1.control space if you can be defended
        # 2.advance to protect another pawn

    def buildPawnStructure(self):

        pawnSquareList = self.board.pieces(chess.PAWN, self.color)
        for i in pawnSquareList:
            if not self.board.piece_at(i):
                self.pawncontrolSpace(i)
                self.pawnAdvanceToDefend(i, i + 8)

        def supportPawn(square):
            if (square + 1) in pawnSquareList or (square - 1) in pawnSquareList:
                return True
            else:
                return False

        def centerPawn(square):
            if 3 < (square % 8) < 6:
                return True
            else:
                return False

        def pawncontrolSpace(square):

            if 8 < square < 17:
                if self.notAttcakedSquare(square + 8) and self.notAttcakedByOSquare(square + 16):
                    move = self.makeMove(square, square + 16)

                    if supportPawn(square):
                        self.inc_MoveWeight(move, GOODMOVE)

                    else:
                        if centerPawn(square) or defendedsquare(square + 16): self.inc_MoveWeight(move, OKMOVE)

                if self.notAttcakedSquare(square + 8):
                    pawnAdvanceToDefend(square, square + 16)  # part of pawnAdvanceToDefend but in second raw

            else:
                move = chess.Move.from_uci(chess.square_name(square) + chess.square_name(square + 8))
                if self.notAttcakedSquare(square + 8) and defendedsquare(square + 8):
                    self.inc_MoveWeight(move, OKMOVE)

        def pawnAdvanceToDefend(startSq,
                                endSq):  # 1.defend and not attacked.2.defened and attacked at the same time (need to also be defended)
            if defendsAnotherPiece(endSq) and (notAttcakedByOSquare(endSq) or defendedsquare(endSq)):
                self.inc_MoveWeight(self.makeMove(startSq, endSq))

        def defendsAnotherPiece(sq):  # check if square defends another piece
            sqAtt = PwouldBeAttackedSq(sq)
            if sqAtt:
                for i in sqAtt:
                    if self.board.color_at(i) == self.color:
                        return True
            return False

        def notAttcakedByOSquare(designatedSquare):
            return not self.board.is_attacked(self.Ocolor, designatedSquare)

        def defendedsquare(square):
            return self.board.is_attacked(self.color, square)

        # check if pawn attacks within board and return them
        def PwouldBeAttackedSq(square):
            attackedSq = []
            if 8 < square + 7 < 64:
                attackedSq.append(square + 7)
            if 8 < square + 9 < 64:
                attackedSq.append(square + 9)
            return attackedSq

        # check most farward pawn that is not protected or pawn that is past 6 row

    def king_move_to_protect(self):
        MyKsquare = self.board.king(self.color)

        def KmoveDirection(PawnSq):
            if PawnSq % 8 < MyKsquare % 8:
                if PawnSq > MyKsquare:
                    return [MyKsquare - 1, MyKsquare + 7, MyKsquare + 8]

            if PawnSq % 8 > MyKsquare % 8:
                if PawnSq > MyKsquare:
                    return [MyKsquare + 1, MyKsquare + 9, MyKsquare + 8]

            else:
                if PawnSq > MyKsquare:
                    return [MyKsquare + 8]
            return []

        pawnSq = self.pieces
        advancedPawns = filter(lambda a: a > 40, pawnSq)
        notprotected = filter(lambda a: not self.board.is_attacked_by(self.color, a), advancedPawns)

        if notprotected:
            for i in notprotected:
                KMSq = KmoveDirection(i)
                if KMSq:
                    for j in KMSq:
                        self.inc_MoveWeight(self.makeMove(MyKsquare, j), OKMOVE)

        # need to check statistic if should capture

    def PawncaptureAnotherPiece(self, move):
        if self.board.is_capture(move):
            if self.board.piece_type_at(move.to_square) is not None and self.board.piece_type_at(move.to_square) > 1:
                self.inc_MoveWeight(move, GOODMOVE)

            else:
                self.inc_MoveWeight(move, OKMOVE)

    def queenMove(self, move):
        QTS = move.to_square
        if not self.board.is_attacked_by(self.Ocolor, QTS):
            if self.board.gives_check(move):
                self.inc_MoveWeight(move, GOODMOVE)
            else:
                self.inc_MoveWeight(move, OKMOVE)
        else:
            self.inc_MoveWeight(move, BADMOVE)

    def kingMove(self, move):

        if move.from_square < move.to_square:
            self.inc_MoveWeight(move, OKMOVE)
        # move in direction of close saperated pawn