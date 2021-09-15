import argparse
import sys
import telebot

from game import Game, State


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
    game.player_join(message.username)

    bot.send_message(
        message.chat.id,
        f"""@{message.username} has started a new Trop Bon Cadavre game!
It will last {n_messages} messages, and each player will have {timeout} seconds to answer.
**Type `/join` to be part of the game.**
@{message.username}: you can use `/start` to start the game once everyone joined, or `/cancel` to cancel it.
""",
    )

    game.player_list_message = bot.send_message(
        message.chat_id, f"""Players: @{message.username}"""
    )


@bot.message_handler(commands=["join"])
def join_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.username in game.players:
        bot.reply_to(message, "You have already joined this game!")
        return

    game.player_join(message.username)
    bot.edit_message_text(
        f"""Players: {', '.join(f'@{username}' for username in game.players)}""",
        chat_id=game.player_list_message.chat.id,
        message_id=game.player_list_message.message_id,
    )
    bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(commands=["start"], filter=is_public)
def start_game(message):
    global game

    if game is None or game.status != State.WAITING:
        return

    if message.username != game.get_creator():
        bot.reply_to(message, "Only the person who created this game can start it.")
        return

    bot.send_message(
        message.chat_id, "The game has started! Waiting for the first player's message."
    )
    game.start()


@bot.message_handler(commands=["cancel"], filter=is_public)
def cancel_game(message):
    global game

    if game is None:
        return

    if message.username != game.get_creator():
        bot.reply_to(message, "Only the person who created this game can cancel it.")
        return

    del game
    game = None

    bot.send_message(message.chat_id, "The game was successfully canceled.")


bot.polling()
