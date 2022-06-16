from flask import Flask, request, render_template, json
from backend import get_coordinates, get_route, get_route_geojson, get_route_many
from clustering import clustering_algo
from battery import charge_and_go, station_coordinates
import pandas as pd


app = Flask(__name__)
app.config["DEBUG"] = True
app.config["APPLICATION_ROOT"] = "/"



@app.route('/', methods=["GET", "POST"])
async def main():
    if request.method == "POST":
        markers = ''
        initial_soc = request.form["start_soc"]
        final_threshold = request.form["arrival_soc"]
        trip_start_at = request.form["trip_start_at"]
       

        # Get coordinates of origin from Geoapify API
        origin = get_coordinates(request.form["origin"])
        origin_lon = origin["features"][0]["geometry"]["coordinates"][0]
        origin_lat = origin["features"][0]["geometry"]["coordinates"][1]
        # Get coordinates of destination from Geoapify API
        destination = get_coordinates(request.form["destination"])
        dest_lon = destination["features"][0]["geometry"]["coordinates"][0]
        dest_lat = destination["features"][0]["geometry"]["coordinates"][1]

        markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(idd="origin",latitude=origin_lat,\
                                                                    longitude=origin_lon,
                                                                            )
        
        markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(idd="destination", latitude=dest_lat,\
                                                                    longitude=dest_lon,
                                                                            )
        
        mid_lat, mid_lon = compute_midPoint(origin_lat,origin_lon,dest_lat,dest_lon)

        pointList, distance, time = get_route(origin_lat,origin_lon,dest_lat,dest_lon)

        path = pd.DataFrame(pointList)
        path.columns = ["lat", "lng"]

        stations = pd.read_csv('bng_df.csv')
        fig, df = clustering_algo(path, stations)
        

        initial_soc = float(initial_soc)
        final_threshold = float(final_threshold)
        total_time = 0
        total_distance = distance
        min_threshold = 15
        dist_travelled = 0
        range_ev = 75
        stop = 1
        range_needed = 0
        ave_speed = 40
        trip_start = trip_start_at 
        night = "02:00:00"
        lst = station_coordinates(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, 
        range_needed, ave_speed, trip_start_at, trip_start, total_time)
        marker_lst = []




        for i in lst.keys():
            id = "stop" + str(i)
            markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                    {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][0]),\
                                                                        longitude=float(lst[i][1]),
                                                                                )

            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][0]),\
                                                                        longitude=float(lst[i][1]),
                                                                                )
            )

        lst2 = list(lst.values())
        lst2.insert(0, [origin_lat, origin_lon])
        lst2.append([dest_lat, dest_lon])
        idx = [i for i in range(len(lst2))]
        res = {idx[i]: lst2[i] for i in range(len(idx))}

        pointListFinal, distance2, time2 = get_route_many(lst2)

        
        # Render the page with the map
        return render_template('results.html', marker_lst = json.dumps(marker_lst), markers = markers, lat=mid_lat, lon=mid_lon, pointListFinal = json.dumps(pointListFinal),
                distance = distance2, time = time2, intial_soc = initial_soc, final_threshold = final_threshold, trip_start_at = json.dumps(trip_start_at), lst = json.dumps(res))


    else:
        # Render the input form
        return render_template('input.html')



def compute_midPoint(lat1,lon1,lat2,lon2):  
  return (lat1 + lat2)/2, (lon1 + lon2)/2