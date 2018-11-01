import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
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
    # TODO reconnecting to a restarted app causes all kinds of trouble
    pass


@socketio.on("authenticate")
def authenticate(data):
    user = data.get("username")
    if user == "Guest":
        last_room = "main"
    elif check_user(user, auth=True) is False:
        return None
    else:
        last_room = users[user]["room"]
        users[user]["sid"] = request.sid

    join_room(last_room)
    enter_live_room(user, last_room)


@socketio.on("disconnect")
def disconnect():
    # TODO sloppy search
    user = next((k for k, v in users.items() if v["sid"] == request.sid),
                "Guest")
    if user != "Guest":
        users[user]["sid"] = None
        room = users[user]["room"]
    else:
        room = "main"
    try:
        channels[room]["current_users"].remove(user)
    except(ValueError):
        print("\nNon-existing user disconnected\n")
    emit("notify", {"user": user, "action": "disconnect"}, room=room)


@socketio.on("register")
def register(data):
    user = data.get("username")
    if user == "Guest":
        emit("error", "Guest as name is not allowed")
    elif user in users:
        emit("error", "User already exists")
    else:
        room = "main"
        users[user] = {"sid": request.sid, "room": room}
        channels[room]["current_users"].remove("Guest")
        channels[room]["current_users"].append(user)
        emit("registered", user)
        emit("notify", {"user": user, "action": "register"}, room=room)


@socketio.on("create channel")
def create_channel(data):
    new_channel = data.get("name")
    user = data.get("user")
    if user == "Guest":
        emit("error", "Guests can not create rooms")
    elif check_user(user) is False:
        return None
    elif new_channel in (None, ""):
        emit("error", "Channel name can not be empty")
    elif new_channel in channels:
        emit("error", "Channel with this name already exists")
    else:
        channels[new_channel] = {
            "history": deque([], maxlen=LIMIT),
            "current_users": [user]
        }

        switch_rooms(user, new_channel)

        emit("channel created")
        emit("new channel", new_channel, broadcast=True)


@socketio.on("join")
def on_join(data):
    # TODO guests are restricted
    user = data.get("user")
    room = data.get("room")
    if room not in channels:
        emit("error", "No such room")
    elif check_user(user) is False:
        return None
    else:
        switch_rooms(user, room)
        enter_live_room(user, room)


@socketio.on("send")
def send_message(data):
    user = data.get("user")
    if user == "Guest":
        room = "main"
    elif check_user(user) is False:
        return None
    else:
        room = users[user]["room"]

    message = {
        "user": user,
        "text": data.get("text")
    }
    channels[room]["history"].append(message)
    emit("receive", message, room=room)


def switch_rooms(user, new_room):
    last_room = users[user]["room"]
    channels[last_room]["current_users"].remove(user)
    emit("notify", {"user": user, "action": "leave"}, room=last_room)
    leave_room(last_room)
    join_room(new_room)
    users[user]["room"] = new_room


def check_user(user, auth=False):
    if users.get(user) is None:
        emit("error", "No such user")
    elif auth:
        if users[user]["sid"] is not None:
            emit("error", "User is active")
    elif users[user]["sid"] != request.sid:
        emit("error", "Wrong SID")
    else:
        return True
    return False


def enter_live_room(user, room):
    channels[room]["current_users"].append(user)
    emit("load room", {
        "history": list(channels[room]["history"]),
        "users": channels[room]["current_users"]
        })
    emit("notify", {"user": user, "action": "enter"}, room=room)
