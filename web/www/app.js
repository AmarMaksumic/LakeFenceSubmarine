"use strict";

new Vue({
  el: '#app',
  template: '#main-template',
  data: {
    controls: {
      enable_camera: false,
      // enable_processing: false,
      camera_mode: 'RAW'
    },
    targets: []
  },
  mounted: function () {
    console.log('mounted');
    var self = this;
    start_camera_stream("/processed/ws", "processed_image");
  },
  watch: {
    'controls.camera_mode': function () {
      Socket.send({ 'controls': this.controls })
    }
  },
  methods: {
    onTargetUpdate: function (key, value, isNew) {
      //console.log(value);
      this.targets = value
    },
    update: function () {
      var self = this;
      // self.controls.camera_mode = mode;
      // Socket.send({'controls':self.controls})
    }
  }
});
