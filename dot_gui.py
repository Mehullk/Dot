import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QMovie
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from dot_main import VirtualAssistant

class WorkerThread(QThread):
    finished = pyqtSignal(str)
    command_received = pyqtSignal(str)

    def __init__(self, va: 'VirtualAssistant', parent=None):
        super().__init__(parent)
        self.va = va
        self.running = True

    def run(self):
        while self.running:
            command = self.va.take_command()  # This listens to the voice input
            if command:
                self.command_received.emit(command)
        self.finished.emit("Assistant stopped.")

    def stop(self):
        """Gracefully stop the thread"""
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self, va: 'VirtualAssistant'):
        super().__init__()
        self.va = va
        self.listen_thread = None
        self.is_listening = False
        self.setWindowTitle(".DOT")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #333; color: white;")
        app.setFont(QFont("LED Dot-Matrix", 12))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Title Label
        self.title_label = QLabel(".DOT", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("LED Dot-Matrix", 32))
        self.layout.addWidget(self.title_label)

        # Listening Animation
        self.animation_label = QLabel(self)
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.movie = QMovie("listening.gif")  # Replace with your animation file
        self.animation_label.setMovie(self.movie)
        self.layout.addWidget(self.animation_label)

        # Output Text Area
        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                border-radius: 20px;
                background-color: rgba(0, 0, 0, 150);
                background-image: url('dot_bg.png'); /* Background image */
                background-position: center;
                background-repeat: no-repeat;
                border: 2px solid #aaaaaa;
                padding: 10px;
                font-size: 18px;
                color: white;
            }
        """)
        self.layout.addWidget(self.output_text)

        # Input Field and Buttons Layout
        self.input_layout = QHBoxLayout()

        # Command Input Field
        self.command_input = QLineEdit(self)
        self.command_input.setPlaceholderText("Enter your command...")
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                border: 2px solid #111111;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 22px;
                max-height: 40px;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #aaa;
            }
        """)
        self.input_layout.addWidget(self.command_input)

        # Voice Button
        self.voice_button = QPushButton(self)
        self.voice_button.setIcon(QIcon("voice.png"))  # Set the mic icon
        self.voice_button.setIconSize(QSize(40, 40))  # Adjust the icon size
        self.voice_button.setStyleSheet("QPushButton {"
                                        "background-color: transparent;"  # Transparent background
                                        "border: none;"  # No border
                                        "padding: 0px;"  # No padding
                                        "}")
        self.voice_button.clicked.connect(self.toggle_listening_mode)
        self.input_layout.addWidget(self.voice_button)

        # Send Button
        self.send_button = QPushButton(self)
        self.send_button.setIcon(QIcon("paper-plane.png"))  # Set the icon for the Send button
        self.send_button.setIconSize(QSize(40, 40))  # Adjust the icon size
        self.send_button.setStyleSheet("QPushButton {"
                                       "background-color: transparent;"  # Transparent background
                                       "border: none;"  # No border
                                       "padding: 0px;"  # No padding
                                       "}")
        self.send_button.clicked.connect(self.toggle_send_mode)
        self.input_layout.addWidget(self.send_button)

        # Add input layout to the main layout
        self.layout.addLayout(self.input_layout)

        # Threading for Assistant
        self.worker_thread = None
        self.is_listening = False
        self.is_executing = False

    def display_text(self, text: str):
        self.output_text.append(f"Assistant: {text}")

    def toggle_listening_mode(self):
        """Toggle listening mode between start and stop."""
        if not self.is_listening:
            # Start listening
            self.movie.start()
            self.voice_button.setIcon(QIcon("stop.png"))  # Change icon to Stop
            self.is_listening = True
            self.start_listening()  # Start listening logic
        else:
            # Stop listening
            self.is_listening = False
            self.movie.stop()
            self.voice_button.setIcon(QIcon("voice.png"))  # Revert to mic icon
            if self.worker_thread is not None:
                self.worker_thread.stop()
                self.worker_thread.wait()
                self.worker_thread = None
            self.reset_listening("Stopped listening.")

    def toggle_send_mode(self):
        """Toggle send button between send and stop mode."""
        if not self.is_executing:
            command = self.command_input.text()
            if command.strip() == "":  # Ignore empty commands
                return
            self.command_input.clear()
            self.is_executing = True
            self.send_button.setIcon(QIcon("stop.png"))  # Change icon to Stop
            self.display_text(f"Executing Command: {command}")
            self.va.execute_command(command)  # Execute the command
            self.finish_execution()
        else:
            # Stop the command (You need to implement stopping logic in your VirtualAssistant class)
            self.display_text("Stopping command...")
            self.finish_execution()

    def start_listening(self):
        """Start the voice assistant listening in a separate thread."""
        if self.worker_thread is None:
            self.worker_thread = WorkerThread(self.va)
            self.worker_thread.command_received.connect(self.handle_voice_command)
            self.worker_thread.finished.connect(self.reset_listening)
            self.worker_thread.start()
        else:
            QMessageBox.warning(self, "Warning", "Assistant is already running.")

    def handle_voice_command(self, command):
        """Handle the voice command received from the worker thread."""
        self.display_text(f"Voice Command: {command}")
        self.va.execute_command(command)

    def reset_listening(self, message: str = None):
        """Resets the voice listening mode."""
        self.movie.stop()
        self.voice_button.setIcon(QIcon("voice.png"))  # Revert Mic button to its original state
        self.worker_thread = None
        self.is_listening = False
        if message:
            self.display_text(message)

    def finish_execution(self):
        """Complete the command execution and reset buttons."""
        self.is_executing = False
        self.send_button.setIcon(QIcon("paper-plane.png"))  # Revert to Send icon

if __name__ == "__main__":
    app = QApplication(sys.argv)
    va = VirtualAssistant()  # Create your VirtualAssistant instance
    window = MainWindow(va)
    window.show()
    sys.exit(app.exec_())
