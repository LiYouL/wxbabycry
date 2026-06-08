const api = require('../../utils/api');
const app = getApp();

Page({
  data: {
    records: [],
    tab: 'feeding',
    noMore: false,
  },

  onShow() { this.loadRecords(); },

  async loadRecords() {
    if (!app.globalData.babyId) return;
    var tab = this.data.tab;
    var path = '/records/' + tab + '/list?baby_id=' + app.globalData.babyId;
    try {
      var res = await api.get(path);
      this.setData({ records: res, noMore: res.length < 20 });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab }, function() { this.loadRecords(); }.bind(this));
  },

  goAdd() {
    wx.navigateTo({ url: '/pages/records/add/add?type=' + this.data.tab });
  },
});
