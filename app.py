import os
import json

from flask import Flask
from flask import render_template
from flask import request

from data import parse_query, fetch_cost, load_from_file_cache, fetch_history, fetch_data

COUNCILS = load_from_file_cache('../data/councils.json', fetch_data)

app = Flask(__name__)

@app.route('/')
def index():
    query = request.args.get('query')
    category = ''
    council = ''
    location = ''
    history = ''
    cost = ''
    if query:
        category, council, place = parse_query(query)
        location = place.raw['geometry']['location']
        cost = fetch_cost()
        entries = []
        history = fetch_history(council, COUNCILS)
    return render_template(
        'index.html',
        query=query,
        category=category,
        council=council,
        location=location,
        cost=cost,
        history=history
        )
    
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
