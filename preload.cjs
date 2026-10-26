const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('lilac',{status:()=>ipcRenderer.invoke('status'),launch:(key,placeId)=>ipcRenderer.invoke('launch',key,placeId),search:input=>ipcRenderer.invoke('search-games',input),onError:callback=>ipcRenderer.on('launch-error',(_,message)=>callback(message))});
