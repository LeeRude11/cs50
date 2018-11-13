window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  var messages = document.getElementById('messages')
  var display_name = localStorage.getItem('username') || 'Guest'
  var rooms_list = document.querySelector('#rooms-list ul')
  var users_list = document.querySelector('#users-list ul')
  var error_div = document.getElementById('error')

  socket.on('connect', function() {

    socket.emit('authenticate', {username: display_name}, (user) => {
      document.getElementById('bar-name').textContent = user
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
    socket.emit('register', {username: form_name}, (user) => {
      if (user != undefined) {
        localStorage.setItem('username', user)
        display_name = user
        document.getElementById('bar-name').textContent = user
      }
    });
    return false
  }

  document.getElementById('send-message').onsubmit = function(form) {
    let text = document.getElementById('message-text').value
    socket.emit('send', {user: display_name, text: text});
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
      removeUser("Guest")
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
    socket.emit('create room', {name: name, user: display_name});
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
    console.log('Error: ', data)
    error_div.textContent = data.text
  })

  function addMessage(message) {
    let new_message = document.createElement('div')
    new_message.textContent = message['user'] + ": " + message['text']
    messages.appendChild(new_message)
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
}
