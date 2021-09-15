import argparse
import sys
import telebot
import time

from game import Game, State
from timer import RepeatedTimer


parser = argparse.ArgumentParser()
parser.add_argument("--token", help="Bot token")
# parser.add_argument("--savedir", default="saves", help="Directory where messages are saved")

args = parser.parse_args()

if not args.token:
    print("[x] Please provide bot token.")
    sys.exit(-1)

bot = telebot.TeleBot(args.token)
game = None


def send_large_message(chat_id, text):
    for text_ in telebot.util.smart_split(text, chars_per_string=3000):
        bot.send_message(chat_id, text_)


def is_public(message):
    return message.chat.type != "private"


@bot.message_handler(commands=["new"], filter=is_public)
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

    game = Game(n_messages, timeout)
    game.player_join(
        {
            "username": message.from_user.username,
            "id": message.from_user.id,
        }
    )

    bot.send_message(
        message.chat.id,
        f"""@{message.from_user.username} has started a new Trop Bon Cadavre game!
It will last {n_messages} messages, and each player will have {timeout} seconds to answer.
**Type `/join` to be part of the game.**
@{message.from_user.username}: you can use `/start` to start the game once everyone joined, or `/cancel` to cancel it.
""",
    )

    game.player_list_message = bot.send_message(
        message.chat_id, f"""Players: @{message.from_user.username}"""
    )


@bot.message_handler(commands=["join"])
def join_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.from_user.username in game.players:
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
    bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(commands=["start"], filter=is_public)
def start_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.from_user.id != game.get_creator()["id"]:
        bot.reply_to(message, "Only the person who created this game can start it.")
        return

    bot.send_message(
        message.chat_id, "The game has started! Waiting for the first player's message."
    )

    current_player, next_player = game.start()
    bot.send_message(
        current_player["id"],
        "You have the honor and the great responsibility to start the story with the first message!",
    )
    if len(game.messages) < game.n_messages - 1:
        bot.send_message(next_player["id"], "Get ready. Next turn is yours!")


@bot.message_handler(commands=["cancel"], filter=is_public)
def cancel_game(message):
    global game

    if game is None:
        return

    if message.from_user.id != game.get_creator()["id"]:
        bot.reply_to(message, "Only the person who created this game can cancel it.")
        return

    del game
    game = None

    bot.send_message(message.chat_id, "The game was successfully canceled.")


def game_poll():
    if game is None or game.status != State.PLAYING:
        return

    if game.timeout >= 120:
        if not game.player_notified_half:
            if time.time() - game.last_time > game.timeout / 2:
                game.player_notified_half = True
                bot.send_message(
                    game.current_player.id,
                    f"You have {game.timeout // 2} seconds left!",
                )

    if game.timeout >= 30:
        if not game.player_notified_thirty_seconds:
            if time.time() - game.last_time > game.timeout - 30:
                game.player_notified_thirty_seconds = True
                bot.send_message(game.current_player.id, "You have 30 seconds left!")

    if time.time() - game.last_time >= game.timeout:
        bot.send_message(game.current_player.id, "Time out! You were too slow.")
        current_player, next_player = game.next_turn()
        if len(game.messages) > 0:
            bot.send_message(
                current_player["id"],
                f"Your turn to write message {len(game.messages) + 1}/{game.n_messages}.\n\n{game.messages[-1]}",
            )
        else:
            bot.send_message(
                current_player["id"],
                "You have the honor and the great responsibility to start the story with the first message!",
            )
        if len(game.messages) < game.n_messages - 1:
            bot.send_message(next_player["id"], "Get ready. Next turn is yours!")


rt = RepeatedTimer(1, game_poll)

try:
    bot.polling()
except Exception as e:
    print(e)
finally:
    rt.stop()
