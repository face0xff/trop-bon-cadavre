from enum import Enum
import html
import os
import random
import time


State = Enum("State", "WAITING PLAYING ENDED")


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
        self.player_notified_five_seconds = False

        self.current_player = None
        self.next_player = None
        self.U1 = None
        self.U2 = None
        self.U_i = 0

        self.title = ""
        self.messages = []

        self.nonce = random.randbytes(3).hex()
        self.savedir = os.path.join(
            savedir,
            f"{int(time.time())}-{self.nonce}.txt",
        )

        self.timeouts = {}

        self.status = State.WAITING
    
    def init_playlist(self):
        if len(self.players) == 1:
            return

        self.U1, self.U2 = self.players[:], self.players[:]
        random.shuffle(self.U1)
        while True:
            random.shuffle(self.U2)
            # No "AA" pattern
            if self.U1[-1]["id"] != self.U2[0]["id"]:
                # No "ABA" pattern (when >= 3 players)
                if len(self.players) >= 3 and (
                    self.U1[-1]["id"] == self.U2[1]["id"] or self.U1[-2]["id"] == self.U2[0]["id"]
                ):
                    continue
                break
        
        return
    
    def next_playlist_turn(self):
        if len(self.players) == 1:
            return self.players[0], self.players[0]

        if self.U_i < len(self.U1):
            if self.U_i < len(self.U1) - 1:
                self.U_i += 1
                return self.U1[self.U_i - 1], self.U1[self.U_i]
            else:
                self.U_i += 1
                return self.U1[-1], self.U2[0]
        
        self.U1, self.U2 = self.U2, self.U1
        while True:
            random.shuffle(self.U2)
            if self.U1[-1]["id"] != self.U2[0]["id"]:
                if len(self.players) >= 3 and (
                    self.U1[-1]["id"] == self.U2[1]["id"] or self.U1[-2]["id"] == self.U2[0]["id"]
                ):
                    continue
                break
        
        self.U_i = 0

    def set_title(self, title):
        self.title = title

    def player_join(self, player):
        self.players.append(player)

    def get_creator(self):
        return self.players[0]

    def start(self):
        self.status = State.PLAYING
        self.init_playlist()
        self.current_player, self.next_player = self.next_playlist_turn()
        self.last_time = time.time()
        return self.current_player, self.next_player

    def play_turn(self, message):
        self.messages.append(
            {
                "player": self.current_player,
                "text": message,
                "duration": time.time() - self.last_time,
            }
        )
        with open(self.savedir, "a") as f:
            f.write(f"{message}\n\n")

    def next_turn(self):
        self.player_notified_half = False
        self.player_notified_thirty_seconds = False
        self.player_notified_five_seconds = False
        self.current_player, self.next_player = self.next_playlist_turn()
        self.last_time = time.time()
        return self.current_player, self.next_player

    def end(self):
        self.status = State.ENDED

    def timed_out(self):
        username = self.current_player["username"]
        if username not in self.timeouts.keys():
            self.timeouts[username] = 0
        self.timeouts[username] += 1

    def get_statistics(self):
        times = {}
        lengths = {}
        for message in self.messages:
            if message["player"]["username"] not in times.keys():
                times[message["player"]["username"]] = []
            if message["player"]["username"] not in lengths.keys():
                lengths[message["player"]["username"]] = 0
            times[message["player"]["username"]].append(message["duration"])
            lengths[message["player"]["username"]] += len(message["text"])

        mean_times = {}
        for player in times:
            mean_times[player] = round(sum(times[player]) / len(times[player]), 1)

        return {
            "words": len(" ".join(m["text"] for m in self.messages).split()),
            "most_characters_count": max(lengths.values()),
            "most_characters_player": max(lengths, key=lengths.get),
            "most_timeouts_count": max(self.timeouts.values())
            if self.timeouts
            else None,
            "most_timeouts_player": max(self.timeouts, key=self.timeouts.get)
            if self.timeouts
            else None,
            "fastest_mean_duration": min(mean_times.values()),
            "fastest_player": min(mean_times, key=mean_times.get),
            "slowest_mean_duration": max(mean_times.values()),
            "slowest_player": max(mean_times, key=mean_times.get),
        }

    def generate_html(self):
        authors = ", ".join(player["username"] for player in self.players)

        s = self.get_statistics()
        statistics = f"""
Number of words: {s["words"]}<br />
Wrote the most: {s["most_characters_player"]} ({s["most_characters_count"]} characters)<br />
Fastest player: {s["fastest_player"]} ({s["fastest_mean_duration"]} seconds in average)<br />
Slowest player: {s["slowest_player"]} ({s["slowest_mean_duration"]} seconds in average)<br />
"""
        if self.timeouts:
            statistics += f"Most timeouts: {s['most_timeouts_player']} ({s['most_timeouts_count']})<br />"

        story = ""
        for i, message in enumerate(self.messages):
            message_ = html.escape(message["text"]).replace("\n", "<br />")
            story += (
                f'<div class="message"><div>{i + 1}</div><div>{message_}</div></div>\n'
            )

        content = """<html>
<head>
    <title>Trop Bon Cadavre : %s</title>
    <meta charset="UTF-8">
    <style>
    body {
        text-align: justify;
    }
    hr {
        color: #fefefe;
    }
    .col {
        width: 50%%;
        margin: 0 auto;
    }
    .message {
        justify-content: flex-start;
        display: flex;
        margin-top: 1em;
    }
    .message > div:first-child {
        text-align: right;
        flex: 1;
        color: #777;
        font-size: 0.6em;
        margin-right: 1em;
        margin-top: 0.25em;
    }
    .message > div:last-child {
        flex: 40;
    }
    @media screen and (max-width: 900px) {
        .col {
            width: 100%%;
        }
    }
    </style>
</head>
<body>
<div class="col">
<h1>%s</h1>
<p><strong>A story written by %s</strong></p>
<hr />
<p>
<strong>Statistics</strong><br />
%s
</p>
<hr />
%s
</div>
</body>
</html>
""" % (
            html.escape(self.title),
            html.escape(self.title),
            authors,
            statistics,
            story,
        )

        return content
