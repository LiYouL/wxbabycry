Page({
  data: {
    result: null,
  },

  onLoad() {
    // Result data is set via navigateTo from recognize page
  },

  goBack() {
    wx.navigateBack();
  },

  retryRecord() {
    wx.navigateBack();
  },
});
