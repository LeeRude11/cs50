window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  var messages = document.querySelector('#messages')

  socket.on('load history', function(history) {
    history.forEach(function(message) {
      addMessage(message)
    })
  });
  var display_name = localStorage.getItem('username') || 'Guest'

  socket.emit('authenticate', {username: display_name})
  document.querySelector('#bar-name').innerHTML = display_name

  document.querySelector('#register').onsubmit = function(form) {
    let form_name = document.querySelector('#display-name').value
    socket.emit('register', {username: form_name});
    return false
  }

  socket.on('registered', function(user) {
    localStorage.setItem('username', user)
    display_name = user
    document.querySelector('#bar-name').innerHTML = display_name
  })

  document.querySelector('#send-message').onsubmit = function(form) {
    // TODO check if logged in
    let text = document.querySelector('#message-text').value
    socket.emit('send', {user: display_name, text: text});
    return false
  }

  document.querySelector('#create-channel').onsubmit = function(form) {
    let name = document.querySelector('#channel-name').value
    socket.emit('create channel', {name: name, user: display_name});
    return false
  }

  // TODO callback in emit send?
  socket.on('receive', function(message) {
    addMessage(message)
  })

  var channels_list = document.querySelector('#navbar ul')
  channels_list.querySelectorAll('li').forEach(function(channel) {
    channel.addEventListener('click', function(){
      socket.emit('join', {user: display_name, room: channel.innerHTML})
    })
  })

  socket.on('channel created', function(data) {
    let new_channel = document.createElement('li')
    new_channel.innerHTML = data
    new_channel.addEventListener('click', function(){
      socket.emit('join', {user: display_name, room: new_channel.innerHTML})
    })
    channels_list.appendChild(new_channel)
  })

  socket.on('error', function(data) {
    console.log('Error', data)
  })
}

function addMessage(message) {
  let new_message = document.createElement('div')
  new_message.innerHTML = message['user'] + ": " + message['text']
  messages.appendChild(new_message)
}
