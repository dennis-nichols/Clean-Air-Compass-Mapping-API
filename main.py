from fastapi import FastAPI
from utils.sensor_map_helpers import request_location_api, get_sensors_bbox_response, parse_sensors_bbox_response, make_interpolated_polygons
import json

app = FastAPI()

@app.get("/points/{location}")
async def get_map(location: str):
  
  # call location IQ API to get bounding box for location
  bbox, valid_response = request_location_api(location)
  
  print(bbox)
  
  if valid_response:
    # call the purple API to get data for sensors within the bbox
    sensors_response = get_sensors_bbox_response(nwlong = bbox['min_lon'], nwlat = bbox['max_lat'], 
                                                selong = bbox['max_lon'], selat = bbox['min_lat'])

    # parse the response from the sensors API into a geodataframe
    geo_df = parse_sensors_bbox_response(sensors_response)
    
    # perform interpolation and return a grid of polygons with interpolated pm2.5 values
    response = make_interpolated_polygons(geo_df)
    
    return response
  else:
    return bbox


@app.get("/average_pollution/{location}")
async def get_average_pollution(location: str):
  
  # call location IQ API to get bounding box for location
  bbox, valid_response = request_location_api(location)
  
  if valid_response:
    # call the purple API to get data for sensors within the bbox
    sensors_response = get_sensors_bbox_response(nwlong = bbox['min_lon'], nwlat = bbox['max_lat'], 
                                                selong = bbox['max_lon'], selat = bbox['min_lat'])

    # parse the response from the sensors API into a geodataframe
    geo_df = parse_sensors_bbox_response(sensors_response)
  
  return geo_df['pm2.5_60minute'].mean()