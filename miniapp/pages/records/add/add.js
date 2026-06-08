const api = require('../../../utils/api');
const app = getApp();

Page({
  data: {
    type: 'feeding',
    startTime: '',
    endTime: '',
    amount: '',
    side: '',
    quality: '',
    diaperType: '',
    color: '',
    note: '',
  },

  onLoad(options) {
    this.setData({ type: options.type || 'feeding' });
  },

  onTimeChange(e) {
    var field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },

  onInputChange(e) {
    var field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },

  async submit() {
    var type = this.data.type;
    var babyId = app.globalData.babyId;
    if (!babyId) {
      wx.showToast({ title: '请先设置宝宝信息', icon: 'none' });
      return;
    }

    var path, body;
    if (type === 'feeding') {
      path = '/records/feeding?baby_id=' + babyId;
      body = {
        start_time: this.data.startTime,
        end_time: this.data.endTime || null,
        amount: parseInt(this.data.amount) || 0,
        side: this.data.side,
        note: this.data.note,
      };
    } else if (type === 'sleep') {
      path = '/records/sleep?baby_id=' + babyId;
      body = {
        start_time: this.data.startTime,
        end_time: this.data.endTime || null,
        quality: this.data.quality,
        note: this.data.note,
      };
    } else {
      path = '/records/diaper?baby_id=' + babyId;
      body = {
        time: this.data.startTime,
        type: this.data.diaperType,
        color: this.data.color,
        note: this.data.note,
      };
    }

    try {
      await api.post(path, body);
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(function() { wx.navigateBack(); }, 1000);
    } catch (err) {
      wx.showToast({ title: '保存失败', icon: 'none' });
    }
  },
});
