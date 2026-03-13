const { app, BrowserWindow } = require('electron');
const path = require('path');
app.whenReady().then(() => {
  console.log('packaged?', app.isPackaged);
  const w = new BrowserWindow({show:false, webPreferences:{preload:path.resolve('geuldobi-desktop/src/preload.js'), contextIsolation:true, nodeIntegration:false}});
  w.loadFile(path.resolve('geuldobi-desktop/src/splash/splash.html')).then(() => {
    console.log('LOAD_OK');
    setTimeout(()=>app.quit(), 1000);
  }).catch(err => {
    console.error('LOAD_ERR', err && err.message);
    setTimeout(()=>app.quit(), 1000);
  });
});
