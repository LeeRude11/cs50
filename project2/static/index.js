window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  var messages = document.querySelector('#messages')

  socket.on('load room', function(data) {
    while (messages.firstChild)
      messages.removeChild(messages.firstChild)
    data.history.forEach(function(message) {
      addMessage(message)
    })
    console.log(data.users)
  });
  var display_name = localStorage.getItem('username') || 'Guest'

  socket.emit('authenticate', {username: display_name})
  // TODO only if successful
  document.querySelector('#bar-name').textContent = display_name

  document.querySelector('#register').onsubmit = function(form) {
    let form_name = document.querySelector('#display-name').value
    socket.emit('register', {username: form_name});
    return false
  }

  socket.on('registered', function(user) {
    localStorage.setItem('username', user)
    display_name = user
    document.querySelector('#bar-name').textContent = user
  })

  document.querySelector('#send-message').onsubmit = function(form) {
    // TODO check if logged in
    let text = document.querySelector('#message-text').value
    socket.emit('send', {user: display_name, text: text});
    return false
  }

  document.querySelector('#create-room').onsubmit = function(form) {
    let name = document.querySelector('#room-name').value
    socket.emit('create room', {name: name, user: display_name});
    return false
  }
  socket.on('room created', function(data) {
    while (messages.firstChild)
      messages.removeChild(messages.firstChild)
    // TODO users list
  })

  // TODO callback in emit send?
  socket.on('receive', function(message) {
    addMessage(message)
  })

  var rooms_list = document.querySelector('#navbar ul')
  rooms_list.querySelectorAll('a').forEach(function(room) {
    room.addEventListener('click', function(){
      socket.emit('join', {user: display_name, room: room.textContent})
    })
  })

  socket.on('new room', function(room_name) {
    let new_room = document.createElement('li')
    let new_room_link = document.createElement('a')
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
