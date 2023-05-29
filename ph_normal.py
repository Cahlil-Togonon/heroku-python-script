from routingpy import Valhalla
from routingpy.utils import decode_polyline6
from shapely.geometry import Point, Polygon, shape
import json
import math
import base64
from time import sleep
from github import Github

def generate_normal(coords, threshold):
    client = Valhalla(base_url='https://valhalla1.openstreetmap.de')
    normal = client.directions(locations=coords,instructions=True,profile="pedestrian")
    normal_output = json.dumps(normal.raw, indent=4)
    with open("./results/normal_results"+str(threshold)+".json","w") as f:
        f.write(normal_output)
    
    polyline = normal.raw["trip"]["legs"][0]["shape"]
    decoded = decode_polyline6(polyline)
    route_points = [list(element) for element in decoded]
    aqi = []
    temp = []
    total = 0
    with open("./temp/polygonized"+str(threshold)+".json") as f:
        data = json.load(f)
    data['features'] = sorted(data['features'], key=lambda x: x["properties"]["AQI"], reverse=True)
    points = [Point(i[0], i[1]) for i in route_points]
    for polygon in data['features']:
        if polygon["properties"]["AQI"] <= 500:
            coordinates = polygon["geometry"]
            temp.append([shape(coordinates),polygon["properties"]["AQI"]])
    for i in points:
        for j in temp:
            if j[0].contains(i):
                aqi.append([j,i])
                break
    x_distance = 0
    y_distance = 0
    total_distance = 0
    for i in range(len(aqi)-1):
        x_distance += int(110.574)*(aqi[i][1].x-aqi[i+1][1].x)
        y_distance += int(111.320)*math.cos((aqi[i][1].y+aqi[i+1][1].y)/2)*(aqi[i][1].y-aqi[i+1][1].y)
        level = aqi[i][0][1]
        distance = math.sqrt((abs(aqi[i][1].x-aqi[i+1][1].x))**2+(abs(aqi[i][1].y-aqi[i+1][1].y))**2)
        total += distance*level
        total_distance += distance
        
    coded_string = "Z2hwXzY3emJ2MGpUdkZRVjdJR201ZXpNSWQ1dU5tOWFHRzNiakp3Tg=="
    g = Github(base64.b64decode(coded_string).decode("utf-8"))
    repo = g.get_repo("pctiope/heroku-python-script")
    contents = repo.get_contents("/results/normal_results.raw", ref="master")
    repo.update_file(contents.path, "updated normal_results.raw", normal_output, contents.sha, branch="master")
    return total/total_distance, total