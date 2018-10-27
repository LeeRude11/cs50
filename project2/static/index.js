window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);

  var messages = document.querySelector('#messages')
  socket.on('load history', function(history) {
    history.forEach(function(message) {
      addMessage(message)
    })
  });
  var display_name = localStorage.getItem('username') || 'Guest'
  document.querySelector('#enter').onsubmit = function(form) {
    let form_name = document.querySelector('#display-name').value
    socket.emit('enter', {name: form_name});
    // TODO delete the form
    localStorage.setItem('username', form_name)
    display_name = form_name
    document.querySelector('#bar-name').innerHTML = display_name
    return false
  }
  document.querySelector('#bar-name').innerHTML = display_name

  document.querySelector('#send').onsubmit = function(form) {
    // TODO check if logged in
    let text = document.querySelector('#message-text').value
    socket.emit('send', {name: display_name, text: text});
    return false
  }

  socket.on('receive', function(message) {
    addMessage(message)
  })

}

function addMessage(message) {
  let new_message = document.createElement('div')
  new_message.innerHTML = message['name'] + ": " + message['text']
  messages.appendChild(new_message)
}
