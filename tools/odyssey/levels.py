"""The levels of HumanLang Odyssey, built from a short description. Each level is a grid of tile letters (16 x 16 tiles)
plus lists of things (coins, bugs, decorations) that the game reads. The test run in tests/test_odyssey.py plays them."""
ROWS = 17          # 17 x 16 = 272 pixels tall
T = 16


class Level:
    def __init__(self, cols, name):
        self.cols, self.name = cols, name
        self.g = [["."] * cols for _ in range(ROWS)]
        self.coins, self.bugs, self.decor, self.flags, self.scrolls = [], [], [], [], []

    def column(self, c, top, letters):
        """A column of ground whose first tile is at row `top`: letters = (surface, second, deep)."""
        for r in range(top, ROWS):
            self.g[r][c] = letters[0] if r == top else letters[1] if r <= top + 2 else letters[2]

    def ground(self, c0, c1, top, letters):
        for c in range(c0, c1 + 1):
            self.column(c, top, letters)

    def block(self, c0, c1, row, letter, rows=1):
        for c in range(c0, c1 + 1):
            for r in range(row, row + rows):
                self.g[r][c] = letter

    def spikes(self, c0, c1, row=16):
        for c in range(c0, c1 + 1):
            self.g[row][c] = "^"

    def text(self):
        return ["".join(r) for r in self.g]

    def top_of(self, c):
        for r in range(ROWS):
            if self.g[r][c] not in (".", "^"):
                return r
        return ROWS

    def coin_arc(self, c0, n, base_y, lift=3):
        """n coins in an arc starting at tile column c0 (x in pixels, y in pixels)."""
        for i in range(n):
            lift_px = [0, 7, 11, 7, 0][i % 5] if n >= 5 else [0, 8, 0][i % 3]
            self.coins.append((c0 * T + 4 + i * 18, base_y - lift_px))

    def coin_row(self, c0, n, y):
        for i in range(n):
            self.coins.append((c0 * T + 4 + i * 16, y))


# =================================================================================================================
# The Motherboard (hub): seven doors on a long circuit-board street
# =================================================================================================================
HUB_DOORS = [150 + 230 * i for i in range(7)]
HUB_COLS = 110


def hub():
    L = Level(HUB_COLS, "hub")
    for c in range(HUB_COLS):
        L.column(c, 14, ("C", "C", "C"))
    return L


# =================================================================================================================
# World 1: Say Hello (a gentle meadow)
# =================================================================================================================
W1_COLS = 72
W1_GROUND = ("G", "D", "E")
W1_ECHO_X, W1_GATE1_X, W1_GATE2_X, W1_PORTAL_X = 12 * T, 28 * T, 52 * T, 65 * T


def world1():
    L = Level(W1_COLS, "w1")
    L.ground(0, W1_COLS - 1, 14, W1_GROUND)
    L.ground(34, 34, 13, W1_GROUND)                 # a little step up to the hill
    L.ground(35, 45, 12, W1_GROUND)                 # the hill
    L.ground(46, 46, 13, W1_GROUND)
    L.block(18, 20, 10, "G")                        # a floating meadow block with a scroll on it
    L.block(60, 62, 10, "G")
    # decorations: (kind, x, ground_y); kinds: 1 tree 2 bush 3 flower pink 4 flower orange 5 tuft 6 rock 7 pine 8 sign
    ground_y = 14 * T
    hill_y = 12 * T
    for kind, c, gy in ((8, 3, ground_y), (1, 5, ground_y), (2, 8, ground_y), (3, 9, ground_y), (1, 15, ground_y), (5, 16, ground_y), (4, 22, ground_y),
                        (2, 24, ground_y), (1, 32, ground_y), (6, 26, ground_y), (3, 31, ground_y), (1, 38, hill_y), (2, 42, hill_y), (4, 44, hill_y),
                        (5, 48, ground_y), (1, 50, ground_y), (3, 55, ground_y), (2, 57, ground_y), (1, 59, ground_y), (4, 63, ground_y), (1, 68, ground_y),
                        (5, 70, ground_y), (3, 12, ground_y), (4, 36, hill_y), (3, 41, hill_y)):
        L.decor.append((kind, c * T, gy))
    L.scrolls = [(19 * T + 0, 9 * T - 22), (40 * T, 12 * T - 24), (61 * T, 9 * T - 22)]
    L.coin_arc(5, 5, 14 * T - 22)
    L.coin_arc(21, 5, 14 * T - 22)
    L.coin_row(18, 3, 9 * T - 40)
    L.coin_arc(36, 5, 12 * T - 22)
    L.coin_arc(47, 5, 14 * T - 22)
    L.coin_arc(56, 4, 14 * T - 22)
    L.coin_row(60, 3, 9 * T - 40)
    return L


# =================================================================================================================
# World 5: Platform Peaks (jumps, spikes, bugs, checkpoints)
# =================================================================================================================
W5_COLS = 130
W5_GROUND = ("N", "S", "S")
W5_SEGMENTS = [(0, 27, 14), (31, 40, 14), (41, 46, 12), (47, 52, 10), (56, 62, 10), (63, 66, 12), (67, 74, 14), (91, 100, 14),
               (101, 104, 12), (105, 108, 10), (109, 112, 8), (116, 129, 14)]
W5_FLOATING = [(78, 79, 12), (82, 83, 11), (86, 87, 12), (13, 15, 12), (35, 36, 12)]
W5_BUGS = [(18, 25, 14), (33, 39, 14), (48, 51, 10), (57, 61, 10), (93, 99, 14), (118, 122, 14)]      # (from column, to column, ground row)
W5_CHECKPOINTS = [70, 100]                                                                              # columns
W5_GOAL_X = 124 * T


def world5():
    L = Level(W5_COLS, "w5")
    for c0, c1, top in W5_SEGMENTS:
        L.ground(c0, c1, top, W5_GROUND)
    for c0, c1, row in W5_FLOATING:
        L.block(c0, c1, row, "N")
    for c in range(W5_COLS):                          # every gap has spikes at the bottom
        if L.top_of(c) == ROWS:
            L.spikes(c, c, 16)
    for c0, c1, lo in W5_BUGS:
        L.bugs.append((c0 * T, (c1 + 1) * T - 30, lo * T - 22))
    L.flags = [(c * T, L.top_of(c) * T - 42) for c in W5_CHECKPOINTS]
    # pines on the high ground (kind 7); rocks (6) and tufts (5)
    for c, kind in ((3, 7), (7, 5), (10, 7), (22, 6), (27, 7), (32, 7), (38, 5), (44, 7), (49, 6), (54, 7), (58, 7), (65, 7), (69, 5),
                    (73, 7), (93, 6), (97, 7), (102, 7), (107, 6), (120, 7), (127, 7), (125, 5)):
        L.decor.append((kind, c * T, L.top_of(min(c, W5_COLS - 1)) * T))
    L.coin_arc(6, 5, 14 * T - 24)
    L.coin_row(13, 3, 12 * T - 22)
    L.coin_arc(28, 5, 14 * T - 60, 0)
    L.coin_arc(33, 5, 14 * T - 24)
    L.coin_row(35, 2, 12 * T - 22)
    L.coin_arc(42, 4, 12 * T - 24)
    L.coin_arc(57, 5, 10 * T - 24)
    L.coin_arc(63, 3, 12 * T - 24)
    L.coin_arc(68, 5, 14 * T - 24)
    L.coin_arc(76, 4, 12 * T - 40)
    L.coin_row(78, 2, 12 * T - 22)
    L.coin_row(82, 2, 11 * T - 22)
    L.coin_row(86, 2, 12 * T - 22)
    L.coin_arc(94, 5, 14 * T - 24)
    L.coin_arc(102, 3, 12 * T - 24)
    L.coin_row(105, 3, 10 * T - 24)
    L.coin_row(109, 3, 8 * T - 24)
    L.coin_arc(117, 5, 14 * T - 24)
    return L
