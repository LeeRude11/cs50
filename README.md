# Flask-SocketIO Web Chat

A Flask-based SocketIO web chat application built using
[Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO).

# Features
* **Main room** - a default space to which guests are restricted
* **User authorization** - utilizing localStorage and Session ID: username is bound while he/she is connected
* **Rooms creation** - authorized users can create rooms unavailable for guests
* **User deletion** - give up your name and become a peasant guest once again
* **History** - up to 100 messages for each room

# Requirements
[Pipenv installed.](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv)

# Usage
First-time only - install requirements from Pipfile:
```
$ pipenv install
```
Enter environment and start server:
```
$ pipenv shell
$ python application.py
```
