const {app, BrowserWindow, ipcMain} = require('electron');
const {execFile, spawn} = require('node:child_process');
const path = require('node:path');
const {promisify} = require('node:util');
const run = promisify(execFile);
const apps = {roblox:'org.vinegarhq.Sober', studio:'org.vinegarhq.Vinegar'};
let win;
app.whenReady().then(() => {
  win = new BrowserWindow({width:1080,height:760,minWidth:720,minHeight:600,backgroundColor:'#14111c',autoHideMenuBar:true,webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  win.webContents.setWindowOpenHandler(() => ({action:'deny'}));
  win.webContents.on('will-navigate', e => e.preventDefault());
  ipcMain.handle('status', async () => {
    const result = {};
    for (const [key,id] of Object.entries(apps)) {
      try { await run('flatpak',['info',id],{timeout:5000}); result[key]=true; }
      catch { result[key]=false; }
    }
    return result;
  });
  ipcMain.handle('launch', async (_,key) => {
    if (!Object.hasOwn(apps,key)) return {ok:false,error:'Unknown application.'};
    try {
      await run('flatpak',['info',apps[key]],{timeout:5000});
      const child=spawn('flatpak',['run',apps[key]],{stdio:['ignore','ignore','pipe']});
      let output='';
      child.stderr.on('data', chunk => {output=(output+chunk).slice(-3000);});
      child.on('error', err => win?.webContents.send('launch-error',err.message));
      child.on('exit', code => {if(code) win?.webContents.send('launch-error',output || 'Application exited with code '+code);});
      return {ok:true};
    } catch {return {ok:false,error:'Missing Flatpak or app. Install with: flatpak install flathub '+apps[key]};}
  });
  win.loadFile('index.html');
});
app.on('window-all-closed',()=>app.quit());
