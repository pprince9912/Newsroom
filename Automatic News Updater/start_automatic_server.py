import requests
import time

URL = # url of the server started by initializeServer.py

def call_route():
    url = f'{URL}/newsroom'
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Route called successfully at {time.ctime()}")
    else:
        print(f"Failed to call route. Status code: {response.status_code}")

while True:
    call_route()
    time.sleep(45 * 60)