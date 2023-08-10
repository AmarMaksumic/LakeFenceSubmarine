"use strict";

new Vue({
  el: '#app',
  template: '#main-template',
  data: {
    enable_processing_feed: false,
    enable_calibration_feed: false,
    color_modes: ['rgb', 'hsv', 'hsl'],
    color_profiles: null,
    selected_color_mode: null,
    selected_profile: null,
    controls_ws: null,
    apply_mask: false
  },
  computed: {
    "values": function () {
      let selected_profile = this.selected_profile;
      let selected_color_mode = this.selected_color_mode;

      if (selected_profile && selected_color_mode) {
        if (selected_color_mode == 'rgb') {
          return [
            {
              name: 'R',
              range: selected_profile.rgb.r
            },
            {
              name: 'G',
              range: selected_profile.rgb.g
            },
            {
              name: 'B',
              range: selected_profile.rgb.b
            }
          ]
        }
        if (selected_color_mode == 'hsl') {
          return [
            {
              name: 'H',
              range: selected_profile.hsl.h
            },
            {
              name: 'S',
              range: selected_profile.hsl.s
            },
            {
              name: 'V',
              range: selected_profile.hsl.l
            }
          ]
        }
        if (selected_color_mode == 'hsv') {
          return [
            {
              name: 'H',
              range: selected_profile.hsv.h
            },
            {
              name: 'S',
              range: selected_profile.hsv.s
            },
            {
              name: 'V',
              range: selected_profile.hsv.v
            }
          ]
        }
      }
      return []
    }
  },
  mounted: function () {
    var self = this;
    self.controls_ws = new_web_socket('/dashboard/ws');
    self.controls_ws.onmessage = function (msg) {
      var data = JSON.parse(msg.data)
      console.log(data);
      if (data.hasOwnProperty('enable_calibration_feed')) {
        self.enable_calibration_feed = data.enable_calibration_feed
      }
      if (data.hasOwnProperty('color_profiles')) {
        self.color_profiles = data.color_profiles;
        if (self.selected_profile) {
          self.selected_profile = self.color_profiles[self.selected_profile.camera_mode]
        }
      }
      //self.$forceUpdate();
    }
    start_camera_stream("/calibration/ws", "image");
  },
  methods: {
    toggleCalibrationFeed: function () {
      this.controls_ws.send(JSON.stringify({
        request_type: 'controls',
        enable_calibration_feed: !this.enable_calibration_feed
      }))
    },
    changeProfile: function (profile) {
      this.selected_profile = profile;
      this.controls_ws.send(JSON.stringify({
        request_type: 'calibration',
        camera_mode: this.selected_profile.camera_mode,
        color_mode: this.selected_color_mode,
        apply_mask: this.apply_mask
      }));
    },
    changeApplyMask: function () {
      this.controls_ws.send(JSON.stringify({
        request_type: 'calibration',
        camera_mode: this.selected_profile.camera_mode,
        color_mode: this.selected_color_mode,
        apply_mask: this.apply_mask
      }));
    },
    changeColorMode: function (color_mode) {
      this.selected_color_mode = color_mode
      this.controls_ws.send(JSON.stringify({
        request_type: 'calibration',
        camera_mode: this.selected_profile.camera_mode,
        color_mode: this.selected_color_mode,
        apply_mask: this.apply_mask
      }));
    },
    updateColors: function () {
      var self = this;
      console.log(self.color_profiles)
      self.controls_ws.send(JSON.stringify({ 'color_profile': self.selected_profile }))
    },
    saveProfile: function () {
      var self = this;
      self.controls_ws.send(JSON.stringify({
        'color_profile': self.selected_profile,
        'save': true
      }))
    },
    resetProfile: function () {
      var self = this;
      self.controls_ws.send(JSON.stringify({
        'color_profile': self.selected_profile,
        'reset': true
      }))
    }
  }
});
