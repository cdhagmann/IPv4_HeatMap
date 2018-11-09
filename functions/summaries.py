import pandas as pd
import sys
from sqlalchemy import create_engine
import numpy as np
import itertools
import math
from geojson import Feature, Point, FeatureCollection, dumps

df = pd.read_csv(sys.argv[1])

latlong = df[["latitude", "longitude"]].dropna()
summary = (
    latlong.groupby(["latitude", "longitude"])["latitude"]
    .count()
    .reset_index(name="count")
)
summary.to_csv('data/unique.csv', index=False)

engine = create_engine("sqlite://", echo=False)
summary.to_sql("points", con=engine)


def map_grid(lat1, long1, lat2, long2, k=80):
    lat_grid = zip(np.linspace(lat1, lat2, k + 1), np.linspace(lat1, lat2, k + 1)[1:])
    long_grid = zip(
        np.linspace(long1, long2, k + 1), np.linspace(long1, long2, k + 1)[1:]
    )
    for ((sublat1, sublat2), (sublong1, sublong2)) in itertools.product(
        lat_grid, long_grid
    ):
        yield sublat1, sublong1, sublat2, sublong2


def points(lat1, long1, lat2, long2, ):
    lat1, lat2 = sorted((lat1, lat2))
    long1, long2 = sorted((long1, long2))

    points = engine.execute(
        "SELECT * FROM points WHERE latitude BETWEEN {0} AND {1} AND longitude BETWEEN {2} AND {3}".format(
            lat1, lat2, long1, long2
        )
    ).fetchall()
    return points


def cluster(lat1, long1, lat2, long2):
    all_points = points(lat1, long1, lat2, long2)

    if not all_points:
        return
    else:
        all_points = np.array(all_points)
        count = np.sum(all_points[:, 3])
        weights = all_points[:, 3] / count
        center_lat = np.dot(weights, all_points[:, 1])
        center_long = np.dot(weights, all_points[:, 2])
        return round(center_lat, 4), round(center_long, 4), count


def reduce_recursive(lat1, long1, lat2, long2, N=5000):
    point_list = []
    all_points = points(lat1, long1, lat2, long2)
    if len(all_points) > N:
        for latlongbounds in map_grid(lat1, long1, lat2, long2, k=5):
            point_list.extend(reduce_recursive(*latlongbounds))
    else:
        for latlongbounds in map_grid(lat1, long1, lat2, long2, k=10):
            point = cluster(*latlongbounds)
            if point:
                print(point)
                point_list.append(point)

    return point_list


def main():
    min_lat = summary["latitude"].min()
    max_lat = summary["latitude"].max()
    min_long = summary["longitude"].min()
    max_long = summary["longitude"].max()

    shorten_list = np.array(reduce_recursive(min_lat, min_long, max_lat, max_long))

    features = FeatureCollection([Feature(geometry=Point((lat, long)), properties={"count": count}) for lat, long, count in shorten_list])

    df = pd.DataFrame.from_dict(
        {
            "latitude": shorten_list[:, 0],
            "longitude": shorten_list[:, 1],
            "count": shorten_list[:, 2],
        }
    )
    df.to_csv("data/summary.csv", index=False)
  
if __name__ == "__main__":
    main()

