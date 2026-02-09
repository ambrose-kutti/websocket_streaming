import cv2
import base64
import threading
import time
import logging

logger = logging.getLogger(__name__)

class Camera:
    def __init__(self, camera_id, rtsp_url, name="Camera", location=None, direction=None):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.name = name
        self.location = location
        self.direction = direction
        self.active = False
        self.thread = None
        self.cap = None
        self.frame = None
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        
    def start(self):
        """Start camera stream"""
        if self.active:
            return False
            
        self.active = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        """Stop camera stream"""
        self.active = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        logger.info(f"Camera {self.camera_id} stopped")
    
    def _capture_loop(self):
        """Main capture loop"""
        try:
            # RTSP connection with timeout
            self.cap = cv2.VideoCapture(self.rtsp_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open RTSP: {self.rtsp_url}")
                self.active = False
                return
            
            logger.info(f"Camera {self.camera_id} started: {self.rtsp_url}")
            
            while self.active:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"Camera {self.camera_id}: Frame read failed")
                    time.sleep(1)
                    continue
                
                self.frame = frame
                
                # Calculate FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_time = current_time
                    
        except Exception as e:
            logger.error(f"Camera {self.camera_id} error: {str(e)}")
        finally:
            if self.cap:
                self.cap.release()
            self.active = False
    
    def get_frame_jpeg(self, quality=85):
        """Get current frame as JPEG base64"""
        if self.frame is None:
            return None
        
        try:
            # Encode frame to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode('.jpg', self.frame, encode_param)
            
            # Convert to base64
            frame_data = base64.b64encode(buffer).decode('utf-8')
            return frame_data
        except Exception as e:
            logger.error(f"Frame encode error: {str(e)}")
            return None

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.next_id = 1
        
    def add_camera(self, rtsp_url, name=None, location=None, direction=None):
        """Add a new camera"""
        camera_id = f"cam_{self.next_id}"
        self.next_id += 1
        
        if not name:
            name = f"Camera {camera_id}"
        
        camera = Camera(camera_id, rtsp_url, name, location, direction)
        self.cameras[camera_id] = camera
        return camera_id
    
    def remove_camera(self, camera_id):
        """Remove a camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            return True
        return False
    
    def start_camera(self, camera_id):
        """Start a camera stream"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].start()
        return False
    
    def stop_camera(self, camera_id):
        """Stop a camera stream"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            return True
        return False
    
    def get_camera_info(self, camera_id):
        """Get camera information"""
        if camera_id in self.cameras:
            cam = self.cameras[camera_id]
            return {
                'id': camera_id,
                'name': cam.name,
                'location': cam.location,
                'direction': cam.direction,
                'active': cam.active,
                'fps': cam.fps,
                'url': cam.rtsp_url
            }
        return None
    
    def get_all_cameras(self):
        """Get all cameras info"""
        cameras = []
        for cam_id, cam in self.cameras.items():
            cameras.append({
                'id': cam_id,
                'name': cam.name,
                'location': cam.location,
                'direction': cam.direction,
                'active': cam.active,
                'fps': cam.fps,
                'url': cam.rtsp_url
            })
        return cameras