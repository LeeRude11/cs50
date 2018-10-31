import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

LIMIT = 100
# TODO current users
channels = {"main": {
        "history": deque([], maxlen=LIMIT),
        "current_users": []
        }
    }
users = {}


@app.route("/")
def index():
    return render_template("index.html", channels=channels.keys())


@socketio.on("connect")
def connect():
    pass


@socketio.on("authenticate")
def authenticate(data):
    user = data.get("username")
    if user == "Guest":
        last_room = "main"
    elif users.get(user) is None:
        emit("error", "No such user")
    elif users[user]["sid"] is not None:
        emit("error", "User is active")
    else:
        last_room = users[user]["room"]

    join_room(last_room)
    emit("load history", list(channels[last_room]["history"]))


@socketio.on("disconnect")
def disconnect():
    # TODO remove SID from the user
    request.sid
    users
    return None


@socketio.on("register")
def login(data):
    user = data.get("username")
    if user == "Guest":
        emit("error", "Guest not allowed")
        return None
    if user in users:
        emit("error", "User already exists")
        return None
    users[user] = {"sid": request.sid, "room": "main"}
    emit("registered", user)


@socketio.on("create channel")
def create_channel(data):
    new_channel = data.get("name")
    if new_channel in (None, ""):
        emit("error")
        return 1
    if new_channel in channels:
        emit("error")
        return 1
    user = data.get("user")
    if user == "Guest":
        emit("error", "Guests can not create rooms")
        return None
    if users.get(user) is None:
        emit("error", "No such user")
        return None
    if users[user]["sid"] != request.sid:
        emit("error", "Wrong SID")
        return None

    channels[new_channel] = {
        "history": deque([], maxlen=LIMIT),
        "current_users": []
    }

    leave_room(users[user]["room"])
    join_room(new_channel)
    users[user]["room"] = new_channel

    emit("channel created", new_channel, broadcast=True)


@socketio.on("join")
def on_join(data):
    user = data.get("user")
    room = data.get("room")
    if user is None or room is None:
        emit("error", "Nones passed")
        return None
    if users.get(user) is None:
        emit("error", "No such user")
        return None
    if users[user]["sid"] != request.sid:
        emit("error", "Wrong SID")
        return None

    last_room = users[user]["room"]
    send(user + ' has left the room.', room=last_room)
    leave_room(last_room)
    join_room(room)
    users[user]["room"] = room

    # TODO send emit?
    emit("load history", list(channels[room]["history"]))
    send(user + ' has entered the room.', room=room)


@socketio.on("send")
def send_message(data):
    user = data.get("user")
    if user == "Guest":
        room = "main"
    elif users.get(user) is None:
        emit("error", "No such user")
        return None
    elif users[user]["sid"] != request.sid:
        emit("error", "SID is not correct")
        return None
    else:
        room = users[user]["room"]

    message = {
        "user": user,
        "text": data.get("text")
    }
    channels[room]["history"].append(message)
    emit("receive", message, room=room)
