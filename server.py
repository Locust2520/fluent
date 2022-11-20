from flask import Flask, render_template, request, redirect
from flask_basicauth import BasicAuth
from werkzeug.utils import secure_filename
from threading import Thread
import bot
import asyncio
import shutil
import time
import json
import os


app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = os.getenv("WEB_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = os.getenv("WEB_PASSWORD")
basic_auth = BasicAuth(app)


with open("history.json") as f:
    history = json.load(f)


def equal_dict(a, b):
    for k in a:
        if k not in b:
            return False
        if a[k] != b[k]:
            return False
        return True


def bot_start():
    global loop, client
    client = bot.GPT3Bot(intents=bot.intents)
    loop = asyncio.get_event_loop()
    loop.create_task(client.start(bot.DISCORD_TOKEN))
    Thread(target=loop.run_forever).start()


@app.route("/")
@basic_auth.required
def index():
    member, *_ = client.members.values()
    return render_template("index.html",
                           name=member.nick,
                           nick=client.nick,
                           context=client.context,
                           history=enumerate(history))


@app.route("/upload", methods=["POST"])
@basic_auth.required
def upload():
    name = request.form["name"]
    nick = request.form["nick"]
    context = request.form["context"]
    member, *_ = client.members.values()
    # adding current character in history
    with open("history.json", 'r') as f:
        new_ch = {
            "name": member.nick,
            "nick": client.nick,
            "context": client.context
        }
        for ch in history[::-1]:
            if equal_dict(ch, new_ch):
                history.remove(ch)
        history.insert(0, new_ch)
        shutil.copy(
            "static/profiles/profile.jpg",
            f"static/profiles/{member.nick}.jpg"
        )
    with open("history.json", 'w') as f:
        json.dump(history, f)
    
    # download image
    file = request.files['image']
    if file.filename != '':
        filename = secure_filename(file.filename)
        file.save("static/profiles/profile.jpg")
    elif os.path.isfile(f"static/profiles/{name}.jpg"):
        shutil.copy(
            f"static/profiles/{name}.jpg",
            "static/profiles/profile.jpg"
        )
    
    task = asyncio.run_coroutine_threadsafe(client.update(name, nick, context), loop)
    task.result()
    return redirect("/")


@app.route("/delete")
@basic_auth.required
def delete():
    i = int(request.args.get("index"))
    history.pop(i)
    with open("history.json", 'w') as f:
        json.dump(history, f)
    return redirect("/")


bot_start()
app.run(debug=False, host="0.0.0.0", port=8080)
