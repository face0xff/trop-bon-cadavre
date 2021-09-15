# Trop Bon Cadavre

A Telegram bot for playing Trop Bon Cadavre.

## Game

Trop Bon Cadavre (english: *very good corpse*) is a game freely adapted from the french *Cadavre exquis*.

A game is instanciated with a certain number of players (at least two) and a number of messages.
A first player is chosen at random to write the beginning of a story (the players can agree or not on a theme for the story).
Then, each turn, another player is chosen at random to follow up on the last message.
They can only read the last message, and they do not know its author either, but they should try their best to continue the storyline in a coherent fashion.
A message can range, at your will, from a single sentence to several paragraphs.

Once the maximum number of messages has been reached, the game stops and participants can reunite to read the whole story.
Sometimes it surprisingly makes sense, sometimes it does not at all; but most of the time, it's hilarious!

## Commands

* `/new <number of messages> <timeout in seconds>` --- Create a new game
* `/join` --- Join the game 
* `/start` --- Start the game (only for the person who created it)
* `/cancel` --- Cancel a game before it starts (only for the person who created it)

## Run the bot

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python main.py --name "Trop Bon Cadavre" --token "<REDACTED>"
```

## Todo

* Concurrent games across channels
* Periodically save the story into a file, in case something wrong happens
* Automatically generate a PDF at the end of a game
* Let a player skip their turn
* Show statistics at the end of a game
  * Number of words
  * Who wrote the most
  * Who timed out the most
  * Who's the slowest or the fastest in average
  * ...
