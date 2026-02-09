from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
import logging
from camera_manager import CameraManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

cam_manager = CameraManager()   # Initialize camera manager
#-----------
# Routes    
#-----------
@app.route('/')
def index():
    """Main page"""
    return render_template('cameras.html')

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    cameras = cam_manager.get_all_cameras()
    return jsonify({'cameras': cameras})

@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """Add a new camera"""
    data = request.json
    if not data or 'rtsp_url' not in data:
        return jsonify({'error':'RTSP URL required'}), 400
    rtsp_url = data['rtsp_url']
    name = data.get('name', f'Camera {len(cam_manager.cameras) + 1}')
    location = data.get('location')
    direction = data.get('direction')
    camera_id = cam_manager.add_camera(rtsp_url, name, location, direction)
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'message': 'Camera added successfully'
    })

@app.route('/api/cameras/<camera_id>/start', methods=['POST'])
def start_camera(camera_id):
    """Start a camera"""
    success = cam_manager.start_camera(camera_id)
    if success:
        return jsonify({'success': True, 'message': 'Camera started'})
    return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/cameras/<camera_id>/stop', methods=['POST'])
def stop_camera(camera_id):
    """Stop a camera"""
    success = cam_manager.stop_camera(camera_id)
    if success:
        return jsonify({'success': True, 'message': 'Camera stopped'})
    return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/cameras/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Remove a camera"""
    success = cam_manager.remove_camera(camera_id)
    if success:
        # Notify all clients
        socketio.emit('camera_removed', {'camera_id': camera_id}, namespace='/stream')
        return jsonify({'success': True, 'message': 'Camera removed'})
    return jsonify({'error': 'Camera not found'}), 404
#-------------------
# WebSocket handlers
#-------------------
@socketio.on('connect', namespace='/stream')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'client_id': request.sid})

@socketio.on('disconnect', namespace='/stream')
def handle_disconnect():
    """Handle client disconnect"""
    logger.info(f"Client disconnected: {request.sid}")  # Flask-SocketIO automatically handles leaving rooms on disconnect.

@socketio.on('start_stream', namespace='/stream')
def handle_start_stream(data):
    """Client wants to start streaming a camera"""
    camera_id = data.get('camera_id')
    if camera_id in cam_manager.cameras:
        join_room(camera_id)
        logger.info(f"Client {request.sid} joined room for camera {camera_id}")
        emit('stream_started', {'camera_id': camera_id})

@socketio.on('stop_stream', namespace='/stream')
def handle_stop_stream(data):
    """Client wants to stop streaming a camera"""
    camera_id = data.get('camera_id')
    if camera_id in cam_manager.cameras:
        leave_room(camera_id)
        logger.info(f"Client {request.sid} left room for camera {camera_id}")
        emit('stream_stopped', {'camera_id': camera_id})

# Frame streaming thread
def stream_frames():
    """Background thread to stream frames to connected clients"""
    while True:
        try:
            # Iterate over all managed cameras
            for camera_id, camera in list(cam_manager.cameras.items()):
                # Only process active cameras that have a frame
                if camera and camera.active and camera.frame is not None:
                    frame_data = camera.get_frame_jpeg(quality=80)
                    if frame_data:
                        # Emit to the room named after the camera_id.
                        # SocketIO will only send to clients in that room.
                        socketio.emit('frame', {
                            'camera_id': camera_id,
                            'frame': frame_data,
                            'fps': camera.fps,
                            'timestamp': time.time()
                        }, namespace='/stream', room=camera_id)
            time.sleep(0.25)    # Control streaming rate (approx 4 FPS)
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            time.sleep(1)

if __name__ == '__main__':
    # Start frame streaming thread
    stream_thread = threading.Thread(target=stream_frames, daemon=True)
    stream_thread.start()   
    logger.info("Starting RTSP Streaming Server on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)