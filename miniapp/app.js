var api = require('./utils/api');

App({
  globalData: {
    apiBase: 'https://babycry-268031-4-1441517375.sh.run.tcloudbase.com/api',
    token: '',
    babyId: null,
    babyInfo: null,
  },

  onLaunch() {
    var token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      this.loadBabyInfo();
    } else {
      this.login();
    }
  },

  login() {
    var that = this;
    wx.login({
      success(res) {
        if (res.code) {
          api.post('/user/login', { code: res.code }).then(function(data) {
            that.globalData.token = data.token;
            wx.setStorageSync('token', data.token);
            that.loadBabyInfo();
          }).catch(function(err) {
            console.error('Login failed:', err);
          });
        }
      },
    });
  },

  loadBabyInfo() {
    var that = this;
    api.get('/baby').then(function(babies) {
      if (babies.length > 0) {
        that.globalData.babyId = babies[0].id;
        that.globalData.babyInfo = babies[0];
      }
    }).catch(function(err) {
      console.error('Load baby failed:', err);
    });
  },
});
