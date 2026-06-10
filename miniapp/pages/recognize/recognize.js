const api = require('../../utils/api');
const app = getApp();
const recorderManager = wx.getRecorderManager();

Page({
  data: {
    isRecording: false,
    recordTime: 0,
    canStop: false,
    timer: null,
    progressTimer: null,
    babyName: '',
    analyzing: false,
    analyzeProgress: 0,
    analyzeText: '',
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

  startAnalyzeProgress() {
    var that = this;
    var steps = [
      '正在上传哭声样本',
      'AI大模型智能分析中',
      '正在生成育儿建议',
    ];
    var progress = 8;
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
    this.setData({
      analyzing: true,
      analyzeProgress: progress,
      analyzeText: steps[0],
    });
    this.data.progressTimer = setInterval(function() {
      progress = Math.min(progress + 9, 96);
      var idx = progress < 38 ? 0 : progress < 78 ? 1 : 2;
      that.setData({
        analyzeProgress: progress,
        analyzeText: steps[idx],
      });
    }, 450);
  },

  stopAnalyzeProgress() {
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
    this.setData({
      analyzing: false,
      analyzeProgress: 0,
      analyzeText: '',
      progressTimer: null,
    });
  },

  async onRecordStop(res) {
    this.startAnalyzeProgress();

    try {
      var formData = {};
      if (app.globalData.babyId) {
        formData.baby_id = String(app.globalData.babyId);
      }

      var result = await api.uploadFile('/cry/recognize', res.tempFilePath, formData, { timeout: 6000 });

      this.stopAnalyzeProgress();
      wx.setStorageSync('latestCryResult', result);
      wx.navigateTo({
        url: '/pages/result/result',
      });
    } catch (err) {
      this.stopAnalyzeProgress();
      wx.showToast({ title: '分析超时，请靠近宝宝重试', icon: 'none' });
    }
  },

  onUnload() {
    if (this.data.timer) clearInterval(this.data.timer);
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
  },
});
