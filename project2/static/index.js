window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  const DEF_NAME = 'Guest'
  var display_name = localStorage.getItem('username') || DEF_NAME

  var messages = document.getElementById('messages')
  var rooms_list = document.querySelector('#rooms-list ul')
  var users_list = document.querySelector('#users-list ul')
  var error_div = document.getElementById('error')

  socket.on('connect', function() {

    socket.emit('authenticate', {username: display_name}, (user) => {
      setUser(user)
    })
  });

  socket.on('load room', function(data) {
    clearRoom()
    data.history.forEach(function(message) {
      addMessage(message)
    })
    data.users.forEach(function(user) {
      addUser(user)
    })
    document.getElementById('users-count').textContent = data.users.length
    setActiveRoom(data.room)
  });

  document.getElementById('register').onsubmit = function(form) {
    let form_name = document.getElementById('display-name').value
    if (isEmpty(form_name)) {
      flashError('Username can not be empty')
    } else {
      socket.emit('register', {username: form_name}, (user) => {
        if (user != undefined) {
          localStorage.setItem('username', user)
          setUser(user)
        }
      });
    }
    return false
  }

  document.getElementById('send-message').onsubmit = function(form) {
    let text = document.getElementById('message-text').value
    document.getElementById('message-text').value = ""
    if (isEmpty(text)) {
      flashError('Can not send an empty message')
    }
    else {
      message = {user: display_name, text: text}
      let pending_message = addMessage(message, pending=true)
      socket.emit('send', message, (response) => {
        pending_message.classList.remove('pending')
        if (response !== true) {
          pending_message.classList.add('failed')
        }
      });
    }
    return false
  }

  socket.on('receive', function(message) {
    addMessage(message)
  })

  socket.on('notify', function(data) {
    let user = data.user
    let message = {
      user: "ROOM",
      text: "User " + user + " has " + data.action + "."
    }
    addMessage(message)
    if (data.action === "entered") {
      addUser(user)
    } else if (["left", "disconnected"].includes(data.action)) {
      removeUser(user)
    } else {
      // "registered"
      removeUser(DEF_NAME)
      addUser(user)
    }
  })

  rooms_list.querySelectorAll('a').forEach(function(room) {
    room.addEventListener('click', function(){
      if (room.textContent == document.querySelector('.active').textContent) {
        return
      }
      socket.emit('join', {user: display_name, room: room.textContent})
    })
  })

  document.getElementById('create-room').onsubmit = function(form) {
    let name = document.getElementById('room-name').value
    if (isEmpty(name)) {
      flashError('Room name can not be empty')
    }
    else {
      socket.emit('create room', {name: name, user: display_name});
    }
    return false
  }

  socket.on('new room', function(room_name) {
    let new_room = document.createElement('li')
    let new_room_link = document.createElement('a')
    new_room_link.href = '#'
    new_room_link.textContent = room_name
    new_room_link.addEventListener('click', function(){
      socket.emit('join', {
        user: display_name,
        room: room_name
      })
    })
    new_room.appendChild(new_room_link)
    rooms_list.appendChild(new_room)
  })

  socket.on('error', function(data) {
    if (data.user) {
      document.getElementById('display-name').value = data.user
      // TODO if they don't exist, it's OK to register it
      console.log('Register a new username instead of ' + data.user)
      localStorage.removeItem('username')
    }
    flashError(data.text)
  })

  var confirm_div = document.getElementById('confirmation')
  document.getElementById('exit').onclick = () => {
    confirm_div.hidden = false
  }
  document.getElementById('confirm-yes').onclick = () => {
    confirm_div.hidden = true
    socket.emit('delete user', {user: display_name}, (response) => {
      if (response === true) {
        localStorage.removeItem('username')
        setUser(DEF_NAME)
      }
    })
  }
  document.getElementById('confirm-no').onclick = () => {
    confirm_div.hidden = true
  }

  document.getElementById('error-button').onclick = () => {
    error_div.hidden = true
  }

  function addMessage(message, pending=false) {
    let new_message = document.createElement('div')
    new_message.textContent = message['user'] + ": " + message['text']
    messages.appendChild(new_message)
    if (pending) {
      new_message.classList.add('pending')
      return new_message
    }
  }

  function addUser(user) {
    document.getElementById('users-count').textContent++
    let new_user = document.createElement('li')
    new_user.textContent = user
    users_list.appendChild(new_user)
  }

  function removeUser(user) {
    document.getElementById('users-count').textContent--
    for (let user_li of users_list.childNodes) {
      if (user_li.textContent === user) {
        users_list.removeChild(user_li)
        break
      }
    }
  }

  function clearRoom() {
    while (messages.firstChild)
    messages.removeChild(messages.firstChild)
    while (users_list.firstChild)
    users_list.removeChild(users_list.firstChild)
  }

  function setActiveRoom(room) {
    let previous = document.querySelector('.active')
    if (previous !== null) {
      previous.classList.remove('active')
    }
    document.getElementById('current-room').textContent = room
    for (let room_li of rooms_list.childNodes) {
      if (room_li.textContent === room) {
        room_li.classList.add('active')
        break
      }
    }
  }

  function setUser(user) {
    document.getElementById('bar-name').textContent = display_name = user
    toggleForm()
  }

  function toggleForm() {
    document.getElementById('register').hidden = display_name !== DEF_NAME
    document.getElementById('exit').hidden = display_name === DEF_NAME
    document.getElementById('create-room').hidden = display_name === DEF_NAME
  }

  function flashError(text) {
    var error_text = document.getElementById('error-text')
    error_text.textContent = 'Error: ' + text
    error_div.hidden = false
  }
  // https://stackoverflow.com/a/28485815
  function isEmpty(str){
    return !str.replace(/\s+/, '').length;
  }
}
