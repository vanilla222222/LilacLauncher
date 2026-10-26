const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('lilac',{status:()=>ipcRenderer.invoke('status'),launch:key=>ipcRenderer.invoke('launch',key),onError:callback=>ipcRenderer.on('launch-error',(_,message)=>callback(message))});
