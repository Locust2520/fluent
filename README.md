# Fluent bot

Fluent is a **Discord bot** that conversates like a _normal_ person, using GPT-3.
It is customizable via a web page where you can define its personality, and eventually change its profile picture.


## You need to know that:
- You **need** a GPT-3 API key to make it work
- The bot is configured to speak in :fr: French; to make it work better in your language, for now, I only suggest that you translate the sentences in `bot.py`.


## Installation

Python >= 3.6 is required

Open a terminal where you want this project to be and then:

```shell
$ git clone https://github.com/Locust2520/fluent
$ cd fluent
$ python -m pip install -r requirements.txt
```


## Run

Before you run the bot, you need to create it from the [Discord's developer portal](https://discord.com/developers/).  
You can find some [tutorials](https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-the-developer-portal) online that are well explained.

### Set up environment variables

You need to define the following environment variables first.

**Mandatory**

|       Name        |                          Description                           |
|-------------------|----------------------------------------------------------------|
| `DISCORD_BOT_KEY` | The token of your bot, got from the Discord's developer portal |
| `OPENAI_API_KEY`  | Your GPT-3 access token                                        |
| `WEB_USERNAME`    | A username defined to access the bot's web page                |
| `WEB_PASSWORD`    | A password for the bot's web page                              |

**Optional**

|     Name      |                              Description                               |
|---------------|------------------------------------------------------------------------|
| `CHAT_LENGTH` | Maximum number of characters in the conversation transcripted to GPT-3 |

You can set an environment variable with:

```shell
$ export ENVIRONMENT_VARIABLE="your content here"
```

### Execute the script

```shell
$ python server.py
```

