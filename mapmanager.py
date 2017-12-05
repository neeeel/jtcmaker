import io
import urllib.request
from PIL import Image
import math
from math import log, exp, tan, atan, pi, ceil,cos,sin,atan2,sqrt
import bisect
import json
from operator import itemgetter



google_api_key = "AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

zoomValues = list(reversed([0.703, 0.352, 0.176, 0.088, 0.044, 0.022, 0.011, 0.005, 0.003, 0.001, 0.0005]))

def __init__(map_height,map_width, zoom, coords):
    zoomValues = [0.703, 0.352, 0.176, 0.088, 0.044, 0.022, 0.011, 0.005, 0.003, 0.001, 0.0005]
    zoomValues = list(reversed(zoomValues))
    map_height = map_height
    map_width = map_width
    zoom = zoom
    center_lat,center_lon = coords
    #print(center_lat,center_lon)


def get_centre_of_points_alternate(points,zoom):
    points = list(map(lambda x: latlontopixels(x, zoom), points))
    #print("points is", points)
    print("max x is ",max(points,key=itemgetter(0)))
    print("min x is ", min(points, key=itemgetter(0)))
    print("max y is ", max(points, key=itemgetter(1)))
    print("min y is ", min(points, key=itemgetter(1)))
    avs = [sum(y) / len(y) for y in zip(*points)]
    #print("avs are",avs)
    centre = pixelstolatlon(avs[0], avs[1], zoom)
    return centre


def get_centre_of_points(points,zoom):
    ###
    ### dont use, has been superceded by alternate versino
    ###

    points = list(map(lambda x :latlontopixels(x,14),points))
    print("points is", points)
    maxX = max(points, key=lambda item: item[0])[0]
    maxY = min(points, key=lambda item: item[1])[1]
    minX = min(points, key=lambda item: item[0])[0]
    minY = max(points, key=lambda item: item[1])[1]
    print(maxX, minX, maxY, minY)
    #centreX = maxX - ((maxX - minX) * 0.5)
    #centreY = maxY - ((maxY - minY) * 0.5)
    centreX = (maxX + minX) / 2
    centreY = (maxY + minY) / 2
    #print("before conversion", centreX, centreY)
    centre = pixelstolatlon(centreX, centreY,14)
    #print("centre is ",centre)
    return centre


def calculate_zoom_value(points):
    GLOBE_WIDTH = 256
    west = min(points, key=lambda item: item[1])[1]
    east = max(points, key=lambda item: item[1])[1]
    north = max(points, key=lambda item: item[0])[0]
    south = min(points, key=lambda item: item[0])[0]
    print("west,east", west, east, north, south)
    delta = 0
    angle = east - west
    angle2 = north - south  # (latRad(north)-latRad(south))/math.pi
    print("angles are", angle, angle2)
    zoom = math.floor(math.log(640 * 360 / angle / GLOBE_WIDTH) / math.log(2)) - delta
    zoom1 = math.floor(math.log(640 * 360 / angle2 / GLOBE_WIDTH) / math.log(2)) - 1
    print("zoomes are", zoom, zoom1)
    if angle2 > angle:
        angle = angle2
        delta = 1
    if (angle < 0):
        angle += 360
    zoom = math.floor(math.log(640 * 360 / angle / GLOBE_WIDTH) / math.log(2)) - delta
    return min(zoom, zoom1)

def latlontopixels(coords,zoom):
    ###
    ### this gives us a value ( in meters? ) of y,x !!!! for lat lon coordinates on a projection of the whole world
    ###
    lat, lon = coords
    mx = (lon * ORIGIN_SHIFT) / 180.0
    my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
    my = (my * ORIGIN_SHIFT) /180.0
    res = INITIAL_RESOLUTION / (2**zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def pixelstolatlon(px, py, zoom):

    ### the two values px and py are reversed, its confusing, but latlontopixels gives an (x,y) which is equivalent to
    ### (lon,lat) I suppose because lat is actually the y direction. Pixelstolatlon takes the (x,y) and reverses them
    ### to give us back the original (lat,lon)
    ###
    ### lol
    ###
    res = INITIAL_RESOLUTION / (2**zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon


def pixelDistance(lat1,lon1,lat2,lon2,zoom):
    ###
    ### takes 2 lat/lons, and a zoom level, and calculates the distance in pixels between then given the zoom value
    ###
    ### returns (xdiff,ydiff,dist)
    ###

    x1,y1 = latlontopixels((lat1,lon1),zoom)
    x2,y2 = latlontopixels((lat2,lon2),zoom)
    #print("xdiff is",x1-x2,"ydiff is ",y1-y2)
    print(math.sqrt(math.pow(x1-x2,2) + math.pow(y1-y2,2)),21-zoom)
    return (x2-x1,-(y2-y1),int(math.sqrt(math.pow(x1-x2,2) + math.pow(y1-y2,2)))) #'>> (21-zoom)


def get_nearest_site(x,y):
    pass

def get_coords(centre,coords,zoom,size=800):
    ## takes a lat and long pair, converts them to x,y coordinates that refer to where on the drawing canvas the point is, given that we know the lat,lon of the centre point of the map
    point = latlontopixels(coords,zoom)
    centre = latlontopixels((centre[0],centre[1]),zoom)
    x = centre[0]-point[0]
    y = centre[1]-point[1]
    scaleFactor = size/640
    x*=scaleFactor # scaling factor, because we have stretched the map to 800 by 800
    y*=scaleFactor
    return (size/2) - x, (size/2) + y

def get_lat_lon_from_x_y(centre,x,y,zoom,size = 800):
    ###
    ### given that we know the centre of the map is (size/2,size/2) and we know the lat,lon of the centre point, we can calculate
    ### the lat,lon of any other x,y point on the map
    ###
    print("new coords are",x,y,zoom)
    xdiff, ydiff = x - (size/2), y - (size/2)
    print("diffs are",xdiff,ydiff)
    centreAsPixels = latlontopixels(centre, zoom)
    print("centre as pixels is",centreAsPixels)
    newLatLon = pixelstolatlon(centreAsPixels[0] + xdiff, centreAsPixels[1] - ydiff, zoom)
    return newLatLon

def get_map_with_path(self,tps,path):
    base = 65
    step = int(len(path) / 150) + 1
    noOfPoints = len(path) * 12
    #print("tps are ",tps)
    markers = ""
    pathString = "&path="
    markers += "&markers=color:green%7Clabel:A%7C" + str(self.tps[0][0]) + "," + str(self.tps[0][1])
    for i, tp in enumerate(self.tps[1:-1]):
        markers += "&markers=color:blue%7Clabel:" + chr(i + 1 + base) + "%7C" + str(tp[0]) + "," + str(tp[1])
    markers += "&markers=color:Red%7Clabel:" + chr(len(self.tps) - 1 + base) + "%7C" + str(self.tps[-1][0]) + "," + str(self.tps[-1][1])
    for p in path[::step]:
        pathString+= str(p[0]) + "," + str(p[1]) + "%7C"
    pathString += str(path[-1][0]) + "," + str(path[-1][1])
    url = "http://maps.googleapis.com/maps/api/staticmap?&size=" + str(self.map_width) + "x" + str(self.map_height) + markers + pathString + "&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print("url for route map is",url)
    buffer = urllib.request.urlopen(url)
    image = Image.open(buffer).convert('RGB')
    return image

def change_zoom(self,val):
    self.zoom+=val
    return self.load_map(self.center_lat, self.center_lon)

def load_map_without_labels(lat,lon,zoom):
    url = "http://maps.googleapis.com/maps/api/staticmap?style=element:labels|visibility:off&zoom=" + str(zoom) + "&center="+ str(lat) + "," + str(lon) + "&size=640x640&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    unlabeledMap = Image.open(buffer)#.convert('RGB')
    return unlabeledMap

def load_high_def_map_without_labels(lat,lon,zoom):
    url = "http://maps.googleapis.com/maps/api/staticmap?style=element:labels|visibility:off&zoom=" + str(zoom) + "&center="+ str(lat) + "," + str(lon) + "&size=640x640&scale=2&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    unlabeledMap = Image.open(buffer)#.convert('RGB')
    return unlabeledMap

def load_map_with_labels(lat,lon,zoom):
    url = "http://maps.googleapis.com/maps/api/staticmap?center=" + str(lat) + "," + str(lon) + "&zoom=" + str(zoom) + "&size=640x640&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    image = Image.open(buffer)#.convert('RGB')
    return image

def load_high_def_map_with_labels(lat,lon,zoom,imageType="roadmap"):
    url = "http://maps.googleapis.com/maps/api/staticmap?center=" + str(lat) + "," + str(lon) + "&zoom=" + str(zoom) + "&maptype=" + imageType + "&size=640x640&scale=2&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    image = Image.open(buffer)#.convert('RGB')
    return image

def load_map_with_labels_and_markers(lat,lon,zoom,points):
    markers = ""
    for i, tp in enumerate(points):
        markers += "&markers=color:blue%7C" + str(tp[0]) + "," + str(tp[1])
    url = "http://maps.googleapis.com/maps/api/staticmap?center=" + str(lat) + "," + str(lon) + "&zoom=" + str(
        zoom) + markers +  "&size=640x640&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    image = Image.open(buffer)  # .convert('RGB')
    return image

def load_high_def_map_with_labels_and_markers(lat,lon,zoom,points):
    markers = ""
    for i, tp in enumerate(points):
        markers += "&markers=color:blue%7C" + str(tp[0]) + "," + str(tp[1])
    url = "http://maps.googleapis.com/maps/api/staticmap?center=" + str(lat) + "," + str(lon) + "&scale=2&zoom=" + str(
        zoom) + markers +  "&size=640x640&key=AIzaSyC1PWgJ7Pcg2xfXLHJyCospiYI9uALAMss"
    print(url)
    buffer = urllib.request.urlopen(url)
    image = Image.open(buffer)  # .convert('RGB')
    return image

def load_overview_map(points):
    centre = get_centre_of_points_alternate(points,14)
    zoom = calculateZoomValueAlternate(points)
    img = load_high_def_map_with_labels(centre[0],centre[1],zoom)
    return (img,centre,zoom)

def load_overview_map_with_markers(points):
    centre = get_centre_of_points_alternate(points, 14)
    zoom = calculateZoomValueAlternate(points)
    img = load_high_def_map_with_labels_and_markers(centre[0], centre[1], zoom, points)
    return (img, centre, zoom)

def load_overview_map_without_street_labels(points):
    centre = get_centre_of_points_alternate(points, 14)
    zoom = calculate_zoom_value(points)
    img = load_high_def_map_without_labels(centre[0], centre[1], zoom)
    #img.show()
    for point in points:
        print(point)
        print(latlontopixels(point,zoom))
    return (img, centre, zoom)

def get_road_name(lat,lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(lat) + "," + str(lon) + "&sensor=true_or_false&key=AIzaSyDRVvMxvveTE7ladKBhUnptw9-lOoHMAAU"
    print(url)
    buffer = urllib.request.urlopen(url).read().decode('utf8')
    result = json.loads(buffer)
    for item in result["results"][0]["address_components"]:
        # print(item["types"][0])
        if item["types"][0] == "route":
            return item["long_name"]
    return ""

def _window_x_y_to_grid(self, x, y):
    '''
    converts graphical x, y coordinates to grid coordinates
    where (0, 0) is the very center of the window
    takes in the actual windows co-ords, and returns relative coords
    '''
    center_x = self.map_width / 2
    center_y = self.map_height / 2
    new_x = x - center_x
    new_y = -1 * (y - center_y)
    return new_x, new_y

def update_values(self,height,width):
    self.map_height = height
    self.map_width = width

def grid_x_y_to_window(self,grid_x,grid_y):
    center_x = self.map_width / 2
    center_y = self.map_height / 2
    new_x = grid_x + center_x
    new_y = 1 * (grid_y + center_y)
    return new_x, new_y

def x_y_to_lat_lon(self, x, y):
    grid_x, grid_y = self._window_x_y_to_grid(x, y)
    offset_x_degrees = (float(grid_x) / self.map_width) * self.degrees_in_map
    offset_y_degrees = (float(grid_y) / self.map_height) * self.degrees_in_map
    # lat = y, lon = x
    return self.center_lat + offset_y_degrees, self.center_lon + offset_x_degrees

def lat_lon_to_x_y(self,lat,lon):
    offset_y_degrees = lat - self.center_lat
    offset_x_degrees = lon - self.center_lon
    grid_y = -1 * (offset_y_degrees / self.degrees_in_map) * self.map_height
    grid_x = (offset_x_degrees / self.degrees_in_map) * self.map_width
    #return grid_x,grid_y
    return self.grid_x_y_to_window(grid_x,grid_y)

@property
def degrees_in_map(self):
    '''
    This logic is based on the idea that zoom=0 returns 360 degrees
    '''
    return (self.map_height / 256.0) * (360.0 / pow(2, self.zoom))

def getDist(p1,p2):
    x,y = p1
    x1, y1 = p2
    #x=truncate(x,5)
    #y=truncate(y,5)
    x = float(x)
    y = float(y)
    #print(p1,x,y)
    #x1 = truncate(x1, 5)
    #y1 = truncate(y1, 5)
    xdiff = abs(x1-x)
    ydiff  = abs(y1-y)
    return math.sqrt(xdiff**2 + ydiff**2)


points = [[	51.375375,-2.303901],[53.39236,-6.39286],[53.39221,-6.39262]]
#centre = get_centre_of_points(points,14)
#print("centre is--",centre)
#zoom = calculateZoomValueAlternate(points)
#print(zoom)
#centre = get_centre_of_points(points,zoom)
#print("centre is--",centre)

points = [[51.375375, -2.303901], [51.373611, -2.304148], [51.357788, -2.315616], [51.357347, -2.315961], [51.343584, -2.316484], [51.337356, -2.319944], [51.330684, -2.317093], [51.332954, -2.317976], [51.310785, -2.305842], [51.309345, -2.306097], [51.286027, -2.30028], [51.283964, -2.300818], [51.28565, -2.300219], [51.254324, -2.260063]]

