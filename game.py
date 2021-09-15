from enum import Enum
import random
import time


State = Enum("State", "WAITING PLAYING ENDED")


def tours(usernames):
    """
    Return a generator that yields the current turn user,
    along with the next turn user.
    """

    if len(usernames) == 1:
        while True:
            yield usernames[0], usernames[0]

    U1, U2 = usernames[:], usernames[:]
    random.shuffle(U1)
    while True:
        random.shuffle(U2)
        if U1[-1] != U2[0]:
            break

    while True:
        for i in range(len(U1)):
            if i < len(U1) - 1:
                yield U1[i], U1[i + 1]
            else:
                yield U1[-1], U2[0]
        U1, U2 = U2, U1
        while True:
            random.shuffle(U2)
            if U1[-1] != U2[0]:
                break


class Game:
    def __init__(self, n_messages=10, timeout=300):
        self.n_messages = n_messages
        self.timeout = timeout

        self.players = []
        self.player_list_message = None
        self.last_time = -1

        self.status = State.WAITING

    def player_join(self, player_username):
        self.players.append(player_username)

    def get_creator(self):
        return self.players[0]

    def start(self):
        self.status = State.PLAYING
        self.last_time = time.time()
