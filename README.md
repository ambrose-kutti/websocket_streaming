# 📹 Camera Management System 📹
The Camera Management System is a comprehensive application designed to manage and monitor multiple cameras in real-time. It provides a robust and scalable solution for camera management, allowing users to add, remove, and control cameras, as well as monitor their live feeds. The system utilizes Flask as the web framework, SocketIO for real-time communication, and OpenCV for computer vision tasks.

## 🚀 Features
- **Camera Management**: Add, remove, and control cameras
- **Real-time Monitoring**: Monitor live feeds from multiple cameras
- **API Endpoints**: API routes for camera management (e.g., getting all cameras, adding a new camera, starting/stopping a camera)
- **SocketIO Integration**: Real-time communication between the server and connected clients
- **Logging**: Basic logging configuration for error tracking and debugging

## 🛠️ Tech Stack
- **Backend**:
  - Flask
  - Flask-SocketIO
  - camera_manager (custom module)
  - logging
  - threading
  - time
- **Frontend**:
  - JavaScript (main.js)
  - HTML (cameras.html)
- **Dependencies**:
  - Flask-SocketIO
  - opencv-python
  - numpy
  - python-socketio
  - python-engineio
  - itsdangerous
  - Jinja2
  - simple-websocket
  - Werkzeug
  - wsproto
- **Database**: Not used

## 📦 Installation
To install the required dependencies, run the following command:
```bash
pip install -r requirements.txt
```
This will install all the necessary packages and libraries specified in the `requirements.txt` file.

## 💻 Usage
1. **Prerequisites**: Ensure you have Python and pip installed on your system.
2. **Installation**: Run `pip install -r requirements.txt` to install the required dependencies.
3. **Running locally**: Run `python app.py` to start the Flask development server.
4. **Accessing the application**: Open a web browser and navigate to `http://localhost:5000` to access the application.

## 📂 Project Structure
```markdown
.
├── app.py
├── camera_manager.py
├── main.js
├── cameras.html
├── requirements.txt
└── ...
```
Note: The actual project structure may vary depending on the specific implementation and additional files.

## 📸 Screenshots

<img width="1335" height="634" alt="image" src="https://github.com/user-attachments/assets/3a259160-d6c2-4dc1-ad11-bf7b367a93da" />


## 🤝 Contributing
Contributions are welcome! If you'd like to contribute to the project, please fork the repository and submit a pull request with your changes.


## 📬 Contact
For any questions or concerns, please contact [arunambrose2004@gmail.com].

## 💖 Thanks Message
This project was made possible by the contributions of many individuals. Thank you to everyone who has contributed to the development and maintenance of this project.
