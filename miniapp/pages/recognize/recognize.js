const api = require('../../utils/api');
const app = getApp();
const recorderManager = wx.getRecorderManager();
const ANALYZE_TIMEOUT_MS = 25000;

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
      '云端仍在分析，请稍等',
    ];
    var progress = 8;
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
    this.setData({
      analyzing: true,
      analyzeProgress: progress,
      analyzeText: steps[0],
    });
    this.data.progressTimer = setInterval(function() {
      progress = Math.min(progress + 7, 96);
      var idx = progress < 35 ? 0 : progress < 70 ? 1 : progress < 96 ? 2 : 3;
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

  finishAnalyzeProgress() {
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
    this.setData({
      analyzing: true,
      analyzeProgress: 100,
      analyzeText: '分析完成，正在生成结果',
      progressTimer: null,
    });
  },

  showAnalyzeError(err) {
    console.error('Recognize failed:', err);
    var message = '识别失败，请稍后重试';
    if (err && err.detail) {
      message = err.detail;
    } else if (err && err.errMsg && err.errMsg.indexOf('timeout') >= 0) {
      message = '网络较慢，云端分析超时，请稍后重试';
    } else if (err && err.errMsg) {
      message = '网络连接失败，请检查后重试';
    }

    wx.showModal({
      title: '识别失败',
      content: message,
      showCancel: false,
    });
  },

  async onRecordStop(res) {
    this.startAnalyzeProgress();

    try {
      var formData = {};
      if (app.globalData.babyId) {
        formData.baby_id = String(app.globalData.babyId);
      }

      var result = await api.uploadFile('/cry/recognize', res.tempFilePath, formData, { timeout: ANALYZE_TIMEOUT_MS });

      this.finishAnalyzeProgress();
      wx.setStorageSync('latestCryResult', result);
      setTimeout(() => {
        this.stopAnalyzeProgress();
        wx.navigateTo({
          url: '/pages/result/result',
        });
      }, 160);
    } catch (err) {
      this.stopAnalyzeProgress();
      this.showAnalyzeError(err);
    }
  },

  onUnload() {
    if (this.data.timer) clearInterval(this.data.timer);
    if (this.data.progressTimer) clearInterval(this.data.progressTimer);
  },
});
