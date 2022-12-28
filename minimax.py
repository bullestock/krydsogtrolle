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

    def is_occupied(self, x, y):
        return self.current_state[x][y] != '.' and self.current_state[x][y] != ' '

    # Checks if the game has ended.
    # If yes, returns (winner, coord1, coord2)
    # Else returns None
    def game_over(self):
        # Vertical win
        for i in range(0, 5):
            for j in range(0, 3):
                if (self.is_occupied(j, i) and
                    self.current_state[j][i] == self.current_state[j+1][i] and
                    self.current_state[j][i] == self.current_state[j+2][i]):
                    return (self.current_state[j][i], (i, j), (i, j+2))

        # Horizontal win
        for i in range(0, 5):
            for j in range(0, 3):
                if (self.current_state[i][j:j+3] == ['X', 'X', 'X']):
                    return ('X', (i, j), (i, j+2))
                elif (self.current_state[i][j:j+3] == ['O', 'O', 'O']):
                    return ('O', (i, j), (i, j+2))

        # Main diagonal wins
        # Left
        for j in range(0, 2):
            if (self.is_occupied(j+1, j) and
                self.current_state[j+1][j] == self.current_state[j+2][j+1] and
                self.current_state[j+1][j] == self.current_state[j+3][j+2]):
                return (self.current_state[j+1][j], (j+1, j), (j+3, j+3))
        # Center
        for j in range(0, 3):
            if (self.is_occupied(0+j, 0+j) and
                self.current_state[0+j][0+j] == self.current_state[1+j][1+j] and
                self.current_state[0+j][0+j] == self.current_state[2+j][2+j]):
                return (self.current_state[0+j][0+j], (j, j), (j+2, j+2))
        # Right
        for j in range(0, 2):
            if (self.is_occupied(j, j+1) and
                self.current_state[j][j+1] == self.current_state[j+1][j+2] and
                self.current_state[j][j+1] == self.current_state[j+2][j+3]):
                return (self.current_state[j][j+1], (j, j+1), (j+2, j+3))

        # Second diagonal wins
        # Left
        for j in range(0, 2):
            if (self.is_occupied(j, 3-j) and
                self.current_state[j][3-j] == self.current_state[j+1][2-j] and
                self.current_state[j][3-j] == self.current_state[j+2][1-j]):
                return (self.current_state[j][3-j], (j, 3-j), (j+2, 1-j))
        # Center
        for j in range(0, 3):
            if (self.is_occupied(j, 4-j) and
                self.current_state[j][4-j] == self.current_state[j+1][3-j] and
                self.current_state[j][4-j] == self.current_state[j+2][2-j]):
                return (self.current_state[j][4-j], (j, 4-j), (j+2, 2-j))
        # Right
        for j in range(0, 2):
            if (self.is_occupied(j+1, 4-j) and
                self.current_state[j+1][4-j] == self.current_state[j+2][3-j] and
                self.current_state[j+1][4-j] == self.current_state[j+3][2-j]):
                return (self.current_state[j+1][4-j], (j+1, 4-j), (j+3, 2-j))

        # Is whole board full?
        for i in range(0, 3):
            for j in range(0, 3):
                # There's an empty field, we continue the game
                if not self.is_occupied(i+1, j+1):
                    return None

        # It's a tie!
        return ('.', None, None)

    def game_won(self):
        go = self.game_over()
        if not go:
            return False
        return go[0] != '.'

    def last_round(self):
        nof_occupied = 0
        for i in range(0, 3):
            for j in range(0, 3):
                if self.current_state[i+1][j+1] != '.':
                    nof_occupied = nof_occupied + 1
        return nof_occupied >= 7
    
    def get_enemy(self, symbol):
        if symbol == 'X':
            return 'O'
        if symbol == 'O':
            return 'X'
        return None

    def get_board(self):
        return self.current_state

    def make_move(self, x, y, symbol, force=False):
        if x is None or y is None:
            self.show()
            raise Exception('Illegal move: x %s y %s' % (str(x), str(y)))
        if force:
            if self.is_occupied(y+1, x+1):
                raise Exception('Illegal move at (%d, %d)' % (x, y))
        elif self.current_state[y+1][x+1] != '.':
            raise Exception('Illegal move at (%d, %d)' % (x, y))
        self.current_state[y+1][x+1] = symbol

    def erase_move(self, x, y):
        self.current_state[y+1][x+1] = '.'
        
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
        move = self.max_alpha_beta(-2, 2)
        temp = Game()
        temp.copy(self)
        temp.make_computer_move(move[1], move[2])
        # Can the human win in next move?
        (m, hx, hy) = temp.get_human_move()
        if temp.is_valid(hx, hy):
            temp.make_human_move(hx, hy)
            go = temp.game_over()
            if go and go[0] != '.':
                # panic!
                print('Looking bad - after human move:')
                if go:
                    print('- game over')
                temp.show()
                temp.erase_move(hx, hy) # undo
                cheat = temp.get_cheating_move()
                if cheat:
                    print('Cheating')
                    return cheat
        # No, just do our best for now 
        return move

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
                if temp.game_won():
                    return (10, x, y)
        # Scan lower border
        y = 3
        for x in range(-1, 4):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_won():
                    return (9, x, y)
        # Scan left border
        x = -1
        for y in range(0, 3):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_won():
                    return (8, x, y)
        # Scan left border
        x = 3
        for y in range(0, 3):
            temp = Game()
            temp.copy(self)
            if temp.is_valid(x, y, force=True):
                temp.make_computer_move(x, y, force=True)
                if temp.game_won():
                    return (7, x, y)
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
            go = g.game_over()
            self.assertFalse(go is None)
            self.assertEqual(go[0], 'O')
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

    def test_game_over_cheat(self):
        # Vertical
        for i in range(-1, 2):
            for x in range(0, 3):
                g = Game()
                g.set_human('X')
                for y in range(0, 3):
                    g.make_computer_move(i + x, y, force=True)
                self.assertEqual(g.game_over()[0], 'O')
        # Horizontal
        for i in range(-1, 2):
            for y in range(0, 3):
                g = Game()
                g.set_human('X')
                for x in range(0, 3):
                    g.make_computer_move(i + x, y, force=True)
                go = g.game_over()
                self.assertEqual(go[0], 'O')
        # Diagonals \
        # Left 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(-1, 0, force=True)
        g.make_computer_move(0, 1, force=True)
        g.make_computer_move(1, 2, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Left 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, 1, force=True)
        g.make_computer_move(1, 2, force=True)
        g.make_computer_move(2, 3, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(-1, -1, force=True)
        g.make_computer_move(0, 0, force=True)
        g.make_computer_move(1, 1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, 0, force=True)
        g.make_computer_move(1, 1, force=True)
        g.make_computer_move(2, 2, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 3
        g = Game()
        g.set_human('X')
        g.make_computer_move(1, 1, force=True)
        g.make_computer_move(2, 2, force=True)
        g.make_computer_move(3, 3, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Right 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, -1, force=True)
        g.make_computer_move(1, 0, force=True)
        g.make_computer_move(2, 1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Right 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(1, 0, force=True)
        g.make_computer_move(2, 1, force=True)
        g.make_computer_move(3, 2, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Diagonals /
        # Left 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, 1, force=True)
        g.make_computer_move(1, 0, force=True)
        g.make_computer_move(2, -1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Left 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(-1, 2, force=True)
        g.make_computer_move(0, 1, force=True)
        g.make_computer_move(1, 0, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(-1, 3, force=True)
        g.make_computer_move(0, 2, force=True)
        g.make_computer_move(1, 1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, 2, force=True)
        g.make_computer_move(1, 1, force=True)
        g.make_computer_move(2, 0, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Center 3
        g = Game()
        g.set_human('X')
        g.make_computer_move(1, 1, force=True)
        g.make_computer_move(2, 0, force=True)
        g.make_computer_move(3, -1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Right 1
        g = Game()
        g.set_human('X')
        g.make_computer_move(0, 3, force=True)
        g.make_computer_move(1, 2, force=True)
        g.make_computer_move(2, 1, force=True)
        self.assertEqual(g.game_over()[0], 'O')
        # Right 2
        g = Game()
        g.set_human('X')
        g.make_computer_move(1, 2, force=True)
        g.make_computer_move(2, 1, force=True)
        g.make_computer_move(3, 0, force=True)
        self.assertEqual(g.game_over()[0], 'O')

    def test_find_cheat_move_1(self):
        g = Game()
        g.set_human('O')

        for i in range(0, 3):
            (m, px, py) = g.get_human_move()
            g.make_human_move(px, py)
            (m, px, py) = g.get_computer_move()
            g.make_computer_move(px, py, force=True)

        (m, px, py) = g.get_human_move()
        g.make_human_move(px, py)
        (m, px, py) = g.get_cheating_move()
        g.make_computer_move(px, py, force=True)
        self.assertEqual(px, 3)
        self.assertEqual(py, -1)
        
    def test_find_cheat_move_2(self):
        g = Game()
        g.set_human('X')
        g.make_human_move(0, 0)
        g.make_human_move(2, 0)
        g.make_human_move(2, 1)
        g.make_human_move(0, 2)
        g.make_human_move(1, 2)
        g.make_computer_move(1, 0)
        g.make_computer_move(0, 1)
        g.make_computer_move(1, 1)
        g.make_computer_move(2, 2)
        (m, px, py) = g.get_cheating_move()
        g.make_computer_move(px, py, force=True)
        self.assertEqual(px, 1)
        self.assertEqual(py, -1)
        
if __name__ == "__main__":
    unittest.main()
