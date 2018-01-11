from tkinter import filedialog
from PIL import Image,ImageDraw,ImageTk,ImageFont
import mapmanager
import pandas as pd
from tkinter import filedialog,messagebox
import openpyxl
import os
import xlwt
from openpyxl.chart import LineChart,PieChart,BarChart
import math
import datetime
import pickle
import copy

outline = 3 ## witdth of line to draw circles on the map
siteDetails = None
baseClasses = [["Car",1],["LGV",1],["OGV1",1.5],["OGV2",2.3],["PSV",2],["MC",0.4],["PC",0.2]]
projectClasses = [["Car",1],["LGV",1],["OGV1",1.5],["OGV2",2.3],["PSV",2],["MC",0.4],["PC",0.2]]
excelMapWidth = 576.5295 ### the size of the map in the excel template sheet
excelMapHeight = 576.5295
sites = {}
groups = {}
groupCount = 1
current_label = 64
individual_site_zoom_value = 18
overview_map_details = []
jobNumber = ""
jobName = ""
surveyDate= ""
timePeriods  = ""
project = None



####################################################################################################
###
### Deal with classes
###
####################################################################################################

def get_classes(surveyIndex):
    surveyType = ["J","Q","P"][surveyIndex]
    return project["survey details"][surveyType]["classes"]

def delete_class(index,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["classes"].pop(index)
    return len(project["survey details"][surveyType]["classes"])

def add_class(vals,surveyIndex):
    if project is None:
        return 0
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["classes"].append(vals)
    return len(project["survey details"][surveyType]["classes"])

def edit_class(vals,index,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["classes"][index] = vals
    return len(project["survey details"][surveyType]["classes"])

def move_class_up(index,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    if index == 0:
        return index
    temp = project["survey details"][surveyType]["classes"][index]
    project["survey details"][surveyType]["classes"][index] = project["survey details"][surveyType]["classes"][index-1]
    project["survey details"][surveyType]["classes"][index - 1] = temp
    return index -1

def move_class_down(index,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    if index == len(project["survey details"][surveyType]["classes"])-1:
        return index
    temp = project["survey details"][surveyType]["classes"][index]
    project["survey details"][surveyType]["classes"][index] = project["survey details"][surveyType]["classes"][index+1]
    project["survey details"][surveyType]["classes"][index + 1] = temp
    return index + 1

####################################################################################################
###
### Deal with groups
###
####################################################################################################

def add_group():
    global project
    if len(project["groups"]) == 1:
        groupName = "Group 1"
    else:
        groupList = sorted([int(key.split(" ")[1]) for key,_ in project["groups"].items() if key != "ALL"])
        groupName = "Group " + str(groupList[-1] + 1)
    project["groups"][groupName] = {}
    project["groups"][groupName]["siteList"] = []
    project["groups"][groupName]["coords"] = []
    project["groups"][groupName]["image"] = None
    return groupName

def delete_group(groupName):
    global project
    del project["groups"][groupName]
    print("ahahah",project["groups"].items())
    print(sorted(project["groups"].keys(), key=lambda x:0 if x == "ALL" else int(x.replace("Group ","").strip())))
    for index,key in enumerate(sorted(project["groups"].keys(), key=lambda k:0 if k == "ALL" else int(k.replace("Group ","").strip()))):
        print(index,key)
        if key != "ALL":
            project["groups"]["Group " + str(index)] = project["groups"].pop(key)
    print(sorted(project["groups"].keys(), key=lambda x: 0 if x == "ALL" else int(x.replace("Group ", "").strip())))


def add_site_to_group(groupName,site):
    global project
    project["groups"][groupName]["siteList"].append(site)

def delete_site_from_group(groupName,site):
    global project
    project["groups"][groupName]["siteList"].remove(site)

def get_groups():
    return project["groups"]


####################################################################################################
###
###  Deal with Project
###
####################################################################################################

def change_period(val,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["period"] = val
    print("survey details are",project["survey details"])

def change_survey_date(d,surveyIndex):
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["date"] = d

def change_times(t,surveyIndex):
    print("received",t)
    surveyType = ["J", "Q", "P"][surveyIndex]
    project["survey details"][surveyType]["times"] = t
    print("times for ",surveyType,"are",project["survey details"][surveyType]["times"])

def get_survey_details(surveyType):
    return [project["survey details"][surveyType]["date"],project["survey details"][surveyType]["times"],project["survey details"][surveyType]["period"]]

####################################################################################################
###
###  Deal with sites
###
####################################################################################################

def get_image_type(site,surveyType):
    return ["roadmap","satellite"].index(site["surveys"][surveyType]["imageType"])

def get_site_by_order(index):
    for _,site in project["sites"].items():
        if site["order"] == index:
            return site
    return None

def change_site_image_type(val,site,surveyType):
    if val ==0:
        val  = "roadmap"
    else:
        val = "satellite"
    if site["surveys"][surveyType]["imageType"] != val:
        x,y = site["surveys"][surveyType]["latlon"]
        map = mapmanager.load_high_def_map_with_labels(x, y, site["surveys"][surveyType]["zoom"],imageType=val)
        map.save(str(site["Site Name"]) + ".png")
        site["surveys"][surveyType]["imageType"] = val
        site["surveys"][surveyType]["image"] = map.resize((800, 800), Image.ANTIALIAS)

def change_site_zoom(site,value,surveyType):
    if value == "+":
        site["surveys"][surveyType]["zoom"] += 1
    else:
        site["surveys"][surveyType]["zoom"]-=1
    map = mapmanager.load_high_def_map_with_labels(site["surveys"][surveyType]["latlon"][0], site["surveys"][surveyType]["latlon"][1], site["surveys"][surveyType]["zoom"],imageType=site["surveys"][surveyType]["imageType"])
    map.save(str(site["Site Name"]) + ".png")
    site["surveys"][surveyType]["image"] = map.resize((800, 800), Image.ANTIALIAS)
    site["surveys"][surveyType]["Arms"] = {}

def change_site_centre_point(site,x,y,surveyType):
    ###
    ### x,y are the deltas that the map has changed by
    ###
    print("changing site centre point,movement was",x,y)
    currentCentre = site["surveys"][surveyType]["latlon"]
    zoom = site["surveys"][surveyType]["zoom"]
    newCentre = mapmanager.get_lat_lon_from_x_y(currentCentre,(640-(x*640/800)),(640-(y*640/800)),zoom,size=1280)
    print("new centre is ",newCentre)

    site["surveys"][surveyType]["latlon"] = newCentre
    map = mapmanager.load_high_def_map_with_labels(site["surveys"][surveyType]["latlon"][0],
                                                   site["surveys"][surveyType]["latlon"][1],
                                                   site["surveys"][surveyType]["zoom"],
                                                   imageType=site["surveys"][surveyType]["imageType"])
    site["surveys"][surveyType]["image"] = map.resize((800, 800), Image.ANTIALIAS)
    site["surveys"][surveyType]["Arms"] = {}
    if surveyType == "J":
        download_overview_map()


def change_site_group(site,group):
    sites[site]["group"] = group




####################################################################################################
###
###  Deal with Arms
###
####################################################################################################



def get_overview_map():
    try:
        print("project is",project["survey details"])
        img = project["survey details"]["J"]["overview image"]
        #img = img.resize((800, 800), Image.ANTIALIAS)
        coordsList = get_all_site_details()
        #coordsList = [(site["Site Name"],mapmanager.get_coords(project["survey details"]["J"]["overview centre"],site["surveys"]["J"]["latlon"],project["survey details"]["J"]["overview zoom"],size=1280)) for _,site in project["sites"].items()]
        print("Coord list is",coordsList)
        return [img,coordsList]
    except Exception as e:
        print("error",e)
        return [None,[]]

def get_nearest_site_on_overview_map(x,y):
    pass

def get_project_details():
    return [project["jobName"],project["jobNumber"]]

def format_date(d):
    surveyDate = None
    if not type(d)== datetime.datetime:
        try:
            surveyDate = datetime.datetime.strptime(d,"%d/%m/%Y")
        except Exception as e:
            try:
                surveyDate = datetime.datetime.strptime(d, "%d/%m/%y")
            except Exception as e:
                pass
        return surveyDate
    else:
        return d

def import_site_details_from_excel():
    project = None
    global siteDetails,jobName,jobNumber,surveyDate,timePeriods,projectClasses, project
    f = filedialog.askopenfilename(initialdir=dir)
    if f == "":
        return
    siteDetails = pd.read_excel(f,parse_cols=[0,1,2,3],index_col=None)
    siteDetails["Site Name"] = siteDetails["Site Name"].apply(str)
    siteDetails["Site Name"] = siteDetails["Site Name"].apply(str.title)
    mask = ~siteDetails["Site Name"].str.contains("Site")
    siteDetails.loc[mask, "Site Name"] = siteDetails[mask]["Site Name"].apply(lambda x: "Site " + x)
    mask = ~siteDetails["Site Name"].str.contains("Site ")
    siteDetails.loc[mask, "Site Name"] = siteDetails[mask]["Site Name"].apply(lambda x: "Site " + x.split("Site")[1])
    siteDetails.dropna(axis=0, inplace=True)
    siteDetails[siteDetails["Type"].isnull()] = "J"
    print(siteDetails)

    wb = openpyxl.load_workbook(f)
    project = {}
    project["jobNumber"] = wb.worksheets[0]["F4"].value
    project["jobName"] = wb.worksheets[0]["F6"].value
    project["survey details"] = {}
    surveyTypes = ["J","P","Q"]
    for index,survey in enumerate(surveyTypes):
        project["survey details"][survey] = {}
        project["survey details"][survey]["date"] = format_date(wb.worksheets[0].cell(row=8+index, column=6).value)
        col = 6
        project["survey details"][survey]["classes"] = []
        while not wb.worksheets[0].cell(row=12+(2*index), column=col).value is None:
            try:
                pcu = int(wb.worksheets[0].cell(row=13 + (2*index),column=col).value)
            except Exception as e:
                pcu = 1
                project["survey details"][survey]["classes"].append([wb.worksheets[0].cell(row=12+(2*index),column=col).value,pcu])
            col+=1

        project["survey details"][survey]["times"] = ""
        project["survey details"][survey]["period"] = "15"
        col = 6
        timeList = []
        while not wb.worksheets[0].cell(row=19+index,column=col).value is None:
            print(wb.worksheets[0].cell(row=19+index,column=col).value)
            try:
                t = wb.worksheets[0].cell(row=19+index,column=col).value
                timeList.append(t.strftime("%H:%M"))
                print("timelist is",timeList)
            except Exception as e:
                messagebox.showinfo(message="there was a problem with one or more times in the project file\n Please check")
                project = None
                return
            col+=1
        if len(timeList) != 0:
            if len(timeList)%2!=0:
                timeList = timeList[:-1]
            project["survey details"][survey]["times"] = ",".join([str(timeList[i]) + "-" + str(timeList[i+1]) for i in range(0,len(timeList),2)])
    ###
    ### fill in any blank survey dates and times
    ###
    #t = [s["times"] for _,s in project["surveys"].items() if not s["times"] is ""]
    #d = [s["date"] for _,s in project["surveys"].items() if not s["date"] is None]
    #print(t,d)
    sites = {}
    project["sites"] = {}
    for index, site in siteDetails.iterrows():
        surveyTypes = site[3].split("/")
        project["sites"][site[0]] = {}
        project["sites"][site[0]]["order"] = index
        project["sites"][site[0]]["Site Name"] = site[0]
        project["sites"][site[0]]["surveys"] ={}
        for survey in surveyTypes:
            project["sites"][site[0]]["surveys"][survey] = {}
            project["sites"][site[0]]["surveys"][survey]["Arms"] = {}
            project["sites"][site[0]]["surveys"][survey]["zoom"] = individual_site_zoom_value
            if survey.upper() == "J":
                project["sites"][site[0]]["surveys"][survey]["zoom"]+=1
            if survey.upper() == "Q":
                project["sites"][site[0]]["surveys"][survey]["imageType"] = "satellite"
            else:
                project["sites"][site[0]]["surveys"][survey]["imageType"] = "roadmap"
            project["sites"][site[0]]["surveys"][survey]["image"] = None
            project["sites"][site[0]]["surveys"][survey]["latlon"] = (site[1], site[2])
    print("project is",project)

def load_project():
    global siteDetails, groups,sites,projectClasses,project
    import_site_details_from_excel()
    if siteDetails is None:
        return None
    points = get_all_site_coords()
    if points != []:
        download_overview_map()
        project["groups"] = {}
        project["groups"]["ALL"] = {}
        project["groups"]["ALL"]["siteList"] = []
        project["groups"]["ALL"]["coords"] = []
        for _,site in project["sites"].items():
            if "J" in site["surveys"]:
                site["coords"] = mapmanager.get_coords(overview_map_details[1],site["surveys"]["J"]["latlon"],overview_map_details[2],size=1280)
                project["groups"]["ALL"]["siteList"].append(site["Site Name"])
                project["groups"]["ALL"]["coords"].append(site["coords"])
        project["groups"]["ALL"]["image"] = None
    download_all_individual_site_maps()

    with open("test" + ".pkl", "wb") as f:
        pickle.dump(project, f)
    with open("test" + ".pkl", "rb") as f:
        project = pickle.load(f)
    print("after loading, project is",project)
    print(get_site_by_order(0))
    return get_site_by_order(0)

def save_project_to_pickle(file):
    print("saving project")
    for key,item in project["sites"].items():
        print(item)
    with open(file + ".pkl","wb") as f:
        pickle.dump(project,f)
    return
    global sites,groups,project
    file = file.replace(".pkl","")
    sitesToSave = {}
    for siteName,site in project["sites"].items():
        print(siteName,site)
        newSite  = {}
        sitesToSave[siteName] = newSite
        for key,value in site.items():
            print(key,value)
            if key == "Arms":
                newSite["Arms"] = {}
                for armLabel,arm in value.items():
                    print(armLabel,arm)
                    newSite["Arms"][armLabel] = {}
                    for k,v in arm.items():
                        if k == "label":
                            pass
                        else:
                            newSite["Arms"][armLabel][k] = v

                pass
            else:
                newSite[key] = value
    print("sites to save is",sitesToSave)
    print("sites are",sites)
    projectToSave = {"sites":sitesToSave,"groups":groups,"details":[project["jobName"],project["jobNumber"]],"classes":projectClasses}
    with open(file + ".pkl","wb") as f:
        pickle.dump(project,f)

def load_project_from_pickle(file):
    global sites,groups,jobName, jobNumber, surveyDate, timePeriods,groupCount,projectClasses,project
    with open(file, "rb") as f:
        project = pickle.load(f)
    print("[project is",project)
    for siteName,site in project["sites"].items():
        for surveyType,survey in site["surveys"].items():
            for label,arm in survey["Arms"].items():
                arm["entry widget"] = None

    return get_site_by_order(0)

def load_previous_site(site):
    ###
    ### user has pressed the left arrow to move to the previous site
    ###
    for _,survey in site["surveys"].items():
        for _,arm in survey["Arms"].items():
            arm["entry widget"] = None
    index = site["order"] - 1
    result = get_site_by_order(index)
    if result is None:
        return site
    return result

def load_next_site(site):
    ###
    ### user has pressed the right arrow to move to the next site
    ###
    index = site["order"] + 1
    for _, survey in site["surveys"].items():
        for _, arm in survey["Arms"].items():
            print("arm is",arm)
            arm["entry widget"] = None
    result = get_site_by_order(index)
    if result is None:
        return site
    return result

def export_to_excel(index):
    if index == 0:
        print("exporting JTC")
        export_JTC_to_excel()
    if index == 1:
        export_Q_to_excel()

def export_JTC_to_excel():
    global groups
    file = filedialog.asksaveasfilename()
    if file == "" or file is None:
        return
    wb = openpyxl.load_workbook("JTC Template.xlsm",keep_vba=True)

    sht = wb.get_sheet_by_name("Maps")

    img = Image.open("Tracsis logo.png")
    imgSmall = img #.resize((247, 78), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA1")

    img = Image.open("Tracsis Icon.png")
    imgSmall = img #.resize((25, 25), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA2")

    img = Image.open("Tracsis-banner.png")
    imgSmall = img  # .resize((25, 25), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA3")

    sht = wb.get_sheet_by_name("Dashboard")

    c1= BarChart()
    c1.title = "Class Ratios"
    sht.add_chart(c1,"AB5")

    c1 = BarChart()
    c1.title = "Total Volumes"
    sht.add_chart(c1, "M25")

    sht = wb.get_sheet_by_name("Data")
    sht.cell(row=2, column=14).value = project["survey details"]["J"]["times"]
    sht.cell(row=3, column=14).value = project["survey details"]["J"]["period"]
    sht.cell(row=4, column=14).value = project["jobNumber"]
    sht.cell(row=5, column=14).value = project["jobName"]
    sht.cell(row=6, column=14).value = project["survey details"]["J"]["date"]
    for index, cl in enumerate(project["survey details"]["J"]["classes"]):
        sht.cell(row=index + 2, column=50).value = cl[0]
        sht.cell(row=index + 2, column=52).value = cl[1]
    row = 2


    fnt = ImageFont.truetype("arial", size=18)

    count = 0
    for key,site in sorted(project["sites"].items(),key=lambda x:x[1]["order"]): ### sorted(sites.items(),key=lambda x:int(x[0].replace("Site ","").strip())):
        print("checking",site)
        if "J" in site["surveys"]:
            ###
            ### check and adjust road names if any are duplicated within a site
            ###
            print("here")
            dets = [[k, i["orientation"] + 180, i["road name"]] for k, i in site["surveys"]["J"]["Arms"].items()]
            mylist = [item["road name"] for key, item in site["surveys"]["J"]["Arms"].items()]
            print([(item["road name"],key) for key, item in site["surveys"]["J"]["Arms"].items()])
            print("list of roads",mylist)
            for road in mylist:
                matches = [x for x in dets if x[2] == road]
                if len(matches) > 1:
                    print("matches are",matches)
                    for m in matches:

                        road = m[2] + "(" + road_orientation(m[1]) + ")"
                        site["surveys"]["J"]["Arms"][m[0]]["road"] = road

            sht = wb.get_sheet_by_name("Maps")
            sht.cell(row=count+2,column=1).value = key
            sht.cell(row=count+2,column=13).value = "No relevant observations"
            sht = wb.get_sheet_by_name("Data")
            siteImg = site["surveys"]["J"]["image"].convert('RGB')
            siteImg = siteImg.resize((800, 800), Image.ANTIALIAS)
            drawimage = ImageDraw.Draw(siteImg)
            if len(site["surveys"]["J"]["Arms"]) !=0:
                col = 4
                sht.cell(row=row,column=1).value = key

                sht.cell(row=row , column=2).value = str(site["coords"][0]) + "," + str(site["coords"][1])
                sht.cell(row=row , column=3).value = str(site["surveys"]["J"]["latlon"][0]) + "," + str(site["surveys"]["J"]["latlon"][1])
                for label,arm in sorted(site["surveys"]["J"]["Arms"].items()):
                    angle = arm["orientation"] + 180
                    if angle > 360:
                        angle-=360
                    x,y = [c-5 for c in arm["coords"]]
                    outline = 3  # line thickness

                    drawimage.ellipse([x - 15- outline, y - 15- outline, x + 15+ outline, y + 15+ outline], outline="Black",fill = "black")
                    drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white",fill = "white")
                    drawimage.text((x-6, y-7), text=label,font=fnt, fill="black")
                    angle += 180
                    if angle >= 360:
                        angle-=360
                    sht.cell(row=row, column=col).value = label + "," + str(angle) + "," + arm["road name"] + "," + str((x-5)*excelMapWidth/800) + "," + str((y-5)*excelMapHeight/800)    ### convert coords to fit a 500x500 map
                    #sht.cell(row=row , column=col+1).value = angle
                    #sht.cell(row=row, column=col + 2).value = arm["road"]
                    print("outputting", label + "," + str(angle) + "," + arm["road name"] + "," + str(x*excelMapWidth/800) + "," + str(y*excelMapHeight/800))
                    col+=1
                row+=1
                img2 = siteImg.resize((800, 800), Image.ANTIALIAS)
                excelMapImage = openpyxl.drawing.image.Image(img2)
                sht = wb.get_sheet_by_name("Maps")
                sht.add_image(excelMapImage, "B" + str(2 + count))
                count+=1

    count = 0
    ###
    ### remove any groups that have no sites attached
    ###
    project["groups"] = {k:v for k,v in project["groups"].items() if len(v["siteList"]) != 0}
    for index,key in enumerate(sorted(project["groups"].keys(), key=lambda k:0 if k == "ALL" else int(k.replace("Group ","").strip()))):
        print(index,key)
        if key != "ALL":
            project["groups"]["Group " + str(index)] = project["groups"].pop(key)
    ###
    ### output groups
    ###

    for key,group in sorted(project["groups"].items(), key=lambda x:0 if x[0] == "ALL" else int(x[0].replace("Group ","").strip())):
        print("key,value",key,group)
        if key != "ALL":
            download_group_map(key)
            img2 = project["groups"][key]["image"]
            excelMapImage = openpyxl.drawing.image.Image(img2)
            sht = wb.get_sheet_by_name("Maps")
            sht.add_image(excelMapImage, "G" + str(2 + count))
            sht.cell(row=count + 2, column=6).value = key

            sht = wb.get_sheet_by_name("Data")
            sht.cell(row=count + 100, column= 1).value = key
            for i,site in enumerate(group["coords"]):
                armData = []
                siteName = site[0]
                siteLatLon = project["sites"][siteName]["surveys"]["J"]["latlon"]
                for armLabel,arm in sorted(project["sites"][siteName]["surveys"]["J"]["Arms"].items()):
                    armLatLon = arm["latlon"]
                    pixelDistance = mapmanager.pixelDistance(siteLatLon[0],siteLatLon[1],armLatLon[0],armLatLon[1],group["zoom"])
                    armData.append(armLabel)
                    armData.append(pixelDistance[0])
                    armData.append((pixelDistance[1]))
                sht.cell(row=count + 100, column=i+2).value = ",".join(map(str,site)) + "," + ",".join(map(str,armData))
            count+=1



        ###
        ### create the overview map showing the sites in the group in red
        ### and the other sites in black
        ###

        #img2 = Image.open("overview.png").convert('RGB')
        #drawimage = ImageDraw.Draw(img2)
        #fnt = ImageFont.truetype("arial", size=18)
        #sitesInGroup = project["groups"]["siteList"]
        #if len(sitesInGroup) > 0:
            #print("sitesingroup",sitesInGroup)
            #siteList = [(site[0], site[1], site[2]) for site in get_all_site_details()]
            #for site in siteList:
                #if site[0] in sitesInGroup:
                    #colour = "red"
                #else:
                    #colour  = "black"
                #x, y = mapmanager.get_coords(overview_map_details[1], (site[1], site[2]), overview_map_details[2], size=1280)
                #drawimage.ellipse([x - 15 - outline, y - 15 - outline, x + 15 + outline, y + 15 + outline], outline=colour,fill=colour)
                #drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white", fill="white")
                #drawimage.text((x - 8, y - 9), text=site[0].split(" ")[1], font=fnt, fill="black")
            #img2.save(key  + "_sites.png")
            #img2 = Image.open(key  + "_sites.png")
            #excelMapImage = openpyxl.drawing.image.Image(img2)
            #sht = wb.get_sheet_by_name("Maps")
            #sht.add_image(excelMapImage, "H" + str(2 + count))
            #count += 1

    print("saving")
    try:

        wb.save(filename=file + " JTC .xlsm")
    except PermissionError as e:
        messagebox.showinfo(message="file is already open, please close file and retry exporting")
        return

def export_Q_to_excel():
    global groups
    file = filedialog.asksaveasfilename()
    if file == "" or file is None:
        return
    wb = openpyxl.load_workbook("Queue Template.xlsm",keep_vba=True)

    sht = wb.get_sheet_by_name("Maps")

    img = Image.open("Tracsis logo.png")
    imgSmall = img #.resize((247, 78), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA1")



    img = Image.open("Tracsis Icon.png")
    imgSmall = img #.resize((25, 25), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA2")

    img = Image.open("Tracsis-banner.png")
    imgSmall = img  # .resize((25, 25), Image.ANTIALIAS)
    excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
    sht.add_image(excelImageSmall, "AA3")

    sht = wb.get_sheet_by_name("Dashboard")

    #c1= BarChart()
    #c1.title = "Class Ratios"
    #sht.add_chart(c1,"AB5")

    c1 = LineChart()
    c1.title = "Queue Lengths"
    sht.add_chart(c1, "M25")



    sht = wb.get_sheet_by_name("Data")
    sht.cell(row=2,column=14).value = project["survey details"]["Q"]["times"]
    sht.cell(row=3, column=14).value = project["survey details"]["Q"]["period"]
    sht.cell(row=4, column=14).value = project["jobNumber"]
    sht.cell(row=5, column=14).value = project["jobName"]
    sht.cell(row=6,column=14).value = project["survey details"]["Q"]["date"]
    for index,cl in enumerate(project["survey details"]["Q"]["classes"]):
        sht.cell(row=index+2, column=50).value = cl[0]
        sht.cell(row=index + 2, column=52).value = cl[1]
    row = 2

    fnt = ImageFont.truetype("arial", size=18)

    count = 0
    for key,site in sorted(project["sites"].items(),key=lambda x:x[1]["order"]): ### sorted(sites.items(),key=lambda x:int(x[0].replace("Site ","").strip())):

        if "Q" in site["surveys"]:
            print("here",key,site)
            dets = [[k, i["orientation"] + 180, i["road name"]] for k, i in site["surveys"]["Q"]["Arms"].items()]
            mylist = [item["road name"] for key, item in site["surveys"]["Q"]["Arms"].items()]
            print([(item["road name"],key) for key, item in site["surveys"]["Q"]["Arms"].items()])
            print("list of roads",mylist)
            for road in mylist:
                matches = [x for x in dets if x[2] == road]
                if len(matches) > 1:
                    print("matches are",matches)
                    for m in matches:
                        road = m[2] + "(" + road_orientation(m[1]) + ")"
                        site["surveys"]["Q"]["Arms"][m[0]]["road name"] = road

            sht = wb.get_sheet_by_name("Maps")
            sht.cell(row=count+2,column=1).value = key
            sht.cell(row=count+2,column=13).value = "No relevant observations"
            sht = wb.get_sheet_by_name("Data")
            siteImg = site["surveys"]["Q"]["image"].convert('RGB')
            print("size is",siteImg.size)
            #siteImg = siteImg.resize((800, 800), Image.ANTIALIAS)
            drawimage = ImageDraw.Draw(siteImg)
            if len(site["surveys"]["Q"]["Arms"]) !=0:
                col = 4
                sht.cell(row=row,column=1).value = key
                sht.cell(row=row , column=2).value = str(site["surveys"]["Q"]["zoom"])
                sht.cell(row=row , column=3).value = str(site["surveys"]["Q"]["latlon"][0]) + "," + str(site["surveys"]["Q"]["latlon"][1])
                for label,arm in sorted(site["surveys"]["Q"]["Arms"].items()):
                    angle = arm["last line orientation"]
                    coords = [(c-5)*excelMapWidth/800 for c in arm["line vertices"]]
                    coords = ",".join(list(map(str,coords)))
                    x,y = arm["line vertices"][:2]
                    outline = 3  # line thickness

                    #drawimage.ellipse([x - 15- outline, y - 15- outline, x + 15+ outline, y + 15+ outline], outline="white")
                    #drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white",fill = "white")
                    drawimage.text((x-6, y-7), text=label,font=fnt, fill="red")
                    angle += 180
                    if angle >= 360:
                        angle-=360
                    print(label,"coords are",coords)
                    sht.cell(row=row, column=col).value = label + "," + str(arm["lanes"]) + "," + arm["road name"] + "," + str(angle) + "," + coords    ### convert coords to fit a 500x500 map
                    #sht.cell(row=row , column=col+1).value = angle
                    #sht.cell(row=row, column=col + 2).value = arm["road"]
                    print("outputting", label + "," + str(arm["lanes"]) + "," + arm["road name"] + "," + coords)
                    col+=1
                row+=1

                img2 = siteImg.resize((800, 800), Image.ANTIALIAS)
                excelMapImage = openpyxl.drawing.image.Image(img2)
                sht = wb.get_sheet_by_name("Maps")
                sht.add_image(excelMapImage, "B" + str(2 + count))
                count+=1

    count = 0
    print("saving")
    try:

        wb.save(filename=file + " Queues .xlsm")
    except PermissionError as e:
        messagebox.showinfo(message="file is already open, please close file and retry exporting")
        return

def get_all_site_coords():
    coords = []
    for _,site in project["sites"].items():
        if "J" in site["surveys"]:
            if not site["surveys"]["J"]["latlon"] in coords:
                coords.append(site["surveys"]["J"]["latlon"])
    return coords

def get_all_site_details():
    coords = []
    for _, site in project["sites"].items():
        if "J" in site["surveys"]:
            coords.append([site["Site Name"], mapmanager.get_coords(project["survey details"]["J"]["overview centre"],site["surveys"]["J"]["latlon"],project["survey details"]["J"]["overview zoom"],size=1280)])
    return coords

def download_all_individual_site_maps():
    for siteName,site in project["sites"].items():
        print("site is",site)
        for surveyType,survey in site["surveys"].items():
            print("survety is",survey)
            x,y = survey["latlon"]
            map = mapmanager.load_high_def_map_with_labels(x,y,survey["zoom"],imageType=survey["imageType"])
            survey["image"] = map.resize((800, 800), Image.ANTIALIAS)
            map.save(siteName + ".png")

def download_overview_map():
    global overview_map_details,project
    points = get_all_site_coords()
    print("in overview map points are",points)
    if points == []:
        return
    overview_map_details = mapmanager.load_overview_map_without_street_labels(points)
    overview_map_details[0].save("overview.png")
    #overview_map_details[0].show()
    project["survey details"]["J"]["overview centre"] = overview_map_details[1]
    project["survey details"]["J"]["overview zoom"] = overview_map_details[2]
    project["survey details"]["J"]["overview image"] = overview_map_details[0]
    print("centre of overview map is",overview_map_details[1],"zoom is",overview_map_details[2])

def download_group_map(groupName):
    if not project["groups"][groupName]["image"] is None:
        return project["groups"][groupName]["image"]
    siteList = project["groups"][groupName]["siteList"]
    if len(siteList)== 0:
        return project["survey details"]["J"]["overview image"]
    project["groups"][groupName]["coords"] = []
    print("site list is",siteList)
    coordsList = [site["surveys"]["J"]["latlon"] for _,site in project["sites"].items() if site["Site Name"] in siteList] ### coordsList is the list of lat/lons for each site in the group
    print("coordslist is",coordsList)
    map_details = mapmanager.load_overview_map_without_street_labels(coordsList)
    project["groups"][groupName]["zoom"] = map_details[2]
    img2 = map_details[0].convert("RGB")
    drawimage = ImageDraw.Draw(img2)
    fnt = ImageFont.truetype("arial", size=18)
    for site in siteList:
        x,y = mapmanager.get_coords(map_details[1],project["sites"][site]["surveys"]["J"]["latlon"],map_details[2],size=1280)
        project["groups"][groupName]["coords"].append([site,x,y])
        drawimage.ellipse([x - 15- outline, y - 15- outline, x + 15+ outline, y + 15+ outline], outline="Black",fill = "black")
        drawimage.ellipse([x - 15, y - 15, x + 15, y + 15], outline="white",fill = "white")
        drawimage.text((x-8, y-9), text=site.split(" ")[1],font=fnt, fill="black")
    project["groups"][groupName]["image"] = img2
    return project["groups"][groupName]["image"]

def road_orientation(angle):
    if angle > 360:
        angle-=360
    if angle>=348.75:
        return "N"
    elif angle < 11.25:
        return "N"
    elif angle>=11.25 and angle < 33.75:
        return "NNE"
    elif angle>=33.75 and angle < 56.25:
        return "NE"
    elif angle>=56.25 and angle < 78.75:
        return "ENE"
    elif angle>=78.75 and angle < 101.75:
        return "E"
    elif angle>=101.75 and angle < 123.75:
        return "ESE"
    elif angle>=123.75 and angle < 146.25:
        return "SE"
    elif angle>=146.25 and angle < 168.75:
        return "SSE"
    elif angle>=168.75 and angle < 191.25:
        return "S"
    elif angle>=191.25 and angle < 213.75:
        return "SSW"
    elif angle>=213.75 and angle < 236.25:
        return "SW"
    elif angle>=236.25 and angle < 258.75:
        return "WSW"
    elif angle>=258.75 and angle < 281.25:
        return "W"
    elif angle>=281.25 and angle < 303.75:
        return "WNW"
    elif angle>=303.75 and angle < 326.25:
        return "NW"
    elif angle>=326.25 and angle < 348.75:
        return "NNW"


#load_project()
#save_project_to_pickle("test.pimagekl")
#load_project_from_pickle("test.pkl")
#print(project)
#export_Q_to_excel()
#save_project_to_pickle("test.pkl")


#centre = (55.91009503466296, -3.501137500000034)


#export_to_excel()
#print(get_next_site("Site 1"))
#get_all_individual_site_maps()
#get_overview_map()

#register_arm_details("Site 1","A",320,320)

#import_site_details_from_excel()
#exit()
#
#load_project()
#groups = {}
#groups["testgroup2"] = ["Site 1","Site 2","Site 3"]
#download_group_map("testgroup2")

#import_site_details_from_excel()
#print(get_project_details())

#import_site_details_from_excel()

#import_site_details_from_excel()

#print(siteDetails[["Lat","Lon"]].values.tolist())