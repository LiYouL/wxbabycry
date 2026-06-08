const api = require('../../utils/api');
const app = getApp();

Page({
  data: { vaccines: [] },

  onShow() { this.loadList(); },

  async loadList() {
    if (!app.globalData.babyId) return;
    try {
      var res = await api.get('/vaccine/list?baby_id=' + app.globalData.babyId);
      this.setData({ vaccines: res });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  async markComplete(e) {
    var id = e.currentTarget.dataset.id;
    try {
      await api.put('/vaccine/' + id + '/status', { status: '已接种' });
      wx.showToast({ title: '已标记完成', icon: 'success' });
      this.loadList();
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },
});
