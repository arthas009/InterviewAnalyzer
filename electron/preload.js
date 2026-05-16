const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  getDataDir: () => ipcRenderer.invoke('get-data-dir'),
  setAlwaysOnTop: (value) => ipcRenderer.invoke('set-always-on-top', value),
  setOpacity: (value) => ipcRenderer.invoke('set-opacity', value),
  onToggleListening: (callback) => ipcRenderer.on('toggle-listening', callback),
});
