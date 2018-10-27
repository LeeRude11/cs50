import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

LIMIT = 100
history = {"main": deque([], maxlen=LIMIT)}
current_users = {"main": []}


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("create channel")
def create_channel(data):
    emit("TODO")


@socketio.on("connect")
def connect():
    emit("load history", list(history["main"]))


@socketio.on("enter")
def new_enter(data):
    emit("new enter")


@socketio.on("send")
def send_message(data):
    # TODO check errors
    message = {
        "name": data.get("name"),
        "text": data.get("text")
    }
    history["main"].append(message)
    emit("receive", message, broadcast=True)
