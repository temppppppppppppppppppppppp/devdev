const { app } = require('electron');
app.whenReady().then(() => {
  console.log('documents=' + app.getPath('documents'));
  console.log('downloads=' + app.getPath('downloads'));
  console.log('home=' + app.getPath('home'));
  app.quit();
});
