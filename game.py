from enum import Enum
import html
import os
import random
import time


State = Enum("State", "WAITING PLAYING ENDED")


def turns(players):
    """
    Return a generator that yields the current turn user,
    along with the next turn user.
    """

    if len(players) == 1:
        while True:
            yield players[0], players[0]

    U1, U2 = players[:], players[:]
    random.shuffle(U1)
    while True:
        random.shuffle(U2)
        if U1[-1]["id"] != U2[0]["id"]:
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
            if U1[-1]["id"] != U2[0]["id"]:
                break


class Game:
    def __init__(self, n_messages, timeout, chat_id, savedir):
        self.n_messages = n_messages
        self.timeout = timeout

        self.players = []
        self.player_list_message = None
        self.chat_id = chat_id

        self.last_time = -1
        self.player_notified_half = False
        self.player_notified_thirty_seconds = False

        self.current_player = None
        self.next_player = None
        self.playlist = None

        self.messages = []
        self.savedir = os.path.join(
            savedir,
            f"{int(time.time())}-{random.randbytes(3).hex()}.txt",
        )

        self.status = State.WAITING

    def player_join(self, player):
        self.players.append(player)

    def get_creator(self):
        return self.players[0]

    def start(self):
        self.status = State.PLAYING
        self.playlist = turns(self.players)
        self.current_player, self.next_player = next(self.playlist)
        self.last_time = time.time()
        return self.current_player, self.next_player

    def play_turn(self, message):
        self.messages.append(
            {
                "username": self.current_player,
                "text": message,
            }
        )
        with open(self.savedir, "a") as f:
            f.write(f"{message}\n\n")

    def next_turn(self):
        self.player_notified_half = False
        self.player_notified_thirty_seconds = False
        self.current_player, self.next_player = next(self.playlist)
        self.last_time = time.time()
        return self.current_player, self.next_player

    def end(self):
        self.status = State.ENDED

    def generate_html(self):
        authors = ", ".join(player["username"] for player in self.players)
        story = ""
        for message in self.messages:
            message_ = html.escape(message["text"]).replace("\n", "<br />")
            story += f"<p>{message_}</p>\n"

        content = """<html>
<head>
    <title>Trop Bon Cadavre</title>
    <style>
    body {
        text-align: justify;
    }
    .col {
        width: 50%%;
        margin: 0 auto;
    }
    @media screen and (max-width: 640px) {
        .col {
            width: 100%%;
        }
    }
    </style>
</head>
<body>
<div class="col">
<h1>Trop Bon Cadavre</h1>
<p><strong>Authors: %s</strong></p>
%s
</div>
</body>
</html>
""" % (
            authors,
            story,
        )

        return content
