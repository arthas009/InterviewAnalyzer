const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const net = require('net');

let mainWindow = null;
let backendProcess = null;
let backendPort = null;

// Determine if running in production (packaged) or development
const isDev = !app.isPackaged;

function getBackendPath() {
  if (isDev) {
    return null; // In dev, we run python directly
  }
  return path.join(process.resourcesPath, 'backend', 'interview-analyzer-backend.exe');
}

function getDataDir() {
  const appData = process.env.APPDATA || path.join(require('os').homedir(), 'AppData', 'Roaming');
  return path.join(appData, 'InterviewAnalyzer');
}

async function findAvailablePort(startPort = 19400) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(startPort, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      resolve(findAvailablePort(startPort + 1));
    });
  });
}

async function startBackend() {
  backendPort = await findAvailablePort();
  const dataDir = getDataDir();

  console.log(`Starting backend on port ${backendPort}, data dir: ${dataDir}`);

  if (isDev) {
    // Development: run python script directly
    const backendDir = path.join(__dirname, '..', 'backend');
    // Use full Python path since Scripts may not be in PATH
    const pythonPath = path.join(
      process.env.LOCALAPPDATA || '',
      'Python', 'pythoncore-3.14-64', 'python.exe'
    );
    const pythonExe = require('fs').existsSync(pythonPath) ? pythonPath : 'python';
    backendProcess = spawn(pythonExe, [
      'main.py',
      '--port', String(backendPort),
      '--data-dir', dataDir,
    ], {
      cwd: backendDir,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
  } else {
    // Production: run bundled exe
    const exePath = getBackendPath();
    backendProcess = spawn(exePath, [
      '--port', String(backendPort),
      '--data-dir', dataDir,
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });
  }

  // Log backend output
  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend ERR] ${data.toString().trim()}`);
  });

  backendProcess.on('exit', (code) => {
    console.log(`Backend process exited with code ${code}`);
    if (code !== 0 && mainWindow) {
      // Backend crashed - attempt restart
      setTimeout(() => {
        console.log('Attempting backend restart...');
        startBackend().catch(console.error);
      }, 2000);
    }
  });

  // Wait for backend to be ready
  await waitForBackend(backendPort);
  console.log('Backend is ready');
}

function waitForBackend(port, maxRetries = 30, interval = 500) {
  return new Promise((resolve, reject) => {
    let retries = 0;

    const check = () => {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      });

      req.on('error', () => retry());
      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    };

    const retry = () => {
      retries++;
      if (retries >= maxRetries) {
        reject(new Error('Backend failed to start within timeout'));
      } else {
        setTimeout(check, interval);
      }
    };

    check();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 700,
    minWidth: 400,
    minHeight: 500,
    frame: true,
    transparent: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    title: 'Interview Analyzer',
  });

  if (isDev) {
    // In dev, try Vite dev server first; fall back to built files
    const fs = require('fs');
    const distIndex = path.join(__dirname, 'dist', 'index.html');
    if (fs.existsSync(distIndex)) {
      // Use built files directly if Vite isn't running
      mainWindow.loadFile(distIndex);
    } else {
      mainWindow.loadURL('http://localhost:5173');
    }
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC handlers
ipcMain.handle('get-backend-port', () => backendPort);
ipcMain.handle('get-data-dir', () => getDataDir());

ipcMain.handle('set-always-on-top', (_, value) => {
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(value);
  }
});

ipcMain.handle('set-opacity', (_, value) => {
  if (mainWindow) {
    mainWindow.setOpacity(value);
  }
});

// App lifecycle
app.whenReady().then(async () => {
  // Single instance lock
  const gotLock = app.requestSingleInstanceLock();
  if (!gotLock) {
    app.quit();
    return;
  }

  try {
    await startBackend();
    createWindow();

    // Register global shortcut to toggle listening
    globalShortcut.register('CommandOrControl+Shift+L', () => {
      if (mainWindow) {
        mainWindow.webContents.send('toggle-listening');
      }
    });
  } catch (err) {
    console.error('Failed to start app:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  app.quit();
});

app.on('will-quit', async () => {
  globalShortcut.unregisterAll();
  await stopBackend();
});

app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

async function stopBackend() {
  if (!backendProcess) return;

  try {
    // Try graceful shutdown first
    const req = http.request({
      hostname: '127.0.0.1',
      port: backendPort,
      path: '/shutdown',
      method: 'POST',
    });
    req.on('error', () => {}); // Ignore errors
    req.end();

    // Wait for process to exit
    await new Promise((resolve) => {
      const timeout = setTimeout(() => {
        // Force kill if graceful shutdown didn't work
        if (backendProcess) {
          backendProcess.kill('SIGTERM');
          setTimeout(() => {
            if (backendProcess) {
              backendProcess.kill('SIGKILL');
            }
            resolve();
          }, 3000);
        } else {
          resolve();
        }
      }, 5000);

      backendProcess.on('exit', () => {
        clearTimeout(timeout);
        resolve();
      });
    });
  } catch (e) {
    // Force kill as last resort
    if (backendProcess) {
      backendProcess.kill('SIGKILL');
    }
  }

  backendProcess = null;
}
