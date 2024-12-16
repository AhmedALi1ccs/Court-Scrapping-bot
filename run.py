import sys
import os
import webbrowser
from threading import Timer

# Explicitly import werkzeug and its components
try:
    import werkzeug
    import werkzeug.urls
    from werkzeug.urls import url_quote
    import flask
    from flask import Flask, request, send_file, render_template
    import flask_cors
except ImportError as e:
    # If import fails, try to modify sys.path
    print(f"Initial import error: {e}")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        # If running as exe, use sys._MEIPASS
        base_path = getattr(sys, '_MEIPASS', current_dir)
    else:
        base_path = current_dir
        
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
        
    # Try importing again after path modification
    try:
        import werkzeug
        import werkzeug.urls
        from werkzeug.urls import url_quote
        import flask
        from flask import Flask, request, send_file, render_template
        import flask_cors
        print("Successfully imported after path modification")
    except ImportError as e:
        print(f"Failed to import after path modification: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

# Import Flask app after werkzeug is properly imported
try:
    from app import app
except ImportError as e:
    print(f"Error importing app: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

def open_browser():
    try:
        webbrowser.open('http://127.0.0.1:5000/')
    except Exception as e:
        print(f"Error opening browser: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    try:
        # If running as executable, ensure paths are correct
        if getattr(sys, 'frozen', False):
            try:
                template_folder = os.path.join(sys._MEIPASS, 'templates')
                static_folder = os.path.join(sys._MEIPASS, 'static')
                app.template_folder = template_folder
                app.static_folder = static_folder
                print(f"Template folder set to: {template_folder}")
            except Exception as e:
                print(f"Error setting up folders: {e}")
                input("Press Enter to exit...")

        # Open browser after a short delay
        Timer(1.5, open_browser).start()
        
        print("Starting Flask application...")
        # Run the app
        app.run(port=5000, debug=False)
    except Exception as e:
        print(f"Error running application: {e}")
        input("Press Enter to exit...")  # Keep window open to see error
        sys.exit(1)
