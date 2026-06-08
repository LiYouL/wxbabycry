const app = getApp();

Page({
  data: {
    babyInfo: null,
    dayCount: 0,
    greeting: '',
  },

  onShow() {
    var b = app.globalData.babyInfo;
    if (b) {
      this.setData({ babyInfo: b });
      if (b.birthday) {
        var days = Math.floor((Date.now() - new Date(b.birthday).getTime()) / 86400000);
        this.setData({ dayCount: days, greeting: '早上好！今天' + b.nickname + '已经' + days + '天啦！' });
      }
    }
  },

  goTo(e) {
    var page = e.currentTarget.dataset.page;
    wx.navigateTo({ url: page });
  },
});
