window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  var messages = document.querySelector('#messages')
  var display_name = localStorage.getItem('username') || 'Guest'

  socket.on('connect', function() {

    socket.emit('authenticate', {username: display_name}, (user) => {
      document.querySelector('#bar-name').textContent = user
      // TODO remove from local storage?
    })
  });

  socket.on('load room', function(data) {
    clearMessages()
    data.history.forEach(function(message) {
      addMessage(message)
    })
    console.log(data.users)
  });

  document.querySelector('#register').onsubmit = function(form) {
    let form_name = document.querySelector('#display-name').value
    socket.emit('register', {username: form_name}, (user) => {
      if (user != undefined) {
        localStorage.setItem('username', user)
        display_name = user
        document.querySelector('#bar-name').textContent = user
      }
    });
    return false
  }

  document.querySelector('#send-message').onsubmit = function(form) {
    let text = document.querySelector('#message-text').value
    socket.emit('send', {user: display_name, text: text});
    return false
  }

  socket.on('receive', function(message) {
    addMessage(message)
  })

  var rooms_list = document.querySelector('#navbar ul')
  rooms_list.querySelectorAll('a').forEach(function(room) {
    room.addEventListener('click', function(){
      socket.emit('join', {user: display_name, room: room.textContent})
    })
  })

  document.querySelector('#create-room').onsubmit = function(form) {
    let name = document.querySelector('#room-name').value
    socket.emit('create room', {name: name, user: display_name}, (data) => {
      if (data != undefined) {
        clearMessages()
      }
    });
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
    console.log('Error: ', data)
  })
}

function addMessage(message) {
  let new_message = document.createElement('div')
  new_message.textContent = message['user'] + ": " + message['text']
  messages.appendChild(new_message)
}

// TODO clear up user list too
function clearMessages() {
  while (messages.firstChild)
    messages.removeChild(messages.firstChild)
}
