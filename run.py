from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from indiana_court_scraper import IndianaCourtCaseScraper
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to track scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_name': '',
    'error': None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def run_scraper(input_path, output_path):
    global scraping_status
    try:
        scraping_status['is_running'] = True
        scraper = IndianaCourtCaseScraper(input_path, output_path)
        scraper.navigate_and_search()
    except Exception as e:
        scraping_status['error'] = str(e)
    finally:
        scraping_status['is_running'] = False
        scraper.close()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global scraping_status
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
            
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'results_' + filename)
            
            file.save(input_path)
            
            # Start scraping in a separate thread
            if not scraping_status['is_running']:
                scraping_thread = threading.Thread(
                    target=run_scraper,
                    args=(input_path, output_path)
                )
                scraping_thread.start()
                return 'Scraping started'
            else:
                return 'A scraping job is already running', 400
                
        return 'Invalid file type', 400
        
    return render_template('index.html', status=scraping_status)

@app.route('/status')
def get_status():
    return scraping_status

@app.route('/download')
def download_results():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        result_files = [f for f in files if f.startswith('results_')]
        if result_files:
            latest_file = max(result_files, key=lambda x: os.path.getctime(
                os.path.join(app.config['UPLOAD_FOLDER'], x)))
            return send_file(
                os.path.join(app.config['UPLOAD_FOLDER'], latest_file),
                as_attachment=True,
                download_name='court_case_results.csv'
            )
    except Exception as e:
        return str(e), 400
    return 'No results file found', 404

if __name__ == '__main__':
    app.run(debug=True)
