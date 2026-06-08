const api = require('../../utils/api');
const app = getApp();
const recorderManager = wx.getRecorderManager();

Page({
  data: {
    isRecording: false,
    recordTime: 0,
    canStop: false,
    timer: null,
    babyName: '',
  },

  onLoad() {
    if (app.globalData.babyInfo) {
      this.setData({ babyName: app.globalData.babyInfo.nickname });
    }
    recorderManager.onStop((res) => this.onRecordStop(res));
  },

  startRecord() {
    this.setData({ isRecording: true, recordTime: 0, canStop: false });

    recorderManager.start({
      duration: 30000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'mp3',
    });

    this.data.timer = setInterval(() => {
      var t = this.data.recordTime + 1;
      this.setData({
        recordTime: t,
        canStop: t >= 6,
      });
      if (t >= 30) {
        this.stopRecord();
      }
    }, 1000);
  },

  stopRecord() {
    if (!this.data.canStop) {
      wx.showToast({ title: '请至少录制6秒', icon: 'none' });
      return;
    }
    clearInterval(this.data.timer);
    recorderManager.stop();
    this.setData({ isRecording: false });
  },

  async onRecordStop(res) {
    wx.showLoading({ title: '识别中...' });

    try {
      var formData = {};
      if (app.globalData.babyId) {
        formData.baby_id = String(app.globalData.babyId);
      }

      var result = await api.uploadFile('/cry/recognize', res.tempFilePath, formData);

      wx.hideLoading();
      wx.navigateTo({
        url: '/pages/result/result',
        success: function(page) {
          page.setData({ result: result });
        },
      });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: '识别失败，请重试', icon: 'none' });
    }
  },

  onUnload() {
    if (this.data.timer) clearInterval(this.data.timer);
  },
});
