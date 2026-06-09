const api = require('../../utils/api');
const app = getApp();
const audioCtx = wx.createInnerAudioContext();

var FALLBACK_LIST = [
  { id: 1, name: '吹风机', icon: '💨', category: '白噪音' },
  { id: 2, name: '虫鸣', icon: '🦗', category: '白噪音' },
  { id: 3, name: '鸟鸣', icon: '🐦', category: '白噪音' },
  { id: 4, name: '电视白噪音', icon: '📺', category: '白噪音' },
  { id: 5, name: '风声', icon: '🌬️', category: '白噪音' },
  { id: 6, name: '心跳', icon: '💓', category: '白噪音' },
  { id: 7, name: '雨声', icon: '🌧️', category: '白噪音' },
  { id: 8, name: '海浪', icon: '🌊', category: '白噪音' },
  { id: 9, name: '蚊子声', icon: '🦟', category: '白噪音' },
  { id: 10, name: '洗衣机', icon: '🧺', category: '白噪音' },
];

Page({
  data: {
    items: [],
    activeId: null,
    isPlaying: false,
  },

  onLoad() {
    this.loadList();
    var that = this;
    audioCtx.onError(function() {
      wx.showToast({ title: '暂无音频资源', icon: 'none' });
      that.setData({ activeId: null, isPlaying: false });
    });
  },

  async loadList() {
    try {
      var res = await api.get('/noise/list');
      this.setData({ items: res.items && res.items.length ? res.items : FALLBACK_LIST });
    } catch (err) {
      this.setData({ items: FALLBACK_LIST });
    }
  },

  togglePlay(e) {
    var id = e.currentTarget.dataset.id;
    var item = this.data.items.find(function(it) { return it.id === id; });
    if (!item) return;

    if (this.data.activeId === id) {
      if (this.data.isPlaying) {
        audioCtx.pause();
        this.setData({ isPlaying: false });
      } else {
        audioCtx.play();
        this.setData({ isPlaying: true });
      }
    } else {
      audioCtx.src = app.globalData.apiBase + '/noise/' + id + '/stream';
      audioCtx.loop = true;
      audioCtx.play();
      this.setData({ activeId: id, isPlaying: true });
    }
  },

  onUnload() { audioCtx.destroy(); },
});
