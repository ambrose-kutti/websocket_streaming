// State
const state = {
    socket: null,
    cameras: {},
    activeStreams: {}
};
// Initialize
function init() {
    connectWebSocket();
    loadCameras();
}
// WebSocket connection
function connectWebSocket() {
    state.socket = io('/stream', {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000
    });
    state.socket.on('connect', () => {
        updateConnectionStatus(true);
        showToast('Connected to server', 'success');
    });
    state.socket.on('disconnect', () => {
        updateConnectionStatus(false);
        showToast('Disconnected from server', 'error');
    });
    state.socket.on('frame', handleVideoFrame);
    state.socket.on('camera_removed', handleCameraRemoved);
}
// Update connection status UI
function updateConnectionStatus(connected) {
    const status = document.getElementById('connectionStatus');
    if (connected) {
        status.textContent = 'Connected';
        status.className = 'connection-status connected';
    } else {
        status.textContent = 'Disconnected';
        status.className = 'connection-status disconnected';
    }
}
// Load cameras from server
async function loadCameras() {
    try {
        const response = await fetch('/api/cameras');
        const data = await response.json();
        
        state.cameras = data.cameras.reduce((acc, cam) => {
            acc[cam.id] = cam;
            return acc;
        }, {});
        updateCameraList();
        updateVideoGrid();
    } catch (error) {
        console.error('Failed to load cameras:', error);
    }
}

// Add new camera
async function addCamera() {
    const name = document.getElementById('cameraName').value || `Camera ${Object.keys(state.cameras).length + 1}`;
    const location = document.getElementById('location').value;
    const direction = document.getElementById('direction').value;
    const url = document.getElementById('rtspUrl').value;
    if (!url) {
        showToast('Please enter RTSP URL', 'error');
        return;
    }
    try {
        const response = await fetch('/api/cameras', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, location, direction, rtsp_url: url })
        });
        const result = await response.json();
        if (result.success) {
            showToast('Camera added successfully', 'success');
            document.getElementById('cameraName').value = '';
            document.getElementById('location').value = '';
            document.getElementById('direction').value = 'N';
            document.getElementById('rtspUrl').value = '';
            loadCameras();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Failed to add camera', 'error');
    }
}

// Start camera stream
async function startCamera(cameraId) {
    try {
        const response = await fetch(`/api/cameras/${cameraId}/start`, {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            showToast('Camera started', 'success');
            loadCameras();
            // Start WebSocket streaming
            if (state.socket.connected) {
                state.socket.emit('start_stream', { camera_id: cameraId });
                state.activeStreams[cameraId] = true;
            }
        }
    } catch (error) {
        showToast('Failed to start camera', 'error');
    }
}

// Stop camera stream
async function stopCamera(cameraId) {
    try {
        const response = await fetch(`/api/cameras/${cameraId}/stop`, {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            showToast('Camera stopped', 'warning');
            loadCameras();
            // Stop WebSocket streaming
            if (state.socket.connected) {
                state.socket.emit('stop_stream', { camera_id: cameraId });
                delete state.activeStreams[cameraId];
            }
        }
    } catch (error) {
        showToast('Failed to stop camera', 'error');
    }
}

// Remove camera
async function removeCamera(cameraId) {
    if (!confirm('Are you sure you want to remove this camera?')) return;
    try {
        const response = await fetch(`/api/cameras/${cameraId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (result.success) {
            showToast('Camera removed', 'warning');
            loadCameras();
        }
    } catch (error) {
        showToast('Failed to remove camera', 'error');
    }
}

// Start all cameras
async function startAll() {
    for (const cameraId in state.cameras) {
        await startCamera(cameraId);
        await sleep(500); // Delay between starts
    }
}

// Stop all cameras
async function stopAll() {
    for (const cameraId in state.cameras) {
        await stopCamera(cameraId);
        await sleep(500); // Delay between stops
    }
}

// Update camera list UI
function updateCameraList() {
    const container = document.getElementById('cameraList');
    const cameras = Object.values(state.cameras);
    if (cameras.length === 0) {
        container.innerHTML = '<div style="color: #64748b; text-align: center; padding: 20px;">No cameras added yet</div>';
        return;
    }
    container.innerHTML = cameras.map(cam => `
        <div class="camera-item">
            <div class="camera-header">
                <div class="camera-name">${cam.name}</div>
                <div class="camera-status status-${cam.active ? 'active' : 'inactive'}">
                    ${cam.active ? 'LIVE' : 'OFFLINE'}
                </div>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 4px;">
                <div><strong>Location:</strong> ${cam.location || 'N/A'}</div>
                <div><strong>Direction:</strong> ${cam.direction || 'N/A'}</div>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 8px; word-break: break-all;">
                ${cam.url.substring(0, 40)}${cam.url.length > 40 ? '...' : ''}
            </div>
            <div class="camera-actions">
                ${cam.active ? 
                    `<button class="stop" onclick="stopCamera('${cam.id}')">Stop</button>` :
                    `<button onclick="startCamera('${cam.id}')">Start</button>`
                }
                <button class="stop" onclick="removeCamera('${cam.id}')">Remove</button>
            </div>
        </div>
    `).join('');
}

// Update video grid UI
function updateVideoGrid() {
    const container = document.getElementById('videosContainer');
    const activeCameras = Object.values(state.cameras).filter(cam => cam.active);
    if (activeCameras.length === 0) {
        container.innerHTML = `
            <div class="no-streams">
                <div>📷</div>
                <h3>No Active Streams</h3>
                <p>Add a camera and start streaming</p>
            </div>
        `;
        return;
    }
    container.innerHTML = activeCameras.map(cam => `
        <div class="video-card">
            <div class="video-header">
                <div style="font-weight: 600;">${cam.name}</div>
                <div class="video-stats">
                    <span id="fps-${cam.id}">0 FPS</span>
                    <span>ID: ${cam.id}</span>
                </div>
            </div>
            <img class="video-feed" id="video-${cam.id}" 
                 src="" alt="${cam.name}"
                 onerror="this.src='data:image/svg+xml,<svg xmlns=&quot;http://www.w3.org/2000/svg&quot; viewBox=&quot;0 0 640 480&quot;><rect width=&quot;100%&quot; height=&quot;100%&quot; fill=&quot;%23000&quot;/><text x=&quot;50%&quot; y=&quot;50%&quot; fill=&quot;%23fff&quot; font-family=&quot;sans-serif&quot; font-size=&quot;16&quot; text-anchor=&quot;middle&quot; dy=&quot;.3em&quot;>LOADING...</text></svg>'">
        </div>
    `).join('');
}

const clientFps = {};   // FPS Counters for client-side calculation

// Handle incoming video frames
function handleVideoFrame(data) {
    const imgElement = document.getElementById(`video-${data.camera_id}`);
    if (imgElement) {
        imgElement.src = `data:image/jpeg;base64,${data.frame}`;   
        // Calculate Client-Side FPS (Streaming Rate)
        if (!clientFps[data.camera_id]) {
            clientFps[data.camera_id] = { count: 0, lastTime: Date.now(), value: 0 };
        }
        const metrics = clientFps[data.camera_id];
        metrics.count++;
        const now = Date.now();
        if (now - metrics.lastTime >= 1000) {
            metrics.value = metrics.count;
            metrics.count = 0;
            metrics.lastTime = now;
        }
        // Update FPS display
        const fpsElement = document.getElementById(`fps-${data.camera_id}`);
        if (fpsElement) {
            fpsElement.textContent = `Capture: ${data.fps || 0} | Stream: ${metrics.value} FPS`;
        }
    }
}

// Handle camera removal
function handleCameraRemoved(data) {
    delete state.cameras[data.camera_id];
    delete state.activeStreams[data.camera_id];
    updateCameraList();
    updateVideoGrid();
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.borderLeftColor = type === 'success' ? '#10b981' : 
                                 type === 'error' ? '#ef4444' : '#3b82f6';
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Utility function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

window.addEventListener('DOMContentLoaded', init);  // Initialize on load

// Make functions global
window.addCamera = addCamera;
window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.removeCamera = removeCamera;
window.startAll = startAll;
window.stopAll = stopAll;