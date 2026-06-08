const api = require('../../utils/api');
const app = getApp();
const audioCtx = wx.createInnerAudioContext();

Page({
  data: {
    items: [],
    categories: [],
    activeCategory: '全部',
    currentTrack: null,
    isPlaying: false,
    isLoop: false,
  },

  onLoad() { this.loadList(); },

  async loadList() {
    try {
      var res = await api.get('/noise/list');
      this.setData({ items: res.items, categories: res.categories });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  switchCategory(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.cat });
  },

  togglePlay(e) {
    var item = e.currentTarget.dataset.item;
    if (this.data.currentTrack && this.data.currentTrack.id === item.id) {
      this._togglePauseResume();
    } else {
      this._playNew(item);
    }
  },

  _playNew(item) {
    audioCtx.src = app.globalData.apiBase + '/noise/' + item.id + '/stream';
    audioCtx.loop = this.data.isLoop;
    audioCtx.play();
    this.setData({ currentTrack: item, isPlaying: true });
  },

  _togglePauseResume() {
    if (this.data.isPlaying) {
      audioCtx.pause();
    } else {
      audioCtx.play();
    }
    this.setData({ isPlaying: !this.data.isPlaying });
  },

  toggleLoop() {
    var loop = !this.data.isLoop;
    audioCtx.loop = loop;
    this.setData({ isLoop: loop });
  },

  onUnload() { audioCtx.destroy(); },
});
