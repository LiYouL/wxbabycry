const api = require('../../../utils/api');
const app = getApp();

Page({
  data: {
    nickname: '',
    birthday: '',
    gender: '',
    feedType: '',
  },

  onShow() {
    var b = app.globalData.babyInfo;
    if (b) {
      this.setData({
        nickname: b.nickname || '',
        birthday: b.birthday || '',
        gender: b.gender || '',
        feedType: b.feed_type || '',
      });
    }
  },

  onInput(e) {
    var field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },

  async save() {
    var body = {
      nickname: this.data.nickname,
      birthday: this.data.birthday || null,
      gender: this.data.gender,
      feed_type: this.data.feedType,
    };
    try {
      var res = await api.post('/baby', body);
      app.globalData.babyId = res.id;
      app.globalData.babyInfo = res;
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(function() { wx.navigateBack(); }, 1000);
    } catch (err) {
      wx.showToast({ title: '保存失败', icon: 'none' });
    }
  },
});
