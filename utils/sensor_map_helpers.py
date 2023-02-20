import pandas as pd
import geopandas as gpd
import requests
import time
import json
from dotenv import load_dotenv
import os
import re

load_dotenv()

API_KEY  = os.environ.get('API_KEY')
LOC_IQ_KEY = os.environ.get('LOC_IQ_KEY')


def is_postal_code(query: str):
    """
    Returns if a string matches US postal code format or not.
    The regular expression pattern matches the US ZIP code format, which can optionally include a ZIP+4 code.
    Examples: 12345, 12345-6789
    """
    pattern = r'^\d{5}(-\d{4})?$'
    match = re.match(pattern, query)
    if match:
        return True
    else:
        return False


def request_location_api(query: str):

    url = "https://us1.locationiq.com/v1/search"
    if is_postal_code(query):
        data = {
            'key': LOC_IQ_KEY,
            'postalcode': int(query),
            'format': 'json',
            'countrycodes': 'us'
        }

    else:
        data = {
            'key': LOC_IQ_KEY,
            'q': query,
            'format': 'json',
            'countrycodes': 'us'
        }
    headers = {
        'Referer': 'https://www.kaggle.com/'
    }
    response = requests.get(url, params=data, headers=headers)
    data = json.loads(response.text)
    bounding_box = data[0]['boundingbox']
    bbox = {
        'min_lat': float(bounding_box[0]),
        'max_lat': float(bounding_box[1]),
        'min_lon': float(bounding_box[2]),
        'max_lon': float(bounding_box[3])
    }

    return bbox


def get_sensors_bbox_response(nwlong: float, nwlat: float, selong: float, selat: float):
    base_url = "https://api.purpleair.com/v1/sensors/"
    fields = 'sensor_index,name,latitude,longitude,altitude,pm1.0,pm2.5,pm10.0,pm2.5_10minute,pm2.5_30minute,pm2.5_60minute'
    query = f'?fields={fields}&location_type=0'
    bbox = f'&nwlng={nwlong}&nwlat={nwlat}&selng={selong}&selat={selat}'

    url = base_url + query + bbox
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return json.loads(response.text)


def parse_sensors_bbox_response(response_object) -> gpd.GeoDataFrame:
    data = response_object
    flat_dicts = []
    for sensor in data['data']:
        flat_dict = {
            'sensor_index': sensor[0],
            'name': sensor[1],
            'latitude': sensor[2],
            'longitude': sensor[3],
            'altitude': sensor[4],
            'pm1.0': sensor[5],
            'pm2.5': sensor[6],
            'pm10.0': sensor[7],
            'pm2.5_10minute': sensor[8],
            'pm2.5_30minute': sensor[9],
            'pm2.5_60minute': sensor[10]
        }
        flat_dicts.append(flat_dict)

    sensor_df = pd.DataFrame(flat_dicts)
    sensor_gdf = gpd.GeoDataFrame(sensor_df, geometry=gpd.points_from_xy(
        sensor_df.longitude, sensor_df.latitude))

    return sensor_gdf


def convert_to_utm_crs(df):

    df.set_crs(epsg=4326, inplace=True, allow_override=True)
    # Find centroid of the dataframe
    centroid = df.centroid.iloc[0]

    # Determine UTM zone based on centroid
    utm_zone = int((centroid.x + 180) / 6) + 1
    if centroid.y < 0:
        utm_zone = -utm_zone

    # Get the EPSG code for the UTM zone
    epsg_code = f'326{utm_zone:02d}' if utm_zone > 0 else f'327{-utm_zone:02d}'

    # Convert the dataframe to the UTM CRS
    df_utm = df.to_crs(epsg=epsg_code)

    return df_utm
