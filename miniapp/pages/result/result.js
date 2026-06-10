Page({
  data: {
    result: null,
  },

  onLoad() {
    var result = wx.getStorageSync('latestCryResult');
    if (result) {
      this.setResult(result);
    }
  },

  setResult(result) {
    var emojiMap = {
      '饥饿': '🍼',
      '尿布不适': '👶',
      '疲倦': '😴',
      '疼痛': '😣',
      '需要安抚': '🤗',
      '其他': '❓',
    };

    result.type_emoji = emojiMap[result.cry_type] || '❓';
    result.confidence_percent = Math.round((result.confidence || 0) * 1000) / 10;
    result.secondary_types = (result.secondary_types || []).map(function(item) {
      return {
        type: item.type,
        confidence: item.confidence,
        confidence_percent: Math.round((item.confidence || 0) * 1000) / 10,
      };
    });
    result.advice = result.advice || {};
    result.advice.solutions = result.advice.solutions || [];
    result.advice.soothing_tips = result.advice.soothing_tips || [];
    result.advice.warnings = result.advice.warnings || [];

    this.setData({ result: result });
  },

  goBack() {
    wx.navigateBack();
  },

  retryRecord() {
    wx.navigateBack();
  },
});
