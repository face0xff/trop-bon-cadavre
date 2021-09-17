import argparse
import pathlib
import sys
import telebot
import tempfile
import time
import traceback

from game import Game, State
from timer import RepeatedTimer


parser = argparse.ArgumentParser()
parser.add_argument("--token", help="Bot token")
parser.add_argument(
    "--savedir", default="saves", help="Directory where messages are saved"
)

args = parser.parse_args()

if not args.token:
    print("[x] Please provide bot token.")
    sys.exit(-1)

if not pathlib.Path(args.savedir).is_dir():
    print("[x] Please provide a valid directory for savedir.")
    sys.exit(-1)

bot = telebot.TeleBot(args.token, threaded=False)
game = None

message_buffer = []
message_buffer_time = -1


def send_large_message(chat_id, text):
    for text_ in telebot.util.smart_split(text, chars_per_string=3000):
        bot.send_message(chat_id, text_, parse_mode="Markdown")


def is_public(message):
    return message.chat.type != "private"


def is_private(message):
    return message.chat.type == "private"


@bot.message_handler(commands=["new"], func=is_public)
def new_game(message):
    global game

    if game is not None:
        bot.reply_to(message, "A game is already starting or has already been started.")
        return

    try:
        n_messages, timeout = map(int, message.text.split()[1:])
    except:
        bot.reply_to(message, "Usage: /new <number of messages> <timeout in seconds>")
        return

    if n_messages <= 0 or n_messages > 10000:
        bot.reply_to(message, "Number of messages must be between 1 and 10000.")
        return

    if timeout < 10 or timeout > 7 * 24 * 60 * 60:
        bot.reply_to(message, "Timeout must be between 10 seconds and 1 week.")
        return

    game = Game(n_messages, timeout, message.chat.id, args.savedir)
    game.player_join(
        {
            "username": message.from_user.username,
            "id": message.from_user.id,
        }
    )

    bot.send_message(
        game.chat_id,
        f"""@{message.from_user.username} has started a new Trop Bon Cadavre game!
It will last {n_messages} messages, and each player will have {timeout} seconds to answer.
*Send me /join in DM to be part of the game.*

@{message.from_user.username}: you can use `/start` to start the game once everyone joined, or `/cancel` to cancel it.
""",
        parse_mode="Markdown",
    )

    game.player_list_message = bot.send_message(
        game.chat_id, f"Players: @{message.from_user.username}"
    )


@bot.message_handler(commands=["join"], func=is_private)
def join_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.from_user.username in [player["username"] for player in game.players]:
        bot.reply_to(message, "You have already joined this game!")
        return

    game.player_join(
        {
            "username": message.from_user.username,
            "id": message.from_user.id,
        }
    )
    bot.edit_message_text(
        f"""Players: {', '.join(f'@{player["username"]}' for player in game.players)}""",
        chat_id=game.player_list_message.chat.id,
        message_id=game.player_list_message.message_id,
    )
    bot.reply_to(message, "You're in!")


@bot.message_handler(commands=["start"], func=is_public)
def start_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.from_user.id != game.get_creator()["id"]:
        bot.reply_to(message, "Only the person who created this game can start it.")
        return

    bot.send_message(
        game.chat_id, "The game has started! Waiting for the first player's message."
    )

    current_player, next_player = game.start()
    bot.send_message(
        current_player["id"],
        "*You have the honor and the great responsibility to start the story with the first message!*",
        parse_mode="Markdown",
    )
    if len(game.messages) < game.n_messages - 1:
        bot.send_message(next_player["id"], "Get ready. Next turn is yours!")


@bot.message_handler(commands=["cancel"], func=is_public)
def cancel_game(message):
    global game

    if game is None:
        return

    if message.from_user.id != game.get_creator()["id"]:
        bot.reply_to(message, "Only the person who created this game can cancel it.")
        return

    bot.send_message(game.chat_id, "The game was successfully canceled.")

    del game
    game = None


@bot.message_handler(func=is_private)
def get_story_message(message):
    global game
    global message_buffer, message_buffer_time

    if game is None or game.status != State.PLAYING:
        return

    if game.current_player["id"] != message.from_user.id:
        return

    if message_buffer_time == -1:
        message_buffer_time = time.time()

    # Allow 250ms interval to get all messages from player in case they were split
    if time.time() < message_buffer_time + 0.25:
        message_buffer.append(message.text)
        return


def game_poll():
    global game
    global message_buffer, message_buffer_time

    if game is None or game.status != State.PLAYING:
        return

    if game.timeout >= 120:
        if not game.player_notified_half:
            if time.time() - game.last_time > game.timeout / 2:
                game.player_notified_half = True
                bot.send_message(
                    game.current_player["id"],
                    f"You have {game.timeout // 2} seconds left!",
                )

    if game.timeout >= 30:
        if not game.player_notified_thirty_seconds:
            if time.time() - game.last_time > game.timeout - 30:
                game.player_notified_thirty_seconds = True
                bot.send_message(game.current_player["id"], "You have 30 seconds left!")

    if time.time() - game.last_time >= game.timeout:
        bot.send_message(game.current_player["id"], "Time out! You were too slow.")
        bot.send_message(
            game.chat_id, "Someone failed to answer in time. Asking the next player..."
        )
        current_player, next_player = game.next_turn()
        if len(game.messages) > 0:
            send_large_message(
                current_player["id"],
                f"*Your turn to write message {len(game.messages) + 1}/{game.n_messages}.*\n\n{game.messages[-1]['text']}",
            )
        else:
            bot.send_message(
                current_player["id"],
                "*You have the honor and the great responsibility to start the story with the first message!*",
                parse_mode="Markdown",
            )
        if len(game.messages) < game.n_messages - 1:
            bot.send_message(next_player["id"], "Get ready. Next turn is yours!")
        return

    if len(message_buffer) > 0 and time.time() >= message_buffer_time + 0.25 * 2:
        game.play_turn(" ".join(message_buffer))
        message_buffer = []
        message_buffer_time = -1

        bot.send_message(game.current_player["id"], "Your message was registered.")
        bot.send_message(
            game.chat_id, f"Message {len(game.messages)}/{game.n_messages} registered!"
        )

        if len(game.messages) == game.n_messages:
            game.end()

            bot.send_message(
                game.chat_id,
                "The game has ended! Exporting the story into an HTML file...",
            )

            content = game.generate_html()
            temp = tempfile.NamedTemporaryFile(delete=False, dir="/tmp", suffix=".html")
            temp.write(content.encode())
            filename = temp.name
            temp.close()
            bot.send_document(game.chat_id, open(filename, "rb"))

            del game
            game = None

            return

        current_player, next_player = game.next_turn()

        send_large_message(
            current_player["id"],
            f"*Your turn to write message {len(game.messages) + 1}/{game.n_messages}.*\n\n{game.messages[-1]['text']}",
        )
        if len(game.messages) < game.n_messages - 1:
            bot.send_message(next_player["id"], "Get ready. Next turn is yours!")


rt = RepeatedTimer(0.5, game_poll)

try:
    bot.polling()
except:
    traceback.print_exc()
finally:
    rt.stop()
