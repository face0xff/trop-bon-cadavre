# Trop Bon Cadavre

A Telegram bot for playing Trop Bon Cadavre (english: *very good corpse*), a game freely adapted from the french *Cadavre exquis*.

A game is instanciated with at least two players, a given number of messages and a *timeout* (maximum allowed time each turn).
Participants can agree or not on a theme for a story.

A first player is chosen at random to write the beginning of the story.
Then, each turn, another player is chosen at random to follow up on the last message.
They can only read the last message, and they do not know its author either. They can only try their best to continue the storyline in a coherent fashion!

Messages can range, at your will, from a single sentence to several paragraphs.
Games can last from a few minutes to several weeks!

Once the maximum number of messages has been reached, the game stops and the entire story is revealed.
Sometimes it surprisingly makes sense, sometimes it does not at all; but most of the time, it's hilarious!

## Commands

* `/new <number of messages> <timeout in seconds>` — Create a new game
* `/join` — Join the game
* `/start` — Start the game (only for the person who created it)
* `/cancel` — Cancel a game before it starts (only for the person who created it)
* `/skip` — Skip your turn

## Run the bot

Requires at least Python 3.9.

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python main.py --token "<Your Telegram Bot Token>" --name my_cadavre
```

Then invite the bot to a group channel.

The `--name` argument is mandatory if you wish to run concurrent instances of the bot. In this case, give them each a name, which can be anything as long as they are distinct.

## Todo

### Features

* Add possibility to leave a game that hasn't started yet (the creator can't leave)
* Add possibility to adjust time and count after `/new`
* Add possibility to host a simple HTTP server to serve the HTML export files (also better to centralize CSS, fonts...)
* Add statistics
  * Game duration
  * ...

### Issues

* State of game is lost when bot crashes/loses connection (except for the txt story save)
  * Need to serialize current `Game` into a file and keep it updated
  * If the bot crashes, it automatically restarts and tries to load the serialized `Game` file if the state was "playing"
  * Careful of what happens when several instances of the same bot are being run (what if two bots crash at the same time? they should load the right file)
* Some race conditions on edge cases, such as sending a message at the timeout moment
* HTML render: responsiveness not always triggered on mobile devices
* Anyone can invite the bot to another group and make it unusable by starting a very long game
  * Provide an option to restrict the bot to a certain channel id?
