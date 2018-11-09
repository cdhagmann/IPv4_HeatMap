from flask import Flask, jsonify, request
from flask_cors import CORS
from geojson import Feature, Point, FeatureCollection
import pandas as pd

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app)

# sanity check route
@app.route('/locations')
def locations():
    lat1 = float(request.args.get('lat1', -90))
    long1 = float(request.args.get('long1', -180))
    lat2 = float(request.args.get('lat2', 90))
    long2 = float(request.args.get('long2', 180))
    features = FeatureCollection(
        [
            Feature(geometry=Point((long, lat)), properties={"count": count})
            for lat, long, count in pd.read_csv("data/unique.csv").values
            if lat1 <= lat <= lat2 and long1 <= long <= long2
        ]
    )
    return jsonify(features)


if __name__ == "__main__":
    app.run()
