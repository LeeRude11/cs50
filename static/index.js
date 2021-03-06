window.onload = function() {
  const socket = io.connect('http://' + document.domain + ':' + location.port);

  const DEF_NAME = 'Guest'
  const MSG_LIMIT = 100
  let display_name = localStorage.getItem('username') || DEF_NAME

  const messages = document.getElementById('messages')
  const users_list = document.querySelector('#users-list ul')
  const error_div = document.getElementById('error')
  const discon_div = document.getElementById('disconnection')

  socket.on('connect', function() {

    discon_div.hidden = true;
    socket.emit('authenticate', {username: display_name}, (user) => {
      setUser(user)
    })
  });

  socket.on('disconnect', function() {
    discon_div.hidden = false;
  })

  const rooms_list = document.querySelector('#rooms-list ul')
  socket.on('load list of rooms', function(list_of_rooms) {
    while (rooms_list.firstChild) {
      rooms_list.removeChild(rooms_list.firstChild)
    }
    list_of_rooms.forEach((room) => {
      addRoom(room)
    })
  })

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

  document.getElementById('register').onsubmit = () => {
    let form_name = document.getElementById('display-name').value
    if (isEmpty(form_name)) {
      flashError('Username can not be empty')
    } else {
      socket.emit('register', {username: form_name}, (response) => {
        if (response === true) {
          localStorage.setItem('username', form_name)
          setUser(form_name)
          document.getElementById('display-name').value = ""
        }
      });
    }
    return false
  }

  document.getElementById('send-message').onsubmit = () => {
    let text = document.getElementById('message-text').value
    document.getElementById('message-text').value = ""
    if (isEmpty(text)) {
      flashError('Can not send an empty message')
    }
    else {
      let message = {user: display_name, text: text}
      let pending_message = addMessage(message)
      if (socket.disconnected) {
        pending_message.classList.add('failed')
      }
      else {
        socket.emit('send', message, (response) => {
          if (response !== true) {
            pending_message.classList.add('failed')
          }
        });
      }
    }
    return false
  }

  socket.on('receive', function(message) {
    addMessage(message)
  })

  socket.on('notify', function(data) {
    let user = data.user
    let message = {
      user: "User " + user,
      text: "has " + data.action + "."
    }
    addMessage(message, true)
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

  document.getElementById('create-room').onsubmit = () => {
    let name = document.getElementById('room-name').value
    if (isEmpty(name)) {
      flashError('Room name can not be empty')
    }
    else {
      socket.emit('create room', {name: name, user: display_name}, (response) => {
          if (response === true)
            document.getElementById('room-name').value = ""
        }
      );
    }
    return false
  }

  socket.on('new room', function(room_name) {
    addRoom(room_name)
  })

  socket.on('error', function(data) {
    if (data.user) {
      data.text += ": " + data.user + ". Your name has been set to Guest"
      document.getElementById('display-name').value = data.user
      confirm_div.hidden = false
    }
    flashError(data.text)
  })

  const confirm_div = document.getElementById('confirmation')
  document.getElementById('exit').onclick = () => {
    confirm_div.hidden = false
  }
  document.getElementById('confirm-yes').onclick = () => {
    confirm_div.hidden = true
    if (display_name === DEF_NAME) {
      localStorage.removeItem('username')
    } else {
      socket.emit('delete user', {user: display_name}, (response) => {
        if (response === true) {
          localStorage.removeItem('username')
          setUser(DEF_NAME)
        }
      })
    }
  }
  document.getElementById('confirm-no').onclick = () => {
    confirm_div.hidden = true
  }

  document.getElementById('error-button').onclick = () => {
    error_div.hidden = true
  }
  document.getElementById('discon-button').onclick = () => {
    discon_div.hidden = true
  }

  function addMessage(message, notify) {
    keepWithinLimit()
    let new_message = document.createElement('div')
    let symbol = ': '
    if (notify !== undefined) {
      symbol = ' '
      new_message.classList.add('notify')
    }
    new_message.textContent = message['user'] + symbol + message['text']
    messages.appendChild(new_message)
    newMessageNotice()
    return new_message
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

  function addRoom(room_name) {
    let new_room = document.createElement('li')
    let new_room_link = document.createElement('a')
    new_room_link.href = '#'
    new_room_link.textContent = room_name
    new_room_link.addEventListener('click', () => {
      if (new_room_link.textContent === document.querySelector('.active').textContent) {
        return
      }
      socket.emit('join', {user: display_name, room: room_name})
    })
    new_room.appendChild(new_room_link)
    rooms_list.appendChild(new_room)
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
    const error_text = document.getElementById('error-text')
    error_text.textContent = 'Error: ' + text
    error_div.hidden = false
  }

  function keepWithinLimit() {
    while (messages.childNodes.length > MSG_LIMIT) {
      messages.removeChild(messages.firstChild)
    }
  }

  function newMessageNotice() {
    const scrollTopMax = () => {
      return messages.scrollHeight - messages.clientHeight
    }
    const closeToBottom = () => {
      return messages.scrollTop + 50 > scrollTopMax()
    }

    if (closeToBottom()) {
      messages.scrollTop = scrollTopMax()
    } else {
      const notice = document.getElementById('message-notice')
      notice.hidden = false
      messages.addEventListener('scroll', () => {
        if (closeToBottom()) {
          notice.hidden = true
        }
      })
    }
  };
  // https://stackoverflow.com/a/28485815
  function isEmpty(str){
    return !str.replace(/\s+/, '').length;
  }
}
