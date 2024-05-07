from flask import Flask, render_template, request, jsonify, abort
import json

JSON_PATH = "summarizedNews.json"
data = []
USERNAME = # username for the post request
PASSWORD = # password for the post request


app = Flask(__name__)

def load_data():
    global data
    with open(JSON_PATH) as file:
        data = json.load(file)

@app.route('/update_news', methods=['POST'])
def save_to_json():
    # Extract username and password from request
    username = request.headers.get('username')
    password = request.headers.get('password')

    if not is_valid_credentials(username, password):
        abort(401, 'Invalid username or password')

    global data
    data = request.json

    with open(JSON_PATH, "w") as file:
        json.dump(data, file, indent=4)
        
    return jsonify({"message": "Data saved successfully"})

def is_valid_credentials(username, password):
    return username == USERNAME and password == PASSWORD

@app.route('/')
def index():
    load_data()
    index = 0
    return get_news(index)

@app.route('/<int:index>')
def get_news(index):
    load_data()
    if index < 0 or index >= len(data):
        return "Invalid index"

    context = {
        'NewsHeadline': data[index]['headline'],
        'NewsParagraph': data[index]['summary'],
        'ImageLink': data[index]['image'],
        'CurrentLink': data[index]['url'],
        'NextLink': f'/{index + 1}' if index + 1 < len(data) else '/',
        'PreviousLink': f'/{index - 1}' if index > 0 else '/',
    }
    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(debug=True)