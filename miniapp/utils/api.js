function getGlobalData() {
  var app = getApp();
  return app ? app.globalData : { token: '', apiBase: 'http://localhost:8000/api' };
}

function request(method, path, data = {}, options = {}) {
  return new Promise((resolve, reject) => {
    var globalData = getGlobalData();
    const header = {
      'Content-Type': 'application/json',
    };
    if (globalData.token) {
      header['Authorization'] = 'Bearer ' + globalData.token;
    }

    wx.request({
      url: globalData.apiBase + path,
      method: method,
      header: header,
      data: data,
      ...options,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail(err) {
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

function uploadFile(path, filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    var globalData = getGlobalData();
    const header = {};
    if (globalData.token) {
      header['Authorization'] = 'Bearer ' + globalData.token;
    }

    wx.uploadFile({
      url: globalData.apiBase + path,
      filePath: filePath,
      name: 'audio',
      header: header,
      formData: formData,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data));
        } else {
          reject(JSON.parse(res.data));
        }
      },
      fail(err) {
        wx.showToast({ title: '上传失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

module.exports = {
  get: function(path, data) { return request('GET', path, data); },
  post: function(path, data) { return request('POST', path, data); },
  put: function(path, data) { return request('PUT', path, data); },
  uploadFile: uploadFile,
};
