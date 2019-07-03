import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
import re

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
users = {DEF_NAME: {"sid": None, "room": DEF_ROOM}}


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def connect():
    """Provide connected user with a list of rooms"""
    emit("load list of rooms", list(rooms.keys()))


@socketio.on("authenticate")
def authenticate(data):
    """Route user to last visited room if authorized or DEF_ROOM"""
    user = data.get("username")

    if check_user(user, auth=True, guest_error=None) is False:
        user = DEF_NAME
    if user != DEF_NAME:
        users[user]["sid"] = request.sid
    last_room = users[user]["room"]

    enter_live_room(user, last_room)

    return user


@socketio.on("disconnect")
def disconnect():
    """Remove disconnected user from room"""
    # TODO sloppy search
    user = next((k for k, v in users.items() if v["sid"] == request.sid),
                DEF_NAME)
    if user != DEF_NAME:
        users[user]["sid"] = None
    leave_current_room(user, action="disconnected")


@socketio.on("register")
def register(data):
    """Return True when successfully registered a user, None otherwise"""
    user = data.get("username")
    if user in users:
        emit("error", {"text": f"User {user} already exists"})
    elif not verify_input(user):
        return None
    elif next((k for k, v in users.items() if v["sid"] == request.sid),
              None) is not None:
        emit("error", {"text": "Can not register authorized users"})
    else:
        room = DEF_ROOM
        users[user] = {"sid": request.sid, "room": room}
        rooms[room]["current_users"].remove(DEF_NAME)
        rooms[room]["current_users"].append(user)
        emit("notify", {"user": user, "action": "registered"}, room=room)
        return True
    return None


@socketio.on("create room")
def create_room(data):
    """Create room, move the creator, return True"""
    new_room = data.get("name")
    user = data.get("user")

    if check_user(user, guest_error="Guests can not create rooms") is False:
        return None
    elif not verify_input(new_room):
        return None
    elif new_room in rooms:
        emit("error", {"text": "Room with this name already exists"})
    else:
        rooms[new_room] = {
            "history": deque([], maxlen=LIMIT),
            "current_users": []
        }
        emit("new room", new_room, broadcast=True)
        switch_rooms(user, new_room)
        return True


@socketio.on("join")
def on_join(data):
    """Move user from last room to provided room"""
    user = data.get("user")
    room = data.get("room")
    if check_user(user, guest_error="Guests can not change rooms") is False:
        return None
    elif room not in rooms:
        emit("error", {"text": "No such room"})
    elif room == users[user]["room"]:
        emit("error", {"text": "Already joined this room"})
    else:
        switch_rooms(user, room)


@socketio.on("send")
def send_message(data):
    """Return True when successfully emitted a message from user"""
    user = data.get("user")
    if check_user(user, guest_error=None) is False:
        return None
    else:
        room = users[user]["room"]

    message = {
        "user": user,
        "text": data.get("text")
    }
    rooms[room]["history"].append(message)
    emit("receive", message, room=room, include_self=False)
    return True


@socketio.on("delete user")
def delete_user(data):
    """Delete a user, set session to default"""
    user = data.get("user")

    if check_user(user, guest_error="Guests can not be deleted") is False:
        return None

    leave_current_room(user)
    users.pop(user)
    enter_live_room(DEF_NAME, DEF_ROOM)
    return True


def switch_rooms(user, new_room):
    """Leave room, set new room in users dict, join new room"""
    leave_current_room(user)
    users[user]["room"] = new_room
    enter_live_room(user, new_room)


def verify_input(a_name):
    """Return True if provided name is of proper format"""
    pattern = re.compile("^[a-zA-Z]+[a-zA-Z0-9]{2,}$")
    if pattern.match(a_name) is None:
        emit("error", {"text": """Names must be at least 3 characters long,
        can only contain numbers and English letters
        and must start with letters"""})
        return False
    return True


def check_user(user, auth=False, guest_error="Not allowed"):
    """Returns boolean of user passing checks"""
    if auth:
        # User must be inactive before authorization
        target_sid = None
    else:
        target_sid = request.sid

    if user == DEF_NAME:
        if guest_error:
            emit("error", {"text": guest_error})
        # Some functions accept guest users
        else:
            return True
    elif users.get(user) is None:
        emit("error", {"text": "Your username was not found", "user": user})
    elif users[user]["sid"] != target_sid:
        emit("error", {"text": "User already in active session", "user": user})
    else:
        return True
    return False


def leave_current_room(user, action="left"):
    """Leave room and notify its users"""
    room = users[user]["room"]
    try:
        rooms[room]["current_users"].remove(user)
    except(ValueError):
        print("\nUser disconnected before authorization")
        return

    leave_room(room)
    emit("notify", {"user": user, "action": action}, room=room)


def enter_live_room(user, room):
    """Join room, load history and user list, notify its users"""
    join_room(room)
    emit("load room", {
        "room": room,
        "history": list(rooms[room]["history"]),
        "users": rooms[room]["current_users"]
        })
    # load room without the new user - he's added with notify
    rooms[room]["current_users"].append(user)
    emit("notify", {"user": user, "action": "entered"}, room=room)
