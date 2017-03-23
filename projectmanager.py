from tkinter import filedialog
from PIL import Image,ImageDraw,ImageTk,ImageFont
import mapmanager
import pandas as pd
from tkinter import filedialog
import openpyxl
import os
import xlwt
from openpyxl.chart import LineChart,PieChart,BarChart

outline = 3 ## witdth of line to draw circles on the map
siteDetails = None

excelMapWidth = 576.5295 ### the size of the map in the excel template sheet
excelMapHeight = 576.5295
sites = {}
current_label = 64
individual_site_zoom_value = 20
overview_map_details = []

def load_sites():
    pass

def save_sites():
    pass

def decrement_arm_label():
    global current_label
    ###
    ### a label was deleted in the user interface, need to decrement the counter so we give the correct letter
    ### when requested
    current_label-=1

def change_site_zoom(site,value):
    print("current zoom of site",site,"is",sites[site]["zoom"])
    if value == "+":
        sites[site]["zoom"] += 1
    else:
        sites[site]["zoom"]-=1
    print("new zoom of site", site, "is", sites[site]["zoom"])
    map = mapmanager.load_high_def_map_with_labels(sites[site]["coords"][0], sites[site]["coords"][1], sites[site]["zoom"])
    map.save(str(sites[site]["Site Name"]) + ".png")


def add_arm_to_site(siteName,x,y):
    global current_label,siteDetails,sites
    if siteDetails is None:
        return
    current_label += 1
    armName = chr(current_label)
    edit_arm(siteName, armName, x, y)
    return chr(current_label)

def delete_arm_from_site(siteName,armName):
    site = sites.get(siteName, {})
    print("before delete, site is",site)
    try:
        del site["Arms"][armName]
    except Exception as e:
        pass
        ### something went wrong, and the arm didnt exist
    print("after delete, site is", site)

def edit_arm(siteName,armName,x,y):
    global siteDetails, sites
    site = sites.get(siteName, {})
    print("site is", site)
    site["coords"] = []
    row = siteDetails[siteDetails["Site Name"] == siteName]
    siteLatLon = row.values.tolist()[0][1:]
    armLatLon = mapmanager.get_lat_lon_from_x_y(siteLatLon, x, y, individual_site_zoom_value)
    site["coords"]=mapmanager.get_coords(overview_map_details[1],siteLatLon,overview_map_details[2],size=1280)
    print("location for arm is", armLatLon)
    print("road for arm is", mapmanager.get_road_name(armLatLon[0], armLatLon[1]))
    site["Arms"][armName] = {}
    site["Arms"][armName]["latlon"] = armLatLon
    site["Arms"][armName]["coords"] = (x, y)
    site["Arms"][armName]["road"] = mapmanager.get_road_name(armLatLon[0], armLatLon[1])
    site["Arms"][armName]["orientation"] = 0
    print("site is now", site)
    print("")
    sites[siteName] = site

def edit_arm_orientation(siteName,armName,orientation):
    global siteDetails, sites
    site = sites.get(siteName, {})
    #print("in edit arm, params are", siteName, armName, x, y)
    site["Arms"][armName]["orientation"] = orientation
    print("site is now", site)

def get_site_map(siteName):
    print("looking for ",str(siteName) + ".png")
    try:
        img = Image.open(str(siteName) + ".png")
        img = img.resize((800, 800), Image.ANTIALIAS)
        print("returning")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        return None

def get_overview_map():
    try:
        img = Image.open("overview.png")
        img = img.resize((400, 400), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        return None

def import_site_details_from_excel():
    global siteDetails
    fileList = list(filedialog.askopenfilenames(initialdir=dir))
    if fileList == []:
        return
    for f in fileList:
        print(f)
        siteDetails = pd.read_excel(f)

def load_project():
    global siteDetails
    import_site_details_from_excel()
    download_all_individual_site_maps()
    download_overview_map()

    fnt = ImageFont.truetype("arial", size=18)
    img2 = Image.open("overview.png").convert('RGB')
    drawimage = ImageDraw.Draw(img2)

    for site in get_all_site_details():
        sites[site[0]] = {}
        sites[site[0]]["Site Name"] = site[0]
        siteNumber = site[0].lower().replace("site","")
        sites[site[0]]["Arms"] ={}
        sites[site[0]]["zoom"] = 20
        sites[site[0]]["coords"] = mapmanager.get_coords(overview_map_details[1],(site[1],site[2]),overview_map_details[2],size=1280)
        x = sites[site[0]]["coords"][0]
        y = sites[site[0]]["coords"][1]
        drawimage.ellipse([x - 15- outline, y - 15- outline, x + 15+ outline, y + 15+ outline], outline="Black",fill = "black")
        drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white",fill = "white")
        drawimage.text((x-8, y-9), text=siteNumber,font=fnt, fill="black")

    img2.save("overview.png")

    print("Sites are ",sites)
    return sites[get_all_site_details()[0][0]]

def load_previous_site(siteName):
    ###
    ### user has pressed the left arrow to move to the previous site
    ###

    global siteDetails,current_label
    print("sitename is", siteName)
    curr = siteDetails[siteDetails["Site Name"] == siteName].index.tolist()[0]
    print("cur is ", curr)
    if curr == 0:
        return sites[siteDetails.iloc[curr].values.tolist()[0]]
    current_label = 64
    return sites[siteDetails.iloc[curr-1].values.tolist()[0]]

def load_next_site(siteName):
    ###
    ### user has pressed the right arrow to move to the next site
    ###
    global siteDetails,current_label
    curr = siteDetails[siteDetails["Site Name"] == siteName].index.tolist()[0]
    print("cur is ",curr)
    try:
        n = siteDetails.iloc[curr+1]
        current_label = 64
        return sites[n.values.tolist()[0]]
    except IndexError as e:
        return sites[siteDetails.iloc[curr].values.tolist()[0]]

def export_to_excel(jobDetails):
    file = filedialog.askopenfilename()
    if file == "" or file is None:
        return
    wb = openpyxl.load_workbook(file,keep_vba=True)

    sht = wb.get_sheet_by_name("Maps")

    img = Image.open("tracsis Logo.jpg")
    imgSmall = img.resize((227, 72), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA1")

    sht = wb.get_sheet_by_name("Dashboard")

    c1 = LineChart()
    c1.title = "Volume Chart"
    c1.style = 13
    sht.add_chart(c1,"B5")

    c1= BarChart()
    c1.title = "Class Ratios"
    sht.add_chart(c1,"AB5")

    c1 = BarChart()
    c1.title = "Total Volumes"
    sht.add_chart(c1, "M25")


    sht = wb.get_sheet_by_name("Maps")
    #img = Image.open("tracsis Logo.jpg")
    #imgSmall = img.resize((227, 72), Image.ANTIALIAS)
    #excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    #sht.add_image(excelImageSmall, "A1")

    ### TODO grouping of sites in case sites are scattered far apart making the overview map difficult to use

    points = get_all_site_coords()
    overview_map_details = mapmanager.load_overview_map(points)
    overview_map_details[0].save("overview_nomarkers.png")
    img2 = Image.open("overview_nomarkers.png")

    excelMapImage = openpyxl.drawing.image.Image(img2)
    sht.add_image(excelMapImage,"G2")
    sht = wb.get_sheet_by_name("Data")
    sht.cell(row=2,column=14).value = ",".join(jobDetails["times"])
    sht.cell(row=3, column=14).value = jobDetails["period"]
    for index,cl in enumerate(jobDetails["classes"]):
        sht.cell(row=index+2, column=50).value = cl
    row = 2

    fnt = ImageFont.truetype("arial", size=18)

    count = 0
    for key,item in sorted(sites.items()):

        sht = wb.get_sheet_by_name("Data")
        siteImg = Image.open(key + ".png").convert('RGB')
        siteImg = siteImg.resize((800, 800), Image.ANTIALIAS)
        drawimage = ImageDraw.Draw(siteImg)
        if len(item["Arms"]) !=0:
            col = 4
            sht.cell(row=row,column=1).value = key
            sht.cell(row=row , column=2).value = item["coords"][0]
            sht.cell(row=row , column=3).value = item["coords"][1]
            for label,arm in sorted(item["Arms"].items()):

                x,y = arm["coords"]
                outline = 3  # line thickness
                #draw.ellipse((x1 - outline, y1 - outline, x2 + outline, y2 + outline), fill=outline_color)
                #draw.ellipse((x1, y1, x2, y2), fill=background_color)
                drawimage.ellipse([x - 15- outline, y - 15- outline, x + 15+ outline, y + 15+ outline], outline="Black",fill = "black")
                drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white",fill = "white")
                drawimage.text((x-6, y-7), text=label,font=fnt, fill="black")
                angle = arm["orientation"] + 180
                if angle > 360:
                    angle-=360
                sht.cell(row=row, column=col).value = label + "," + str(angle) + "," + arm["road"] + "," + str(x*excelMapWidth/800) + "," + str(y*excelMapHeight/800)    ### convert coords to fit a 500x500 map
                #sht.cell(row=row , column=col+1).value = angle
                #sht.cell(row=row, column=col + 2).value = arm["road"]
                print("outputting", label + "," + str(angle) + "," + arm["road"] + "," + str(x*excelMapWidth/800) + "," + str(y*excelMapHeight/800))
                col+=1
            row+=1
        folder = os.path.dirname(os.path.abspath(__file__))
        #folder = os.path.join(folder, "Runs\\")
        siteImg.save(folder + "/" + key + " with arm labels" + ".png")
        img2 = Image.open(key + " with arm labels.png")
        img2 = img2.resize((500, 500), Image.ANTIALIAS)
        excelMapImage = openpyxl.drawing.image.Image(img2)
        sht = wb.get_sheet_by_name("Maps")
        sht.add_image(excelMapImage, "B" + str(2 + count))
        count+=1
    print("saving")
    wb.save(filename="TemplateResult.xlsm")

def get_all_site_coords():
    global siteDetails
    return siteDetails[["Lat", "Lon"]].values.tolist()

def get_all_site_details():
    global siteDetails
    return siteDetails[["Site Name","Lat","Lon"]].values.tolist()

def download_all_individual_site_maps():
    for site in get_all_site_details():
        map = mapmanager.load_high_def_map_with_labels(site[1],site[2],individual_site_zoom_value)
        #map = mapmanager.load_high_def_map_without_labels(site[1], site[2], individual_site_zoom_value)
        map.save(str(site[0]) + ".png")

def download_overview_map():
    global overview_map_details
    points = get_all_site_coords()
    overview_map_details = mapmanager.load_overview_map_without_street_labels(points)
    overview_map_details[0].save("overview.png")
    print("centre of overview map is",overview_map_details[1],"zoom is",overview_map_details[2])

centre = (55.91009503466296, -3.501137500000034)

#load_project()
#export_to_excel()
#print(get_next_site("Site 1"))
#get_all_individual_site_maps()
#get_overview_map()

#register_arm_details("Site 1","A",320,320)