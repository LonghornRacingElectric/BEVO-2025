// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld('electron', {
    onCanData: (callback: (data: any) => void) => ipcRenderer.on('can-message', (event, data) => callback(data)),
    removeCanDataListener: (callback: (data: any) => void) => ipcRenderer.removeListener('can-message', callback),
});