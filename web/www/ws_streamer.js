function new_web_socket(uri_path) {
  var protocol = 'ws:';
  if (window.location.protocol === 'https:') {
    protocol = 'wss:';
  }
  var host = window.location.host;
  var url = protocol + '//' + host + uri_path;
  console.log(url);
  var ws = new WebSocket(url);
  return ws;
}

var imageMap = {};
var socketMap = {};

var start_camera_stream = function (websocket_source, target) {

  imageMap[websocket_source] = document.getElementById(target)
  socketMap[websocket_source] = new_web_socket(websocket_source);

  time_0 = (new Date()).getTime();
  counter = 0;

  update_fps = function () {
    counter += 1;
    if ((counter % 5) == 0) {
      tdif = (new Date()).getTime() - time_0;
      time_0 = (new Date()).getTime();
      fps = Math.round(5 * 1.0 / (tdif / 1000.0));
      $(document).ready(function () {
        $('#actual').text(fps);
      });

    }
  }


  socketMap[websocket_source].onmessage = function (e) {

    if (e.data == 'connected') {
      console.log('opening feed ' + websocket_source);
      socketMap[websocket_source].send("open feed");
    }

    if (e.data instanceof Blob) {
      //update_fps()
      imageMap[websocket_source].src = URL.createObjectURL(e.data);
      imageMap[websocket_source].onload = function () {
        URL.revokeObjectURL(imageMap[websocket_source].src);
      }
    }
  }

  socketMap[websocket_source].onopen = function () {
    console.log('connected ' + websocket_source);
    //ws_imagestream.send("open feed")
  };
  socketMap[websocket_source].onclose = function () {
    console.log('closed feed ');
  };
};
