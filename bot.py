import discord
import openai
import json
import os
import re
import asyncio
from datetime import datetime
from shlex import split

DISCORD_TOKEN = os.getenv("DISCORD_BOT_KEY")
GPT3_TOKEN = os.getenv("OPENAI_API_KEY")
# max length (in characters) of the conversation for GPT-3:
MAX_HISTORY_LEN = int(os.getenv("CHAT_LENGTH", 500))


class GPT3Bot(discord.Client):

    def get_all_self_members(self):
        """
        only to get the bot's Member object
        on the discord servers
        """
        for guild in self.guilds:
            for member in guild.members:
                if member.id == self.user.id:
                    yield guild, member
                    break
    
    
    def get_self_member(self, channel):
        """bot's Member object from a channel"""
        for member in channel.members:
            if member.id == self.user.id:
                return member


    async def on_ready(self):
        try:
            with open("save.json", 'r') as f:
                save = json.load(f)
        except:
            save = {"nick": "GPT3", "context": ""}
        self.nick = save["nick"]
        self.messages = {}
        self.usernames = {}
        self.context = save["context"]
        self.activated = True
        self.members = dict(self.get_all_self_members())
        self.parameters = {
            "frequency_penalty": 0.5,
            "presence_penalty": 1.0
        }
        print('Logged on as', self.user)


    async def update(self, name, nick, context):
        self.messages = {}
        self.usernames = {}
        self.context = context
        if nick != "":
            self.nick = nick
        if name != "":
            for member in self.members.values():
                await member.edit(nick=name)
        with open("static/profiles/profile.jpg", 'rb') as image:
            await self.user.edit(avatar=image.read())
        with open("save.json", 'w') as f:
            json.dump({"nick": nick, "context": context}, f)
    
    
    async def on_message_delete(self, message):
        chname = message.channel.name
        if chname in self.messages and message in self.messages[chname]:
            self.messages[chname].remove(message)
    
    
    def history_to_prompt(self, history, reply_to=None):
        """
        generates a full text conversation for GPT-3
        - reply_to: if not None, message in the history to reply to
        """
        if reply_to is not None:
            replies = []
            msg_ids = list(map(lambda m: m.id, history))
            while reply_to and reply_to.reference is not None:
                try:
                    i = msg_ids.index(reply_to.reference.message_id)
                    history = history[:i+1]
                    replies.insert(0, reply_to)
                    reply_to = history[i]
                except:
                    reply_to.reference = None
            history += replies
        prompt = ""
        author = ""
        for message in history:
            if message.author != author:
                author = message.author
                username = author.nick or author.name
                if message.author.id == self.user.id:
                    username = self.nick
                prompt += f"\n[{username}] "
            prompt += message.clean_content + "\n"
        prompt += "\n["
        prompt = prompt[-MAX_HISTORY_LEN:]
        return prompt
    
    
    def nick_to_mention(self, nick, guild):
        """transforms a string like "#nick" to "<@id_of_user>" """
        nick = nick.group()
        if nick is not None:
            nick = nick.lstrip("@")
            for member in guild.members:
                if (member.nick or member.name) == nick:
                    return f"<@{member.id}>"
        return "@"+nick


    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        elif message.content.startswith('$'):
            args = split(message.content[1:])
            if args[0].lower() == "ping":
                await message.channel.send('pong')

            elif args[0].lower() == "reset":
                self.mode = None
                self.messages[message.channel.name] = []
                if message.channel.name in self.usernames:
                    self.usernames.pop(message.channel.name)
                await message.channel.send("**[système]** Conversation et mode réinitialisés")
            
            elif args[0].lower() == "activate":
                self.activated = True
                await message.channel.send("**[système]** GPT3 est activé")

            elif args[0].lower() == "deactivate":
                self.activated = False
                await message.channel.send("**[système]** GPT3 est désactivé")

            elif args[0].lower() == "help":
                await message.channel.send("\n".join((
                    "> **Commandes disponibles :**",
                    ">  - `$reset` : réinitialiser la conversation pour GPT-3",
                    ">  - `$deactivate` : désactiver GPT3",
                    ">  - `$activate` : activer GPT3"
                )))
            
            elif args[0].lower() in self.parameters:
                try:
                    value = float(args[1])
                except:
                    await message.channel.send(f"**[système]** Syntaxe: ${args[0].lower()} <valeur>")
                    return
                self.parameters[args[0].lower()] = value
                await message.channel.send(f"**[système]** `{args[0].lower()}` fixé à `{value}`")

        elif self.activated:
            channel = message.channel
            chname = channel.name
            user = message.author
            username = user.nick or user.name

            # updating conversation history
            if chname not in self.messages:
                self.messages[chname] = []
            self.messages[chname] = self.messages[chname][-50:]
            history = self.messages[chname]
            history.append(message)

            # updating the last authors in this channel
            if chname not in self.usernames:
                self.usernames[chname] = []
            if username in self.usernames[chname]:
                self.usernames[chname].remove(username)
            self.usernames[chname].insert(0, username)

            # requesting GPT-3
            prompt = "Conversation entre " \
                 + ", ".join(self.usernames[chname]) \
                 + f" et {self.nick}. {self.context}" \
                 + "\n\n###\n"
            
            # if the message is a reply to ourselves
            if message.reference is not None \
                and message.reference.resolved.author.id == self.user.id:
                prompt += self.history_to_prompt(history, reply_to=message)
                reply = True
            else:
                prompt += self.history_to_prompt(history)
                reply = False
            print(prompt)
            stops = ["\n["] + list(map(lambda s: s+"]", self.usernames[chname]))
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                stop=stops[:4],
                max_tokens=150,
                **self.parameters
            )
            text = response["choices"][0]["text"]
            print(text, '\n')
            if text.startswith(f"{self.nick}]"):
                for msg in text[len(self.nick)+2:].split("\n"):
                    if msg == "": continue
                    msg = re.sub(r"@\w+", lambda s: self.nick_to_mention(s, message.guild), msg)
                    async with channel.typing():
                        await asyncio.sleep(len(msg)/20)
                    if reply:
                        bot_message = await message.reply(msg)
                    else:
                        bot_message = await channel.send(msg)
                    history.append(bot_message)


openai.api_key = GPT3_TOKEN
intents = discord.Intents.all()  # necessitates to be enabled via the Discord developer console

# client = GPT3Bot()
# client.run(TOKEN)
