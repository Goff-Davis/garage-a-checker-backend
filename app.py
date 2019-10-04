import json
import os
import firebase_admin
import email_helper
import re
from firebase_admin import credentials, firestore
from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from requests import get
from datetime import datetime

# flask config
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app)

# set up firebase service account
cred = credentials.Certificate({
    "private_key": os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
    "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
    "type": os.environ.get('FIREBASE_TYPE'),
    "token_uri": os.environ.get('FIREBASE_TOKEN_URI')
})
firebase_admin.initialize_app(cred)

db = firestore.client()

def jsonify_error(msg):
    return jsonify({'error': msg})

# get and parse the data from the ucf homepage
def api():
    page = get(os.environ.get('SCRAPE_URL'))

    if page.status_code != 200:
        send_email("There was an error loading UCF Parking Website. Make sure the website is still up and the URL hasn't been changed.")
        return jsonify_error(page.text)

    soup = BeautifulSoup(page.content, 'html.parser')

    # This is the row containing Garage A data
    a_data = soup.find("tr", {"id": "ctl00_MainContent_gvCounts_DXDataRow0"})

    name = a_data.contents[1].text

    if name != 'Garage A':
        send_email('Incorrect garage name parsed. Make sure the website is still up and unchanged.')
        return jsonify_error('Incorrect garage name parsed. Make sure the website is still up and unchanged.')

    spaces = a_data.contents[2].text.rstrip().replace('\n', '').split('/')
    spaces_left = int(spaces[0])
    max_spaces = int(spaces[1])

    if spaces_left > max_spaces:
        spaces_left = max_spaces

    percent_full = round(((max_spaces - spaces_left) / max_spaces) * 100, 2)

    data = {
        'max_spaces': max_spaces,
        'spaces_left': spaces_left,
        'spaces_filled': max_spaces - spaces_left,
        'percent_full': percent_full
    }

    return jsonify(data)

# save the garage info to the database
@app.route('/')
def add():
    data = api().json

    if 'error' in data:
        send_email('Error in garage data. Ensure scraper is working correctly.')
        return 'Failure!'

    date = datetime.now()
    data['date'] = date.isoformat()
    data['timestamp'] = int(date.timestamp())

    doc_ref = db.collection(u'latest_info').document('garage-a')
    doc_ref.set(data)
    return 'Success! Check your database.'

@app.errorhandler(404)
def error404(err):
    return jsonify_error('Page not found')


@app.errorhandler(408)
def error408(err):
    return jsonify_error('Request timed out')


@app.errorhandler(500)
def error500(err):
    return jsonify_error('Internal server error')

if __name__ == '__main__':
    app.run(threaded=True)
