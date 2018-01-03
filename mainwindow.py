import tkinter
from PIL import Image,ImageDraw,ImageTk
import projectmanager
import mapmanager
from tkinter import font,filedialog
import math
import numpy as np
from tkinter import ttk
import datetime
from tkinter import messagebox
import time
import mapViewer

baseClasses = [["Car","Car/Taxi",1],["LGV","Light Goods Vehicle",1],["OGV1","Other Goods Vehicle 1",1.5],["OGV2","Other Goods Vehicle 2",2.3],["PSV","Omnibus",2],["MC","Motorcycle",0.4],["PC","Pedal Cycle",0.2]]
surveyTypes = {"J":"JTC","Q":"Queue","P":"Ped"}


class MainWindow(tkinter.Tk):

    def __init__(self):
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        super(MainWindow, self).__init__()
        self.state("zoomed")
        #self.mapPanel = mapViewer.MapViewer(self,width=800,height=800,surveyType="J")
        self.siteDisplayFrame = tkinter.Frame(self,bg="white")
        self.mapPanelImage = None
        self.overviewImage = None
        self.mapPanelSize = 800 ### TODO change this to deal with different screen res
        self.armLabelRadius = 15
        self.fontsize = 10
        self.pickedUpLine = False
        self.mapScale = 1
        self.topLeftOfImage = [0,0]
        self.baseMapImage = None
        self.movingMap = False
        self.drawingArm = False
        self.allowArmDelete = True
        self.winSpawned = False
        ### set up the menu bar

        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Load New Project", command=self.load_project)
        menu.add_command(label="Load Previous Project", command=self.load_project_from_pickle)
        menu.add_command(label="Save Current Project", command=self.save_project_to_pickle)
        #menu.add_command(label="Occupancy Mismatch", command=self.get_occupancy_mismatch)
        self.menubar.add_cascade(label="File", menu=menu)
        self.config(menu=self.menubar)

        self.jobNameVar = tkinter.StringVar()
        self.jobNumVar = tkinter.StringVar()
        self.mapPanelHasFocus = False

        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        f2 = tkinter.font.Font(family='Helvetica', size=8)

        tkinter.Label(self, text="Job Details", font=f, fg=self.tracsisBlue,relief=tkinter.GROOVE,bg="light blue").grid(row=0, column=0,sticky="nsew")
        self.detailsPanel = tkinter.Frame(self,relief=tkinter.GROOVE,borderwidth=2)


        self.detailsPanel.grid(row=1, column=0, sticky="n")



        self.surveyTabs = ttk.Notebook(self.detailsPanel)
        self.surveyTabs.grid(row=2, column=0)
        for survey in ["JTC","Queue","Ped"]:
            frame = tkinter.Frame(self.detailsPanel)
            self.surveyTabs.add(frame, text=survey)

        self.build_JTC_frame()
        self.build_queue_frame()
        self.build_ped_frame()
        self.update()


        self.mapLabel = tkinter.Label(self, text="", font=f, fg=self.tracsisBlue,bg="light blue",relief=tkinter.GROOVE,borderwidth=2)
        self.mapLabel.grid(row = 0,column = 1,sticky="nsew")
        tkinter.Button(self.detailsPanel,text="Export",command=self.export_to_excel).grid(row=4,column=0,sticky="nsew",padx=3)
        frame = tkinter.Frame(self.detailsPanel)
        for col,surveyType in enumerate(["JTC","Queue","Ped"]):
            var = tkinter.IntVar()
            c = tkinter.Checkbutton(frame,text=surveyType,variable=var)
            c.grid(row=0,column=col)
            c.var = var
            #c.var.set(1)
        frame.grid(row=5,column=0)
        frame = tkinter.Frame(self)
        tkinter.Button(frame, text="<", command=lambda:self.decrement_map(None),width = 4,height = 2).grid(row=0, column=0,padx = 5,rowspan=2)
        tkinter.Button(frame, text="+", command=lambda:self.change_site_zoom("+"),width = 4,height = 2).grid(row=0, column=1,padx = 5,rowspan=2)
        tkinter.Button(frame, text="-", command=lambda:self.change_site_zoom("-"),width = 4,height = 2).grid(row=0, column=2,padx = 5,rowspan=2)
        tkinter.Button(frame, text=">", command=lambda:self.increment_map(None),width = 4,height = 2).grid(row=0, column=3,padx = 5,rowspan=2)
        self.imageTypeVar = tkinter.IntVar()
        tkinter.Radiobutton(frame,text = "regular",variable=self.imageTypeVar,value=0,command=self.change_site_image_type).grid(row=0,column=4)
        tkinter.Radiobutton(frame,text = "Satellite",variable=self.imageTypeVar,value=1,command=self.change_site_image_type).grid(row=1,column=4)
        frame.grid(row = 4,column=1)




        tkinter.Label(self, text="Overview", font=f, fg=self.tracsisBlue,bg="light blue",relief=tkinter.GROOVE,borderwidth=2).grid(row=0, column=2,sticky="nsew")
        self.overviewPanel = tkinter.Canvas(self,bg="white",relief=tkinter.RAISED,borderwidth=1)
        self.overviewPanel.bind("<Button-1>",self.overview_map_clicked)
        self.overviewPanel.grid(row = 1,column = 2)
        self.overviewPanel.bind("<MouseWheel>",self.on_mousewheel)

        self.addingArmLabel = False
        self.armLineStartingCoords = None
        self.armList = []
        self.dragInfo = {}
        self.dragInfo["Widget"] = None
        self.siteDisplayFrame.grid(row=1, column=1, rowspan=3)
        #self.mapPanel.grid(row=1, column=1, rowspan=3)
        # self.mapPanel.bind("<Double-Button-1>",self.add_arm_icon)

        self.controlDown = False

        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)

        self.activity = None
        # self.load_map_panel_map(self.currentSite["Site Name"])
        # self.load_overview_map()
        # self.currentTag = ""
        # self.dragInfo = {}
        for child in self.winfo_children():
            print(type(child))
            for c in child.winfo_children():
                print("-------------",type(c))
        return






    ##########################################################################################################################
    ###
    ### Functions to deal with the setting up the various windows for survey details etc
    ###
    ##########################################################################################################################

    def display_project_details(self):
        for child in self.winfo_children()[1:]:
            child.destroy()

    def build_JTC_frame(self):
        frame = self.surveyTabs.tabs()[0]
        frame = self.nametowidget(frame)
        print("frame is",frame,type(frame))
        #for child in frame.winfo_children():
            #child.destroy()
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        f2 = tkinter.font.Font(family='Helvetica', size=8)

        ##########################################################################################
        #
        # JTC TAB
        #
        ##########################################################################################

        tkinter.Label(frame, text=" Job Name ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=0, column=0, sticky="nsew")
        tkinter.Label(frame, text=" Job No ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=1, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        e.grid(row=0, column=1, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")
        e = tkinter.Entry(frame, font=f2)
        self.surveyDateVar = tkinter.StringVar()
        self.timesVar = tkinter.StringVar()

        tkinter.Label(frame, text="Survey Date", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=2, column=0, sticky="nsew")
        tkinter.Label(frame, text="Times", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=3, column=0, sticky="nsew")
        tkinter.Label(frame, text="Period", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=4, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.surveyDateVar, font=f2)
        e.grid(row=2, column=1, sticky="nsew")

        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")
        self.periodBox = ttk.Combobox(frame, width=16)
        self.periodBox["values"] = ["5", "15", "30", "60"]
        self.periodBox.grid(row=4, column=1, sticky="nsew")

        tkinter.Label(frame, text="Classes", font=f, fg=self.tracsisBlue, relief=tkinter.GROOVE, bg="light blue").grid(
            row=5, column=0, columnspan=2, sticky="nsew")
        cols = ["Class", "PCU"]

        for i,col in enumerate(cols):
            tkinter.Label(frame,text = col).grid(row=6,column=i,sticky="nsew")
        classesframe = tkinter.Frame(frame, bg="blue")
        classesframe.grid(row=7, column=0, columnspan=2, sticky="nsew")
        tkinter.Button(frame, text="Add", command=self.add_class, width=6).grid(row=8, column=0, sticky="nsew",columnspan=2)
        self.update()
        ####
        ### Groups
        ###


        #frame.grid_propagate(False)
        tkinter.Label(frame, text="Groups", font=f, fg=self.tracsisBlue, relief=tkinter.GROOVE, bg="light blue").grid(
            row=9, column=0, columnspan=4, sticky="nsew")
        cols = ["Group"]
        frame = tkinter.Frame(frame, bg="white")
        frame.grid(row=10, column=0, columnspan=4, sticky="nsew")
        self.groupsTree = ttk.Treeview(frame, columns=cols, height=7, show="headings", selectmode="browse")
        self.groupsTree.bind("<<TreeviewSelect>>", self.display_group)
        self.groupsTree.bind("<Double-Button-1>", self.delete_group)
        self.groupsTree.bind("<Button-3>", self.show_group_map)
        self.groupsTree.tag_configure("odd", background="white", foreground=self.tracsisBlue)
        self.groupsTree.tag_configure("even", background="azure2", foreground=self.tracsisBlue)
        for i, c in enumerate(cols):
            self.groupsTree.heading(i, text=c)  #
        self.groupsTree.column(0, width=120, anchor=tkinter.CENTER)
        self.groupsTree.grid(row=11, column=0)
        # self.groupsTree.insert("","end",values= ["Group 1"],tags =("tree", "odd") )

        self.groupList = tkinter.Listbox(frame)
        self.groupList.bind("<Double-Button-1>", self.delete_site_from_group)
        #self.groupList.bind("<Button-3>", self.show_group_map)
        self.groupList.grid(row=11, column=1, sticky="ns")
        tkinter.Button(frame, text="Add", command=self.add_group, width=6).grid(row=12, column=0, columnspan=2, sticky="nsew")
        # tkinter.Button(self.detailsPanel, text="Delete", command=self.delete_class,width = 6).grid(row=13, column=0, columnspan=2)

    def build_queue_frame(self):
        frame = self.surveyTabs.tabs()[1]
        frame = self.nametowidget(frame)
        print("frame is",frame,type(frame))
        #for child in frame.winfo_children():
            #child.destroy()
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        f2 = tkinter.font.Font(family='Helvetica', size=8)

        ##########################################################################################
        #
        # queue TAB
        #
        ##########################################################################################

        tkinter.Label(frame, text=" Job Name ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=0, column=0, sticky="nsew")
        tkinter.Label(frame, text=" Job No ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=1, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        e.grid(row=0, column=1, sticky="nsew")

        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")

        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        self.surveyDateVar = tkinter.StringVar()
        self.timesVar = tkinter.StringVar()

        tkinter.Label(frame, text="Survey Date", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=2, column=0, sticky="nsew")
        tkinter.Label(frame, text="Times", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=3, column=0, sticky="nsew")
        tkinter.Label(frame, text="Period", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=4, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.surveyDateVar, font=f2)
        e.grid(row=2, column=1, sticky="nsew")

        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")

        self.periodBox = ttk.Combobox(frame, width=16)
        self.periodBox["values"] = ["5", "15", "30", "60"]
        self.periodBox.grid(row=4, column=1, sticky="nsew")

        tkinter.Label(frame, text="Classes", font=f, fg=self.tracsisBlue, relief=tkinter.GROOVE, bg="light blue").grid(
            row=5, column=0, columnspan=2, sticky="nsew")
        cols = ["Class", "PCU"]

        for i, col in enumerate(cols):
            tkinter.Label(frame, text=col).grid(row=6, column=i, sticky="nsew")
        classesframe = tkinter.Frame(frame, bg="red")
        classesframe.grid(row=7, column=0, columnspan=2, sticky="nsew")

        tkinter.Button(frame, text="Add", command=self.add_class, width=6).grid(row=8, column=0, sticky="nsew",columnspan=2)

    def build_ped_frame(self):
        frame = self.surveyTabs.tabs()[2]
        frame = self.nametowidget(frame)
        print("frame is",frame,type(frame))
        #for child in frame.winfo_children():
            #child.destroy()
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        f2 = tkinter.font.Font(family='Helvetica', size=8)

        ##########################################################################################
        #
        # PED TAB
        #
        ##########################################################################################

        tkinter.Label(frame, text=" Job Name ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=0, column=0, sticky="nsew")
        tkinter.Label(frame, text=" Job No ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=1, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        e.grid(row=0, column=1, sticky="nsew")

        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")

        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        self.surveyDateVar = tkinter.StringVar()
        self.timesVar = tkinter.StringVar()

        tkinter.Label(frame, text="Survey Date", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=2, column=0, sticky="nsew")
        tkinter.Label(frame, text="Times", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=3, column=0, sticky="nsew")
        tkinter.Label(frame, text="Period", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=4, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.surveyDateVar, font=f2)
        e.grid(row=2, column=1, sticky="nsew")

        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")

        self.periodBox = ttk.Combobox(frame, width=16)
        self.periodBox["values"] = ["5", "15", "30", "60"]
        self.periodBox.grid(row=4, column=1, sticky="nsew")

        tkinter.Label(frame, text="Classes", font=f, fg=self.tracsisBlue, relief=tkinter.GROOVE, bg="light blue").grid(
            row=5, column=0, columnspan=2, sticky="nsew")
        cols = ["Class", "PCU"]

        for i, col in enumerate(cols):
            tkinter.Label(frame, text=col).grid(row=6, column=i, sticky="nsew")
        classesframe = tkinter.Frame(frame, bg="red")
        classesframe.grid(row=7, column=0, columnspan=2, sticky="nsew")

        tkinter.Button(frame, text="Add", command=self.add_class, width=6).grid(row=8, column=0, sticky="nsew",columnspan=2)

        frame = tkinter.Frame(frame, bg="red")

        frame.grid(row=9, column=0, columnspan=4, sticky="nsew")

    ##########################################################################################################################
    ###
    ### Functions to deal with the overview panel, defining and selecting groups,zooming and panning map
    ###
    ###########################################################################################################################

    def overview_map_clicked(self,event):
        print(event.x,event.y)
        widget = self.overviewPanel.find_closest(event.x, event.y, halo=10)[0]
        print("widget is",widget)
        tags = self.overviewPanel.gettags(widget)
        print("tags are",tags)
        print("closest site is",tags[0])
        if "site" in tags[0].lower():
            self.add_site_to_group(tags[0])
        if tags[0] == "map":
            ### user has clicked map only
            winX = event.x - self.overviewPanel.canvasx(0)
            winY = event.y - self.overviewPanel.canvasy(0)
            print("clicked at", winX, winY)
            self.dragInfo = {}
            self.dragInfo["Widget"] = widget
            self.dragInfo["xCoord"] = winX
            self.dragInfo["yCoord"] = winY
            self.dragInfo["tag"] = "map"
            self.mapClickedCoords = (winX, winY)
            self.overviewPanel.bind("<B1-Motion>", self.on_overviewpanel_movement)
            self.overviewPanel.bind("<ButtonRelease-1>", self.on_release_to_move_overview_map)

    def on_overviewpanel_movement(self,event):
        winX = event.x - self.overviewPanel.canvasx(0)
        winY = event.y - self.overviewPanel.canvasy(0)
        # print("mouse is now at", winX, winY)
        newX = winX - self.dragInfo["xCoord"]
        newY = winY - self.dragInfo["yCoord"]

        if self.dragInfo["tag"] == "map":
            for child in self.overviewPanel.find_all():
                self.overviewPanel.move(child, newX, newY)
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY

    def on_release_to_move_overview_map(self,event):
        winX = event.x - self.overviewPanel.canvasx(0)
        winY = event.y - self.overviewPanel.canvasy(0)
        print("map was moved", winX - self.mapClickedCoords[0], winY - self.mapClickedCoords[1])
        self.overviewPanel.unbind("<B1-Motion>")
        self.overviewPanel.unbind("<ButtonRelease-1>")
        if winX - self.mapClickedCoords[0] == 0 and winY - self.mapClickedCoords[1] == 0:
            return
        if self.mapScale == 1:
            self.topLeftOfImage = [0, 0]
        else:
            self.topLeftOfImage[0] -= (winX - self.mapClickedCoords[0]) * (1280 / self.mapScale) / 800
            self.topLeftOfImage[1] -= (winY - self.mapClickedCoords[1]) * (1280 / self.mapScale) / 800

        self.draw_overview_site_labels()

    def on_mousewheel(self,event):
        if self.baseMapImage is None:
            return
        iw, ih = self.baseMapImage.size
        previousCw = iw / self.mapScale
        self.mapScale += event.delta * 0.5 / 120
        if self.mapScale <= 1:
            self.mapScale = 1
            self.topLeftOfImage = [0,0]
        else:
            ###
            ### diff is the diff in x y given that we have zoomed in ( or out)
            ### ie, the width of the viewport was previousCw , in the current zoom it is now
            ### cw
            ###
            cw, ch = iw / self.mapScale, ih / self.mapScale
            diff = previousCw - cw
            self.topLeftOfImage[0] += int(diff / 2)
            self.topLeftOfImage[1] += int(diff / 2)
        self.draw_overview_site_labels()

    def mouse_over_map_panel(self,event):
        print("mouse over")
        #self.mapPanel.config(highlightbackground="red")
        #.mapPanelHasFocus = True
        #self.mapPanel.focus_set()
        self.groupList.focus_force()

    def mouse_leave_map_panel(self,event):
        print("mouse left")
        #self.mapPanel.config(highlightbackground="grey")
        self.mapPanelHasFocus = False

    def return_clicked(self,event):
        print("ohohowoeroiwj")

    def load_overview_map(self):
        circleRadius = 10
        self.overviewDetails = projectmanager.get_overview_map()
        self.baseMapImage = self.overviewDetails[0]
        print("base map is",self.baseMapImage)
        print("type of map is", type(self.baseMapImage))
        self.overviewPanel.delete(tkinter.ALL)
        self.photoImage = ImageTk.PhotoImage(self.baseMapImage)
        self.overviewPanel.create_image(5, 5, image=self.photoImage, anchor=tkinter.NW, tags=("map",))
        self.overviewPanel.configure(width=800, height=800)
        self.update_groups_tree()
        self.display_group(None)

    def draw_overview_site_labels(self):
        self.overviewPanel.delete(tkinter.ALL)

        iw, ih = self.baseMapImage.size
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        if cw > iw or ch > ih:
            cw = iw
            ch = ih
            # crop it
        print("cw,ch",cw,ch)
        ###
        ### self.topLeftOfImage is the absolute coords of the displayed part of the map
        ### eg [100,100] would mean that (0,0) on the map panel would be showing [100,100] of the base map image
        ###
        if self.topLeftOfImage[0] < 0:
            self.topLeftOfImage[0] = 0
        if self.topLeftOfImage[1] < 0:
            self.topLeftOfImage[1] = 0
        if self.topLeftOfImage[0] > 1280 - cw:
            self.topLeftOfImage[0] = 1280 - cw
        if self.topLeftOfImage[1] > 1280 - ch:
            self.topLeftOfImage[1] = 1280 - ch
        tmp = self.baseMapImage.crop((self.topLeftOfImage[0], self.topLeftOfImage[1],
                                      self.topLeftOfImage[0] + int(cw), self.topLeftOfImage[1] + int(ch)))
        # draw
        self.img = ImageTk.PhotoImage(tmp.resize((800, 800)))
        self.img_id = self.overviewPanel.create_image(0, 0, image=self.img, anchor=tkinter.NW, tags=("map",))

        circleRadius = 10
        colour = "black"
        if self.groupsTree.selection() == "":
            groupName = "ALL"
        else:
            curItem = self.groupsTree.selection()[0]
            groupName = self.groupsTree.item(curItem)["values"][0]
        groups = projectmanager.get_groups()
        grpList = groups[groupName]["siteList"]
        print("grpList is",grpList)
        for siteName,coords in self.overviewDetails[1]:
            if siteName in grpList and groupName != "ALL":
                colour = "red"
            else:
                colour = "black"

            x, y = coords
            print("before adjustment, coords are",x,y)
            ### translate point relative to viewport
            x -= self.topLeftOfImage[0]
            y -= self.topLeftOfImage[1]
            ### adjust point to fit the 800x800 display panel
            x = x * 800 / (1280 / self.mapScale)
            y = y * 800 / (1280 / self.mapScale)
            print("after adjustment, coords are", x, y)
            print("top left of image is",self.topLeftOfImage)
            self.overviewPanel.create_oval(x-circleRadius,y-circleRadius,x+circleRadius,y+circleRadius,width = 3,outline=colour,tags=[str(siteName)])
            self.overviewPanel.create_text((x,y),text=siteName.split(" ")[1],tags=[str(siteName)])
            print(self.overviewPanel.find_withtag(siteName))

    def display_group(self,event):
        if event is None:
            groupName = "ALL"
        else:
            widget = event.widget
            print("selection is",widget.selection())
            curItem = widget.selection()[0]
            groupName = widget.item(curItem)["values"][0]
            print("selected group",groupName)
        groups = projectmanager.get_groups()
        grpList = groups[groupName]["siteList"]
        self.groupList.delete(0, tkinter.END)
        for site in grpList:
            self.groupList.insert(tkinter.END,site)
        self.draw_overview_site_labels()

    def add_group(self):
        groupName = projectmanager.add_group()
        rowCount = len(self.groupsTree.get_children())
        if rowCount % 2 == 0:
            self.groupsTree.insert("", "end", values=[groupName], tags=("tree", "even"))
        else:
            self.groupsTree.insert("", "end", values=[groupName], tags=("tree", "odd"))

    def delete_group(self,event):
        print("selection is",self.groupsTree.selection())
        if self.groupsTree.selection()== "":
            return
        curItem = self.groupsTree.selection()[0]
        groupName = self.groupsTree.item(curItem)["values"][0]
        print("selected group", groupName)
        if groupName != "ALL":
            projectmanager.delete_group(groupName)
        self.update_groups_tree()

    def show_group_map(self,event):
        curItem = event.widget.identify_row(event.y)
        print("curitemis",curItem)
        print(self.groupsTree.item(curItem))
        groupName = self.groupsTree.item(curItem)["values"][0]
        print("groupname is",groupName)
        if groupName == "ALL":
            self.load_overview_map()
            return
        self.baseMapImage = projectmanager.download_group_map(groupName)
        print("type of map is",type(self.baseMapImage))
        self.photoImage = ImageTk.PhotoImage(self.baseMapImage.resize((800, 800), Image.ANTIALIAS))
        #self.baseMapImage.show()
        self.overviewPanel.delete(tkinter.ALL)
        self.overviewPanel.create_image(5, 5, image=self.photoImage, anchor=tkinter.NW,tags=("map",))



    def update_groups_tree(self):
        self.groupsTree.delete(*self.groupsTree.get_children())
        for name, grp in sorted(projectmanager.get_groups().items(),
                                key=lambda x: 0 if x[0] == "ALL" else int(x[0].replace("Group ", "").strip())):
            rowCount = len(self.groupsTree.get_children())
            print("rowcount is", rowCount)
            if rowCount % 2 == 0:
                self.groupsTree.insert("", "end", values=[name], tags=("tree", "even"))
            else:
                self.groupsTree.insert("", "end", values=[name], tags=("tree", "odd"))

    def add_site_to_group(self,site):
        if self.groupsTree.selection() == "":
            groupName = "ALL"
        else:
            curItem = self.groupsTree.selection()[0]
            groupName = self.groupsTree.item(curItem)["values"][0]
        groups = projectmanager.get_groups()
        print("groups are",groups)
        grpList = groups[groupName]["siteList"]
        if not site in grpList:
            print("adding site", site, "to group", groupName)
            projectmanager.add_site_to_group(groupName,site)
            self.groupList.insert("end",site)
            self.draw_overview_site_labels()

    def delete_site_from_group(self,event):
        sel = self.groupList.curselection()
        site  = self.groupList.get(sel)
        print("selection is", site)
        if self.groupsTree.selection() == "":
            groupName = "ALL"
        else:
            curItem = self.groupsTree.selection()[0]
            groupName = self.groupsTree.item(curItem)["values"][0]
        projectmanager.delete_site_from_group(groupName,site)
        self.draw_overview_site_labels()
        self.groupList.delete(sel)

    #######################################################################################################################
    ###
    ###  Functions to deal with adding, deleting and editing vehicle classes
    ###
    #######################################################################################################################

    def add_class(self):
        tabIndex = self.surveyTabs.index(self.surveyTabs.select())
        row = projectmanager.add_class(["Class",1],tabIndex) - 1
        self.display_classes(widgetFocus=(tabIndex,(row* 2 )))

    def delete_class(self):
        try:
            curItem = self.classesTree.selection()[0]
            print("curitem is",curItem)
            self.classesTree.delete(curItem)
            if "I0" in curItem:
                index = 0
            else:
                index = int(curItem)
            projectmanager.delete_class(index)
            self.display_classes()
        except IndexError as e:
            print("eoriehjo")

    def display_classes(self,widgetFocus=None):
        vcmd = (self.register(self.verify_class), "%d", "%s", "%S")
        for i in range(3):
            frame = self.surveyTabs.tabs()[i]
            frame = self.nametowidget(frame).winfo_children()[14]
            print("frame is",type(frame))
            for child in frame.winfo_children():
                child.destroy()
            for row,value in enumerate(projectmanager.get_classes(i)):
                e = tkinter.Entry(frame)
                e.bind("<Return>", self.verify_class)
                e.bind("<Tab>", self.verify_class)
                e.bind("<Up>", self.move_class_up)
                e.bind("<Down>", self.move_class_down)
                e.grid(row=row,column=0)
                e.insert(0,value[0])
                e = tkinter.Entry(frame)
                e.bind("<Return>",self.verify_class)
                e.bind("<Tab>",self.verify_class)
                e.bind("<Up>", self.move_class_up)
                e.bind("<Down>", self.move_class_down)
                e.grid(row=row, column=1)
                e.insert(0, value[1])
        if not widgetFocus is None:
            print("widgetfocus is",widgetFocus)
            frameIndex = widgetFocus[0]
            widgetNo = widgetFocus[1]
            frame = self.nametowidget(self.surveyTabs.tabs()[frameIndex]).winfo_children()[14]
            print("frame is",type(frame))
            frame.winfo_children()[widgetNo].focus_set()

    def move_class_up(self,event):
        tabIndex = self.surveyTabs.index(self.surveyTabs.select())
        row = event.widget.grid_info()["row"]
        index = projectmanager.move_class_up(row,tabIndex)
        self.display_classes(widgetFocus=(tabIndex,((index* 2 ) + event.widget.grid_info()["column"])))
        #event.widget.focus_set()

    def move_class_down(self,event):
        tabIndex = self.surveyTabs.index(self.surveyTabs.select())
        row = event.widget.grid_info()["row"]
        index = projectmanager.move_class_down(row, tabIndex)
        self.display_classes(widgetFocus=(tabIndex, ((index * 2) + event.widget.grid_info()["column"])))
        #event.widget.focus_set()

    def verify_class(self,event):
        parentFrame = self.nametowidget(event.widget.winfo_parent())
        tabIndex = self.surveyTabs.index(self.surveyTabs.select())
        row = event.widget.grid_info()["row"]
        col = event.widget.grid_info()["column"]
        print("edited row",row)
        text = event.widget.get()
        print("text is",text)
        print("tabindex is",tabIndex)
        vals = [parentFrame.winfo_children()[2*row].get(),parentFrame.winfo_children()[(2*row) + 1].get()]
        print("vals are",vals)
        widgetFocus = None
        if col==0 and text == "":
            num = projectmanager.delete_class(row,tabIndex)
            if num == 0:
                widgetFocus = None
            else:
                row-=1
                if row <0:
                    row = 0
                widgetFocus = (tabIndex,row*2)
        else:
            num = projectmanager.edit_class(vals,row,tabIndex)
            index = (row * 2) + 1 + col
            if index > (num*2) -1:
                index = (num*2)-1
            widgetFocus =(tabIndex,index)
        self.display_classes(widgetFocus=widgetFocus)

    ########################################################################################################################
    ###
    ### methods to deal with zooming or dragging the overview map
    ###
    #######################################################################################################################



    ########################################################################################################################
    ###
    ### methods to deal with the site aps,importing, exporting projects etc
    ###
    ########################################################################################################################

    def change_site_image_type(self):
        map = self.nametowidget(self.mapTabs.select()).winfo_children()[0]
        print("surveytype is", map.surveyType)
        projectmanager.change_site_image_type(self.imageTypeVar.get(),self.currentSite,map.surveyType)
        print("map widget is", map, type(map))
        print(map.surveyType)
        map.clear_all()
        map.display_site()

    def load_project(self):
        #self.mapPanel.delete(tkinter.ALL)
        self.overviewPanel.delete(tkinter.ALL)
        self.dragInfo["widget"] = None
        self.currentSite = projectmanager.load_project()
        self.display_project()
        if not self.currentSite is None:
            self.display_site()
        return

    def save_project_to_pickle(self):
        file = filedialog.asksaveasfilename()
        if file == "":
            return
        projectmanager.save_project_to_pickle(file)
        messagebox.showinfo(message="Save Complete")

    def load_project_from_pickle(self):
        file = filedialog.askopenfilename()
        if file == "":
            return
        result = projectmanager.load_project_from_pickle(file)
        print("result is",result)
        if result is None:
            messagebox.showinfo(message="Something went wrong when loading the file, no project loaded")
            return
        self.currentSite = result
        self.load_overview_map()
        self.display_project()
        if not self.currentSite is None:
            self.display_site()

    def display_project(self):
        print("current site is", self.currentSite)
        projectDetails = projectmanager.get_project_details()
        print("project details are",projectDetails)
        self.jobNameVar.set(projectDetails[0])
        self.jobNumVar.set(projectDetails[1])
        for i,survey in enumerate(["J"]):
            print("--" * 100)
            frame = self.surveyTabs.tabs()[i]
            frame = self.nametowidget(frame)  #.winfo_children()[14]
            children = frame.winfo_children()
            for child in children:
                print("---",type(child))
            surveyDets = projectmanager.get_survey_details(survey)
            children[8].delete(0,"end")
            children[8].insert(0,datetime.datetime.strftime(surveyDets[0],"%d/%m/%Y"))
            children[9].delete('1.0', tkinter.END)
            children[9].insert(tkinter.END,surveyDets[1])
            children[10].set(surveyDets[2])
            self.update()
            #children[16].config(width=frame.winfo_reqwidth())

        self.load_overview_map()
        self.display_classes()

    def display_site(self):
        for child in self.siteDisplayFrame.winfo_children():
            child.destroy()
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.mapTabs = ttk.Notebook(self.siteDisplayFrame)
        self.mapTabs.bind("<<NotebookTabChanged>>",self.survey_type_changed)
        self.mapTabs.grid(row=0,column=0)
        for surveyType,survey in sorted(self.currentSite["surveys"].items()):
            frame = tkinter.Frame(self.siteDisplayFrame)
            self.mapTabs.add(frame, text=surveyTypes[surveyType])
            map = mapViewer.MapViewer(frame,800,800,surveyType=surveyType)
            map.set_site(self.currentSite)
            map.grid(row=0,column=0)
            map.display_site()

    def survey_type_changed(self,event):
        nb = event.widget
        print("type of nb is",type(nb))
        print("selected tab is",nb.index(nb.select()))

    def change_site_zoom(self,value):
        map = self.nametowidget(self.mapTabs.select()).winfo_children()[0]
        print("surveytype is",map.surveyType)
        projectmanager.change_site_zoom(self.currentSite,value,map.surveyType)

        #widget = self.nametowidget(self.surveyTabs.select())
        print("map widget is", map, type(map))
        print(map.surveyType)
        map.clear_all()
        map.display_site()
        #self.display_site()

    def export_to_excel(self):
        frame = self.detailsPanel.winfo_children()[5]
        for i in range(3):
            if self.nametowidget(frame.winfo_children()[i]).var.get() == 1:
               projectmanager.export_to_excel(i)
        messagebox.showinfo(message="Export Complete")
        return

        jobDetails = {}
        try:
            surveyDate = datetime.datetime.strptime(self.surveyDateVar.get(),"%d/%m/%Y")
        except Exception as e:
            messagebox.showinfo(message = "Incorrect format for survey date,must be in format dd/mm/yyyy")
            return
        times  =self.timesTextBox.get("1.0","end-1c").strip().split(",")
        print("times is",times)
        for t in times:
            print("checking",t)
            if "-" not in t:
                messagebox.showinfo(message = "Incorrect format for times. Must be in format hh:mm-hh:mm, with multiple time periods separated by commas")
                return
            result = t.split("-")
            for r in result:
                print("------ checking",r)
                if len(r) != 5:
                    messagebox.showinfo(message="Incorrect format for time " + str(r) + ". Must be in format hh:mm")
                    return
                try:
                    d = time.strptime(r,"%H:%M")
                    print(d)
                except Exception as e:
                    messagebox.showinfo(message="Incorrect format for time " + str(r) + ". Must be in format hh:mm")
                    return
        classes = [self.classesTree.item(child,"values")[0] for child in self.classesTree.get_children() ]
        period = self.periodBox.get()
        print("currently selected period is",period)
        if period  == "":
            messagebox.showinfo(message="You must select a period")
            return
        print("classes are",classes)
        jobDetails["date"] = surveyDate
        jobDetails["times"] = times
        jobDetails["classes"] = classes
        jobDetails["period"] = period
        projectmanager.export_to_excel(jobDetails)
        self.update_groups_tree()
        messagebox.showinfo(message="Export Finished")

    def increment_map(self,event):
        print("pressed right arrow")
        self.currentSite = projectmanager.load_next_site(self.currentSite)
        self.display_site()

    def decrement_map(self,event):
        print("pressed left arrow")
        self.currentSite = projectmanager.load_previous_site(self.currentSite)
        self.display_site()

    def load_map_panel_map(self,siteName):
        self.mapPanelImage = ImageTk.PhotoImage(self.currentSite["image"])
        allwidgetsWithTag = self.mapPanel.find_withtag("map")
        print("allwidgets with tag are", allwidgetsWithTag)
        for child in allwidgetsWithTag:
            self.mapPanel.delete(child)
        self.mapPanel.create_image(5, 5, image=self.mapPanelImage, anchor=tkinter.NW,tags=("map",))
        self.mapPanel.configure(width=self.mapPanelSize,height=self.mapPanelSize)

    def rollWheel(self,event):
        if self.baseImage == None:
            return
        print("event", event.num, event.delta, event)
        if event.delta == 120:
            self.zoom += 100
        elif event.delta == -120:
            self.zoom -= 100
        img = self.baseImage.resize((self.zoom,self.zoom), Image.ANTIALIAS)
        # baseImage.show()
        mapImage = ImageTk.PhotoImage(img)
        self.delete(tkinter.ALL)
        self.create_image(0, 0, image=img, anchor=tkinter.NW)


win = MainWindow()
win.mainloop()