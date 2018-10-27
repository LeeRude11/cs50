import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

LIMIT = 100
channels = {"main": {
        "history": deque([], maxlen=LIMIT),
        "current_users": []
        }
    }


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("create channel")
def create_channel(data):
    print("\nTEST\n")
    emit("TODO")


@socketio.on("connect")
def connect():
    emit("load history", list(channels["main"]["history"]))


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
    channels["main"]["history"].append(message)
    emit("receive", message, broadcast=True)
