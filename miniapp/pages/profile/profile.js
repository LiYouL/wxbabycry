const app = getApp();

Page({
  data: { babyInfo: null },

  onShow() {
    this.setData({ babyInfo: app.globalData.babyInfo });
  },

  goEditBaby() {
    wx.navigateTo({ url: '/pages/baby/edit/edit' });
  },

  goVaccine() {
    wx.navigateTo({ url: '/pages/vaccine/vaccine' });
  },

  goNoise() {
    wx.navigateTo({ url: '/pages/noise/noise' });
  },
});
