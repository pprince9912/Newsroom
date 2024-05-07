from flask import Flask, jsonify
import subprocess
import requests
import time

app = Flask(__name__)

PYTHON_PATH = # path of the python exe
GETSUMMARIZEDNEWS_PATH = # path of getSummarizedNews.py
URL = # URL of the server started by getSummarizedNews.py

@app.route('/newsroom')
def start_api_server():
    # Start the API server
    process = subprocess.Popen([PYTHON_PATH, GETSUMMARIZEDNEWS_PATH])
    
    time.sleep(30)
    
    # Send a request to the newly started server
    response = requests.get(f'{URL}/')

    print(response)
    # Terminate the API server process
    process.terminate()
    
    return jsonify({'message': 'API server started and request sent successfully.'}), 200

if __name__ == '__main__':
    app.run(debug=False, port=8080)