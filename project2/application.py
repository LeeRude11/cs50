import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

LIMIT = 100
# default room to enter with default name
DEF_ROOM = "main"
DEF_NAME = "Guest"
rooms = {DEF_ROOM: {
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
    pass


@socketio.on("authenticate")
def authenticate(data):
    user = data.get("username")
    if user == DEF_NAME:
        last_room = DEF_ROOM
    elif check_user(user, auth=True) is False:
        user, last_room = DEF_NAME, DEF_ROOM
    else:
        last_room = users[user]["room"]
        users[user]["sid"] = request.sid

    enter_live_room(user, last_room)

    return user


@socketio.on("disconnect")
def disconnect():
    # TODO sloppy search
    user = next((k for k, v in users.items() if v["sid"] == request.sid),
                DEF_NAME)
    if user != DEF_NAME:
        users[user]["sid"] = None
        room = users[user]["room"]
    else:
        room = DEF_ROOM
    try:
        rooms[room]["current_users"].remove(user)
    except(ValueError):
        print("\nNon-existing user disconnected")
        print(rooms[room]["current_users"])
        print(user, "\n")
    emit("notify", {"user": user, "action": "disconnected"}, room=room)


@socketio.on("register")
def register(data):
    user = data.get("username")
    # TODO list of inappropriate names
    if user == "Guest":
        emit("error", {"text": "Guest as name is not allowed"})
    elif user in users:
        emit("error", {"text": f"User {user} already exists"})
    else:
        room = DEF_ROOM
        users[user] = {"sid": request.sid, "room": room}
        rooms[room]["current_users"].remove(DEF_NAME)
        rooms[room]["current_users"].append(user)
        emit("notify", {"user": user, "action": "registered"}, room=room)
        return user
    return None


@socketio.on("create room")
def create_room(data):
    new_room = data.get("name")
    user = data.get("user")
    if user == DEF_NAME:
        emit("error", {"text": "Guests can not create rooms"})
    elif check_user(user) is False:
        return None
    elif new_room in (None, ""):
        emit("error", {"text": "Room name can not be empty"})
    elif new_room in rooms:
        emit("error", {"text": "Room with this name already exists"})
    else:
        rooms[new_room] = {
            "history": deque([], maxlen=LIMIT),
            "current_users": []
        }

        emit("new room", new_room, broadcast=True)

        switch_rooms(user, new_room)


@socketio.on("join")
def on_join(data):
    user = data.get("user")
    room = data.get("room")
    if user == DEF_NAME:
        emit("error", {"text": "Guests can not change rooms"})
    elif room not in rooms:
        emit("error", {"text": "No such room"})
    elif check_user(user) is False:
        return None
    elif room == users[user]["room"]:
        emit("error", {"text": "Already joined this room"})
    else:
        switch_rooms(user, room)


@socketio.on("send")
def send_message(data):
    user = data.get("user")
    if user == DEF_NAME:
        room = DEF_ROOM
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


@socketio.on("delete user")
def delete_user(data):
    user = data.get("user")
    if check_user(user) is False:
        return None
    room = users[user]["room"]
    users.pop(user)
    rooms[room]["current_users"].remove(user)

    emit("notify", {"user": user, "action": "left"}, room=room)

    # don't reload if user is here
    if room == DEF_ROOM:
        emit("notify", {"user": DEF_NAME, "action": "entered"}, room=room)
    else:
        leave_room(room)
        enter_live_room(DEF_NAME, DEF_ROOM)
    return True


def switch_rooms(user, new_room):
    last_room = users[user]["room"]
    rooms[last_room]["current_users"].remove(user)
    leave_room(last_room)
    emit("notify", {"user": user, "action": "left"}, room=last_room)
    users[user]["room"] = new_room

    enter_live_room(user, new_room)


def check_user(user, auth=False):
    if auth:
        target_sid = None
    else:
        target_sid = request.sid

    if users.get(user) is None:
        emit("error", {"text": "No such user", "user": user})
    elif users[user]["sid"] != target_sid:
        emit("error", {"text": "User is active", "user": user})
    else:
        return True
    return False


def enter_live_room(user, room):
    join_room(room)
    emit("load room", {
        "room": room,
        "history": list(rooms[room]["history"]),
        "users": rooms[room]["current_users"]
        })
    # load room without the new user - he's added with notify
    rooms[room]["current_users"].append(user)
    emit("notify", {"user": user, "action": "entered"}, room=room)
