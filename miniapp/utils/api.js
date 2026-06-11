function getGlobalData() {
  var app = getApp();
  return app ? app.globalData : { token: '', apiBase: 'https://babycry-268031-4-1441517375.sh.run.tcloudbase.com/api' };
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

function uploadFile(path, filePath, formData = {}, options = {}) {
  return new Promise((resolve, reject) => {
    var globalData = getGlobalData();
    const header = {};
    var timeoutMs = options.timeout || 25000;
    var settled = false;
    var uploadTask = null;
    var timeoutTimer = null;
    if (globalData.token) {
      header['Authorization'] = 'Bearer ' + globalData.token;
    }

    function finish(callback, value) {
      if (settled) return;
      settled = true;
      if (timeoutTimer) clearTimeout(timeoutTimer);
      callback(value);
    }

    if (timeoutMs > 0) {
      timeoutTimer = setTimeout(function() {
        finish(reject, {
          errMsg: 'uploadFile:fail timeout',
          detail: '云端分析超时，请稍后重试',
        });
        if (uploadTask && uploadTask.abort) {
          uploadTask.abort();
        }
      }, timeoutMs);
    }

    uploadTask = wx.uploadFile({
      url: globalData.apiBase + path,
      filePath: filePath,
      name: 'audio',
      header: header,
      formData: formData,
      ...options,
      success(res) {
        var body = {};
        try {
          body = JSON.parse(res.data || '{}');
        } catch (e) {
          body = { detail: res.data || '服务响应解析失败' };
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          finish(resolve, body);
        } else {
          finish(reject, body);
        }
      },
      fail(err) {
        finish(reject, err);
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
