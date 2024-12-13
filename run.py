import sys
import os
import webbrowser
from threading import Timer
from flask import Flask
from app import app  # Import your Flask app

def open_browser():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # If running as executable, ensure paths are correct
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app.template_folder = template_folder
        app.static_folder = static_folder

    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    # Run the app
    app.run(port=5000)