import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

LIMIT = 100
# TODO current users
rooms = {"main": {
        "history": deque([], maxlen=LIMIT),
        "current_users": []
        }
    }
users = {}


@app.route("/")
def index():
    return render_template("index.html", rooms=rooms.keys())


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
        user, last_room = "Guest", "main"
    else:
        last_room = users[user]["room"]
        users[user]["sid"] = request.sid

    join_room(last_room)
    enter_live_room(user, last_room)

    return user


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
        rooms[room]["current_users"].remove(user)
    except(ValueError):
        print("\nNon-existing user disconnected")
        print(rooms[room]["current_users"])
        print(user, "\n")
    emit("notify", {"user": user, "action": "disconnect"}, room=room)


@socketio.on("register")
def register(data):
    user = data.get("username")
    if user == "Guest":
        emit("error", "Guest as name is not allowed")
    elif user in users:
        emit("error", f"User {user} already exists")
    else:
        room = "main"
        users[user] = {"sid": request.sid, "room": room}
        rooms[room]["current_users"].remove("Guest")
        rooms[room]["current_users"].append(user)
        emit("notify", {"user": user, "action": "register"}, room=room)
        return user
    return None


@socketio.on("create room")
def create_room(data):
    new_room = data.get("name")
    user = data.get("user")
    if user == "Guest":
        emit("error", "Guests can not create rooms")
    elif check_user(user) is False:
        return None
    elif new_room in (None, ""):
        emit("error", "room name can not be empty")
    elif new_room in rooms:
        emit("error", "room with this name already exists")
    else:
        rooms[new_room] = {
            "history": deque([], maxlen=LIMIT),
            "current_users": [user]
        }

        switch_rooms(user, new_room)

        emit("new room", new_room, broadcast=True)
        return True
    return None


@socketio.on("join")
def on_join(data):
    # TODO guests are restricted
    # they can't be in users, so they blocked anyway
    # emit an error for UX
    user = data.get("user")
    room = data.get("room")
    if room not in rooms:
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
    rooms[room]["history"].append(message)
    emit("receive", message, room=room)


def switch_rooms(user, new_room):
    last_room = users[user]["room"]
    rooms[last_room]["current_users"].remove(user)
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
        else:
            return True
    elif users[user]["sid"] != request.sid:
        emit("error", "User is active")
    else:
        return True
    return False


def enter_live_room(user, room):
    rooms[room]["current_users"].append(user)
    emit("load room", {
        "history": list(rooms[room]["history"]),
        "users": rooms[room]["current_users"]
        })
    emit("notify", {"user": user, "action": "enter"}, room=room)
