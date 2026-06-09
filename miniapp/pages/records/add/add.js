const api = require('../../../utils/api');
const app = getApp();

function pad(n) { return n < 10 ? '0' + n : '' + n; }

function todayStr() {
  var d = new Date();
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
}

function nowTime() {
  var d = new Date();
  return pad(d.getHours()) + ':' + pad(d.getMinutes());
}

function fmtDisplay(datetime) {
  if (!datetime) return '';
  var d = new Date(datetime);
  return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

Page({
  data: {
    type: 'feeding',
    currentDate: todayStr(),
    startTime: nowTime(),
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
    var val = e.detail.value;
    this.setData({ [field]: val });
    // Update display text
    var displayField = field + 'Display';
    this.setData({ [displayField]: fmtDisplay(this.data.currentDate + ' ' + val) });
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

    var startDt = this.data.currentDate + ' ' + this.data.startTime;
    var endDt = this.data.endTime ? this.data.currentDate + ' ' + this.data.endTime : '';

    var path, body;
    if (type === 'feeding') {
      path = '/records/feeding?baby_id=' + babyId;
      body = {
        start_time: startDt,
        end_time: endDt || null,
        amount: parseInt(this.data.amount) || 0,
        side: this.data.side,
        note: this.data.note,
      };
    } else if (type === 'sleep') {
      path = '/records/sleep?baby_id=' + babyId;
      body = {
        start_time: startDt,
        end_time: endDt || null,
        quality: this.data.quality,
        note: this.data.note,
      };
    } else {
      path = '/records/diaper?baby_id=' + babyId;
      body = {
        time: startDt,
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
