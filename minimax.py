import time

class Game:
    def __init__(self):
        self.initialize_game()

    def initialize_game(self):
        self.current_state = [['.','.','.'],
                              ['.','.','.'],
                              ['.','.','.']]

    def set_human(self, symbol):
        self.human_symbol = symbol
        self.computer_symbol = self.get_enemy(self.human_symbol)

    def show(self):
        for i in range(0, 3):
            for j in range(0, 3):
                print('{}|'.format(self.current_state[i][j]), end=" ")
            print()
        print()

    def is_valid(self, px, py):
        if px < 0 or px > 2 or py < 0 or py > 2:
            return False
        elif self.current_state[px][py] != '.':
            return False
        else:
            return True

    # Checks if the game has ended and returns the winner in each case
    def game_over(self):
        # Vertical win
        for i in range(0, 3):
            if (self.current_state[0][i] != '.' and
                self.current_state[0][i] == self.current_state[1][i] and
                self.current_state[1][i] == self.current_state[2][i]):
                return self.current_state[0][i]

        # Horizontal win
        for i in range(0, 3):
            if (self.current_state[i] == ['X', 'X', 'X']):
                return 'X'
            elif (self.current_state[i] == ['O', 'O', 'O']):
                return 'O'

        # Main diagonal win
        if (self.current_state[0][0] != '.' and
            self.current_state[0][0] == self.current_state[1][1] and
            self.current_state[0][0] == self.current_state[2][2]):
            return self.current_state[0][0]

        # Second diagonal win
        if (self.current_state[0][2] != '.' and
            self.current_state[0][2] == self.current_state[1][1] and
            self.current_state[0][2] == self.current_state[2][0]):
            return self.current_state[0][2]

        # Is whole board full?
        for i in range(0, 3):
            for j in range(0, 3):
                # There's an empty field, we continue the game
                if (self.current_state[i][j] == '.'):
                    return None

        # It's a tie!
        return '.'

    def get_enemy(self, symbol):
        if symbol == 'X':
            return 'O'
        if symbol == 'O':
            return 'X'
        return None

    def max_alpha_beta(self, alpha, beta):
        maxv = -2
        px = None
        py = None

        result = self.game_over()

        if result == self.human_symbol:
            return (-1, 0, 0)
        elif result == self.computer_symbol:
            return (1, 0, 0)
        elif result == '.':
            return (0, 0, 0)

        for i in range(0, 3):
            for j in range(0, 3):
                if self.current_state[i][j] == '.':
                    self.current_state[i][j] = self.computer_symbol
                    (m, min_i, in_j) = self.min_alpha_beta(alpha, beta)
                    if m > maxv:
                        maxv = m
                        px = i
                        py = j
                    self.current_state[i][j] = '.'

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

        if result == self.human_symbol:
            return (-1, 0, 0)
        elif result == self.computer_symbol:
            return (1, 0, 0)
        elif result == '.':
            return (0, 0, 0)

        for i in range(0, 3):
            for j in range(0, 3):
                if self.current_state[i][j] == '.':
                    self.current_state[i][j] = self.human_symbol
                    (m, max_i, max_j) = self.max_alpha_beta(alpha, beta)
                    if m < minv:
                        minv = m
                        qx = i
                        qy = j
                    self.current_state[i][j] = '.'

                    if minv <= alpha:
                        return (minv, qx, qy)

                    if minv < beta:
                        beta = minv

        return (minv, qx, qy)

def main2():
    g = Game()
    g.set_human('O')
    print('Human plays O at (1, 1)')
    g.current_state[1][1] = 'O'
    g.show()
    if g.game_over():
        print('Game over!')
        quit()
    (m, px, py) = g.max_alpha_beta(-2, 2)
    print('Playing X at (%d, %d)' % (px, py))
    g.current_state[px][py] = 'X'
    g.show()
    
    print('---\nHuman plays O at (0, 1)')
    g.current_state[0][1] = 'O'
    g.show()
    if g.game_over():
        print('Game over!')
        quit()
    (m, px, py) = g.max_alpha_beta(-2, 2)
    print('Playing X at (%d, %d)' % (px, py))
    g.current_state[px][py] = 'X'
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

if __name__ == "__main__":
    main2()
    
