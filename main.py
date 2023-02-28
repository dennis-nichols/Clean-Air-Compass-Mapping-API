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
    
    # if at first there are no sensors try to expand the bounding box
    
    if len(sensors_response['data']) < 1:
      expanded_search = True
      ctr = 1
      while ctr < 4:
        bbox, valid_response = request_location_api(location, factor=ctr)
        sensors_response = get_sensors_bbox_response(nwlong = bbox['min_lon'], nwlat = bbox['max_lat'], 
                                                selong = bbox['max_lon'], selat = bbox['min_lat'])
        
        print('Expanding search')
        print(bbox)
        
        if len(sensors_response['data']) > 1:
          break
        ctr += 1
      
      if len(sensors_response['data']) < 1:
        bbox_polygon = {
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": [[[bbox['min_lon'], bbox['min_lat']],
                [bbox['min_lon'], bbox['max_lat']],
                [bbox['max_lon'], bbox['max_lat']],
                [bbox['max_lon'], bbox['min_lat']],
                [bbox['min_lon'], bbox['min_lat']]
              ]
            ]
          }
        }
        
        return json.loads(json.dumps({"message":"No sensors available in that location, please try another.", "bbox": bbox, "bbox_polygon": bbox_polygon}))
  
    expanded_search = False
    # parse the response from the sensors API into a geodataframe
    geo_df = parse_sensors_bbox_response(sensors_response)
    
    # perform interpolation and return a grid of polygons with interpolated pm2.5 values
    response = make_interpolated_polygons(geo_df, expanded_search=expanded_search)
    
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
  
  else:
    return bbox