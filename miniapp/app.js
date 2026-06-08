App({
  globalData: {
    apiBase: 'http://localhost:8000/api',
    token: '',
    babyId: null,
    babyInfo: null,
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
    }
  },
});
