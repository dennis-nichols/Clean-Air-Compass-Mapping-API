from fastapi import FastAPI
from utils.sensor_map_helpers import request_location_api, get_sensors_bbox_response, parse_sensors_bbox_response, convert_to_utm_crs

app = FastAPI()


@app.get("/points/{location}")
async def get_map(location: str):
  
  # call location IQ API to get bounding box for location
  bbox = request_location_api(location)
  # call the purple API to get data for sensors within the bbox
  sensors_response = get_sensors_bbox_response(nwlong = bbox['min_lon'], nwlat = bbox['max_lat'], 
                                               selong = bbox['max_lon'], selat = bbox['min_lat'])
  # parse the response from the sensors API into a geodataframe
  geo_df = parse_sensors_bbox_response(sensors_response)
  # convert the geodataframe to an appropriate coordinate reference system based on its US location - NOTE: will need to change for international use
  geo_df = convert_to_utm_crs(geo_df)
  # conver the geodataframe to a geo_json object
  geo_json = geo_df.to_json()
  
  return geo_json
