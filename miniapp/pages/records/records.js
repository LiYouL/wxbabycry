const api = require('../../utils/api');
const app = getApp();

function pad(n) { return n < 10 ? '0' + n : '' + n; }

function fmtTime(datetime) {
  if (!datetime) return '';
  var d = new Date(datetime);
  if (isNaN(d.getTime())) return datetime;
  return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

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
      var that = this;
      res = res.map(function(r) {
        if (r.start_time) r.start_time = fmtTime(r.start_time);
        if (r.end_time) r.end_time = fmtTime(r.end_time);
        if (r.time) r.time = fmtTime(r.time);
        return r;
      });
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
