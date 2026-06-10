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
        this.setData({ dayCount: days, greeting: b.nickname + ' 已经 ' + days + ' 天啦！' });
      }
    }
  },

  goEditBaby() {
    wx.navigateTo({ url: '/pages/baby/edit/edit' });
  },

  goVaccine() {
    wx.navigateTo({ url: '/pages/vaccine/vaccine' });
  },

  goNoise() {
    wx.switchTab({ url: '/pages/noise/noise' });
  },

  goRecords() {
    wx.switchTab({ url: '/pages/records/records' });
  },

  goGrowth() {
    wx.showToast({ title: '成长分析整理中', icon: 'none' });
  },

  goFeedback() {
    wx.showModal({
      title: '意见反馈',
      content: '可以先把问题截图发给开发者，后续会接入微信反馈入口。',
      showCancel: false,
    });
  },

  shareApp() {
    wx.showToast({ title: '请用右上角菜单分享', icon: 'none' });
  },

  onShareAppMessage() {
    return {
      title: '智能育儿助手',
      path: '/pages/recognize/recognize',
    };
  },
});
