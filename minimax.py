import copy
import time
import unittest

class Game:
    def __init__(self):
        self.initialize_game()

    def initialize_game(self):
        self.current_state = [[ ' ', ' ', ' ', ' ', ' ' ],
                              [ ' ', '.', '.', '.', ' ' ],
                              [ ' ', '.', '.', '.', ' ' ],
                              [ ' ', '.', '.', '.', ' ' ],
                              [ ' ', ' ', ' ', ' ', ' ' ]]

    def copy(self, other):
        self.current_state = copy.deepcopy(other.current_state)
        self.human_symbol = other.human_symbol
        self.computer_symbol = other.computer_symbol

    def set_human(self, symbol):
        self.human_symbol = symbol
        self.computer_symbol = self.get_enemy(self.human_symbol)

    def show(self, board = None):
        if not board:
            board = self.current_state
        for i in range(0, 5):
            for j in range(0, 5):
                print('{}|'.format(board[i][j]), end=" ")
            print()
        print()

    def is_valid(self, px, py, force=False):
        if not force and (px < 0 or px > 2 or py < 0 or py > 2):
            return False
        if self.current_state[py+1][px+1] == '.':
            return True
        if force and self.current_state[py+1][px+1] == ' ':
            return True
        return False

    # Checks if the game has ended.
    # If yes, returns (winner, type, number)
    # Else returns None
    def game_over(self):
        # Vertical win
        for i in range(0, 3):
            if (self.current_state[0+1][i+1] != '.' and
                self.current_state[0+1][i+1] == self.current_state[1+1][i+1] and
                self.current_state[1+1][i+1] == self.current_state[2+1][i+1]):
                return (self.current_state[0+1][i+1], 'V', i)

        # Horizontal win
        for i in range(0, 3):
            if (self.current_state[i+1][1:4] == ['X', 'X', 'X']):
                return ('X', 'H', i)
            elif (self.current_state[i+1][1:4] == ['O', 'O', 'O']):
                return ('O', 'H', i)

        # Main diagonal win
        if (self.current_state[0+1][0+1] != '.' and
            self.current_state[0+1][0+1] == self.current_state[1+1][1+1] and
            self.current_state[0+1][0+1] == self.current_state[2+1][2+1]):
            return (self.current_state[0+1][0+1], 'D', 0)

        # Second diagonal win
        if (self.current_state[0+1][2+1] != '.' and
            self.current_state[0+1][2+1] == self.current_state[1+1][1+1] and
            self.current_state[0+1][2+1] == self.current_state[2+1][0+1]):
            return (self.current_state[0+1][2+1], 'D', 1)

        # Is whole board full?
        for i in range(0, 3):
            for j in range(0, 3):
                # There's an empty field, we continue the game
                if (self.current_state[i+1][j+1] == '.'):
                    return None

        # It's a tie!
        return ('.', None, None)

    def get_enemy(self, symbol):
        if symbol == 'X':
            return 'O'
        if symbol == 'O':
            return 'X'
        return None

    def get_board(self):
        return self.current_state

    def make_move(self, x, y, symbol, force=False):
        if force:
            if self.current_state[y+1][x+1] != '.' and self.current_state[y+1][x+1] != ' ':
                raise Exception('Illegal move at (%d, %d)' % (x, y))
        elif self.current_state[y+1][x+1] != '.':
            raise Exception('Illegal move at (%d, %d)' % (x, y))
        self.current_state[y+1][x+1] = symbol

    def make_human_move(self, x, y):
        self.make_move(x, y, self.human_symbol)

    def make_computer_move(self, x, y, force=False):
        self.make_move(x, y, self.computer_symbol, force)

    def max_alpha_beta(self, alpha, beta):
        """
        Determine optimal move
        Returns (max_value, x, y)
        """
        maxv = -2
        px = None
        py = None

        result = self.game_over()

        if result:
            if result[0] == self.human_symbol:
                return (-1, 0, 0)
            elif result[0] == self.computer_symbol:
                return (1, 0, 0)
            elif result[0] == '.':
                return (0, 0, 0)

        for i in range(0, 3):
            for j in range(0, 3):
                if self.current_state[i+1][j+1] == '.':
                    self.current_state[i+1][j+1] = self.computer_symbol
                    (m, min_i, in_j) = self.min_alpha_beta(alpha, beta)
                    if m > maxv:
                        maxv = m
                        py = i
                        px = j
                    self.current_state[i+1][j+1] = '.'

                    # Next two ifs in Max and Min are the only difference between regular algorithm and minimax
                    if maxv >= beta:
                        return (maxv, px, py)

                    if maxv > alpha:
                        alpha = maxv

        return (maxv, px, py)

    def min_alpha_beta(self, alpha, beta):

        minv = 2

        qx = None
        qy = None

        result = self.game_over()

        if result:
            if result[0] == self.human_symbol:
                return (-1, 0, 0)
            elif result[0] == self.computer_symbol:
                return (1, 0, 0)
            elif result[0] == '.':
                return (0, 0, 0)

        for i in range(0, 3):
            for j in range(0, 3):
                if self.current_state[i+1][j+1] == '.':
                    self.current_state[i+1][j+1] = self.human_symbol
                    (m, max_i, max_j) = self.max_alpha_beta(alpha, beta)
                    if m < minv:
                        minv = m
                        qy = i
                        qx = j
                    self.current_state[i+1][j+1] = '.'

                    if minv <= alpha:
                        return (minv, qx, qy)

                    if minv < beta:
                        beta = minv

        return (minv, qx, qy)

    def get_computer_move(self):
        # Can the human win in next move?
        (m, hx, hy) = self.get_human_move()
        temp = Game()
        temp.copy(self)
        #print('human %d, %d' % (hx, hy))
        if temp.is_valid(hx, hy):
            temp.make_human_move(hx, hy)
            if temp.game_over():
                # panic!
                cheat = temp.get_cheating_move()
                if cheat:
                    return cheat
         # No, just do our best for now 
        return self.max_alpha_beta(-2, 2)

    def get_human_move(self):
        return self.min_alpha_beta(-2, 2)
    
    def get_cheating_move(self):
        # Scan upper border
        y = -1
        for x in range(-1, 4):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_over():
                    return (10, x, y)
        # Scan lower border
        y = 3
        for x in range(-1, 4):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_over():
                    return (10, x, y)
        # Scan left border
        x = -1
        for y in range(0, 3):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_over():
                    return (10, x, y)
        # Scan left border
        x = 3
        for y in range(0, 3):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_over():
                    return (10, x, y)
        return None

def main2():
    g = Game()
    g.set_human('O')
    print('Human plays O at (1, 1)')
    g.current_state[1+1][1+1] = 'O'
    g.show()
    if g.game_over():
        print('Game over!')
        quit()
    (m, px, py) = g.max_alpha_beta(-2, 2)
    print('Playing X at (%d, %d)' % (px, py))
    g.current_state[px+1][py+1] = 'X'
    g.show()
    
    print('---\nHuman plays O at (0, 1)')
    g.current_state[0+1][1+1] = 'O'
    g.show()
    if g.game_over():
        print('Game over!')
        quit()
    (m, px, py) = g.max_alpha_beta(-2, 2)
    print('Playing X at (%d, %d)' % (px, py))
    g.current_state[px+1][py+1] = 'X'
    g.show()

    # print('---\nHuman plays O at (2, 1)')
    # g.current_state[2][1] = 'O'
    # g.show()
    # if g.game_over():
    #     print('Game over!')
    #     quit()
    # (m, px, py) = g.max_alpha_beta(-2, 2)
    # print('Playing X at (%d, %d)' % (px, py))
    # g.current_state[px][py] = 'X'
    # g.show()

class TestGameMethods(unittest.TestCase):

    def test_find_best_move(self):
        g = Game()
        g.set_human('O')
        g.make_human_move(1, 1)
        (m, px, py) = g.get_computer_move()
        g.make_computer_move(px, py)
        g.make_human_move(0, 1)
        (m, px, py) = g.get_computer_move()
        g.make_computer_move(px, py)
        # Computer must play (2, 1) to prevent human win
        self.assertEqual(px, 2)
        self.assertEqual(py, 1)

    def test_game_over(self):
        # Vertical
        for x in range(0, 3):
            g = Game()
            g.set_human('O')
            for y in range(0, 3):
                g.make_human_move(x, y)
            self.assertEqual(g.game_over()[0], 'O')
        # Horizontal
        for y in range(0, 3):
            g = Game()
            g.set_human('O')
            for x in range(0, 3):
                g.make_human_move(x, y)
            self.assertEqual(g.game_over()[0], 'O')
        # Diagonal (just test one)
        g = Game()
        g.set_human('O')
        for x in range(0, 3):
            g.make_human_move(x, x)
        self.assertEqual(g.game_over()[0], 'O')

    def test_find_cheat_move(self):
        g = Game()
        g.set_human('O')

        for i in range(0, 4):
            (m, px, py) = g.get_human_move()
            g.make_human_move(px, py)
            print('%d computer' % i)
            g.show()
            (m, px, py) = g.get_computer_move()
            g.make_computer_move(px, py, force=True)
            g.show()

        g.show()

        # No legal winning move, computer must play (2, 1) to prevent draw
        (m, px, py) = g.get_computer_move()
        g.make_move(px, py, 'X')
        g.show()
        self.assertEqual(px, 1)
        self.assertEqual(py, 3)
        
if __name__ == "__main__":
    unittest.main()
    
