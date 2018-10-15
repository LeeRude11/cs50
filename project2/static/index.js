window.onload = function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);
  socket.on('connect', function() {
    socket.emit('my event', {data: 'I\'m connected!'});
  });
  var display_name = localStorage.getItem("username")
  if (!display_name) {
    document.querySelector('#bar-name').innerHTML = 'Guest'
    document.querySelector('#enter').onsubmit = function(form) {
      let form_name = document.querySelector('#display-name').value
      socket.emit('enter', {name: form_name});
      // TODO delete the form
      localStorage.setItem("username", form_name)
      return false
    }
  } else {
    // TODO delete the form
    document.querySelector('#bar-name').innerHTML = display_name
  }
}
