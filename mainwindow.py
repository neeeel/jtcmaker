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

baseClasses = [["Car","Car/Taxi",1],["LGV","Light Goods Vehicle",1],["OGV1","Other Goods Vehicle 1",1.5],["OGV2","Other Goods Vehicle 2",2.3],["PSV","Omnibus",2],["MC","Motorcycle",0.4],["PC","Pedal Cycle",0.2]]

class MainWindow(tkinter.Tk):

    def __init__(self):
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        super(MainWindow, self).__init__()
        self.state("zoomed")
        self.mapPanel = tkinter.Canvas(self,relief=tkinter.RAISED,borderwidth=1,width=800,height=800)
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
        tkinter.Button(self,text="Export",command=self.export_to_excel).grid(row=4,column=0)
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
        self.mapPanel.grid(row=1, column=1, rowspan=3)
        # self.mapPanel.bind("<Double-Button-1>",self.add_arm_icon)
        self.mapPanel.bind("<Button-1>", self.on_press_to_move)
        self.mapPanel.bind("<Button-3>", self.on_right_click_to_move_map)
        self.bind("<Control_L>", self.control_pressed)
        self.bind("<KeyRelease-Control_L>", self.control_released)
        self.controlDown = False
        self.mapPanel.bind("<ButtonRelease-1>", self.onReleaseToMove)
        self.mapPanel.bind("<ButtonRelease-3>", self.onReleaseRightClickToMove)
        print("binding left and right")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
        self.mapPanel.bind("<Enter>", self.mouse_over_map_panel)
        self.mapPanel.bind("<Leave>", self.mouse_leave_map_panel)
        self.activity = None
        # self.load_map_panel_map(self.currentSite["Site Name"])
        # self.load_overview_map()
        # self.currentTag = ""
        # self.dragInfo = {}

        return



        ####
        ### Groups
        ###


        tkinter.Label(frame, text="Groups", font=f, fg=self.tracsisBlue,relief=tkinter.GROOVE,bg="light blue").grid(row = 10,column = 0,columnspan = 4,sticky="nsew")
        cols = ["Group"]
        self.groupsTree = ttk.Treeview(frame, columns=cols, height=7, show="headings", selectmode="browse")
        self.groupsTree.bind("<<TreeviewSelect>>", self.display_group)
        self.groupsTree.bind("<Double-Button-1>",self.delete_group)
        self.groupsTree.bind("<Button-3>", self.show_group_map)
        self.groupsTree.tag_configure("odd", background="white", foreground=self.tracsisBlue)
        self.groupsTree.tag_configure("even", background="azure2", foreground=self.tracsisBlue)
        for i, c in enumerate(cols):
            self.groupsTree.heading(i, text=c)#
        self.groupsTree.column(0, width=100, anchor=tkinter.CENTER)
        self.groupsTree.grid(row = 11,column = 0)
        #self.groupsTree.insert("","end",values= ["Group 1"],tags =("tree", "odd") )

        self.groupList = tkinter.Listbox(frame)
        self.groupList.bind("<Double-Button-1>", self.delete_site_from_group)
        self.groupList.bind("<Button-3>", self.show_group_map)
        self.groupList.grid(row = 11,column = 1,sticky = "ns")
        tkinter.Button(frame,text = "Add",command=self.add_group,width = 6).grid(row = 12,column = 0,columnspan = 1)
        #tkinter.Button(self.detailsPanel, text="Delete", command=self.delete_class,width = 6).grid(row=13, column=0, columnspan=2)



        self.winSpawned = False


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
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
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
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")
        self.timesTextBox.bind("<FocusIn>", self.disable_arm_delete)
        self.timesTextBox.bind("<FocusOut>", self.enable_arm_delete)
        self.periodBox = ttk.Combobox(frame, width=16)
        self.periodBox["values"] = ["5", "15", "30", "60"]
        self.periodBox.grid(row=4, column=1, sticky="nsew")

        tkinter.Label(frame, text="Classes", font=f, fg=self.tracsisBlue, relief=tkinter.GROOVE, bg="light blue").grid(
            row=5, column=0, columnspan=2, sticky="nsew")
        cols = ["Class", "PCU"]

        for i,col in enumerate(cols):
            tkinter.Label(frame,text = col).grid(row=6,column=i,sticky="nsew")
        classesframe = tkinter.Frame(frame, bg="red")
        classesframe.grid(row=7, column=0, columnspan=2, sticky="nsew")



        tkinter.Button(frame, text="Add", command=self.add_class, width=6).grid(row=8, column=0, sticky="nsew",columnspan=2)


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
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
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
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")
        self.timesTextBox.bind("<FocusIn>", self.disable_arm_delete)
        self.timesTextBox.bind("<FocusOut>", self.enable_arm_delete)
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
        # JTC TAB
        #
        ##########################################################################################

        tkinter.Label(frame, text=" Job Name ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE,
                      borderwidth=2).grid(row=0, column=0, sticky="nsew")
        tkinter.Label(frame, text=" Job No ", width=12, fg=self.tracsisBlue, relief=tkinter.GROOVE, borderwidth=2).grid(
            row=1, column=0, sticky="nsew")
        e = tkinter.Entry(frame, textvariable=self.jobNameVar, font=f2)
        e.grid(row=0, column=1, sticky="nsew")
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        e = tkinter.Entry(frame, textvariable=self.jobNumVar, font=f2)
        e.grid(row=1, column=1, sticky="nsew")
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
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
        e.bind("<FocusIn>", self.disable_arm_delete)
        e.bind("<FocusOut>", self.enable_arm_delete)
        self.timesTextBox = tkinter.Text(frame, height=3, width=20, wrap=tkinter.WORD, font=f2)
        self.timesTextBox.grid(row=3, column=1, sticky="nsew")
        self.timesTextBox.bind("<FocusIn>", self.disable_arm_delete)
        self.timesTextBox.bind("<FocusOut>", self.enable_arm_delete)
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
        #self.overviewPanel.delete(tkinter.ALL)
        #self.overviewPanel.create_image(5, 5, image=self.overviewDetails[0], anchor=tkinter.NW, tags=("map",))
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
        result = projectmanager.download_group_map(groupName)
        if result != False:
            img2 = Image.open(groupName + ".png")
            #img2.show()

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
    ### methods to deal with the site maps,importing, exporting projects etc
    ###
    ########################################################################################################################

    def change_site_image_type(self):
        projectmanager.change_site_image_type(self.imageTypeVar.get(),self.currentSite)
        self.redraw_map_with_labels()

    def load_project(self):
        self.armList = []
        self.mapPanel.delete(tkinter.ALL)
        self.overviewPanel.delete(tkinter.ALL)
        self.dragInfo["widget"] = None
        self.currentSite = projectmanager.load_project()
        self.display_classes()
        if not self.currentSite is None:
            self.display_project()

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
        self.redraw_map_with_labels()

    def display_project(self):
        print("current site is", self.currentSite)
        projectDetails = projectmanager.get_project_details()
        print("project details are",projectDetails)
        self.jobNameVar.set(projectDetails[0])
        self.jobNumVar.set(projectDetails[1])
        self.surveyDateVar.set(datetime.datetime.strftime(projectDetails[2], "%d/%m/%Y"))
        self.timesTextBox.delete("0.0",tkinter.END)
        self.timesTextBox.insert("0.0", projectDetails[3])
        self.focus_force()
        self.armLine = None
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.load_overview_map()
        self.currentTag = ""
        self.dragInfo = {}
        self.display_classes()

    def change_site_zoom(self,value):
        projectmanager.change_site_zoom(self.currentSite,value)
        self.redraw_map_with_labels()

    def export_to_excel(self):
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
        print("currenty site is",self.currentSite)
        self.redraw_map_with_labels()

    def decrement_map(self,event):
        print("pressed left arrow")
        self.currentSite = projectmanager.load_previous_site(self.currentSite)
        self.redraw_map_with_labels()

    def redraw_map_with_labels(self):
        self.mapPanel.delete(tkinter.ALL)
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.load_overview_map()
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.armLineStartingCoords = None
        self.armList = []
        self.currentTag = ""
        self.dragInfo = {}
        for key, item in self.currentSite["Arms"].items():
            print("drawing",key,item)
            self.currentTag = key
            self.draw_arm_label(key, item["coords"][0], item["coords"][1])
            self.redraw_arm_line(item["line coords"])
            e = tkinter.Entry(self, width=20)
            e.insert(0, self.currentSite["Arms"][key]["road"])
            e.bind("<Return>", lambda event, x=self.currentTag: self.update_road_name(event, x))
            e.bind("<FocusIn>",lambda event:self.disable_arm_delete(event,focus=True))
            e.bind("<FocusOut>", self.enable_arm_delete)
            self.currentSite["Arms"][key]["label"] = e
            coords = self.currentSite["Arms"][key]["labelcoords"]
            self.mapPanel.create_window((coords[0] , coords[1] ), window=e,tags =(key,"label"))
            self.armList.append(key)
        self.armList = sorted(self.armList)
        print("armlist is",self.armList)
        self.bind_all("<Delete>", self.delete_most_recent_arm)
        if self.currentSite["imageType"] == "roadmap":
            val = 0
        else:
            val = 1
        self.imageTypeVar.set(val)

    def load_map_panel_map(self,siteName):
        self.mapPanelImage = ImageTk.PhotoImage(self.currentSite["image"])
        allwidgetsWithTag = self.mapPanel.find_withtag("map")
        print("allwidgets with tag are", allwidgetsWithTag)
        for child in allwidgetsWithTag:
            self.mapPanel.delete(child)
        self.mapPanel.create_image(5, 5, image=self.mapPanelImage, anchor=tkinter.NW,tags=("map",))
        self.mapPanel.configure(width=self.mapPanelSize,height=self.mapPanelSize)


    ####################################################################################################
    ###
    ### Functions to deal with adding, dragging, dropping and adjusting any icons etc
    ### that we have added to a particular map
    ###

    def control_pressed(self,event):
        self.controlDown = True

    def control_released(self,event):
        self.controlDown = False

    def draw_arm_label(self,armName,x,y):
        print("Drawing a label at ",x,y)
        f = tkinter.font.Font(family='Helvetica', size=self.fontsize, weight=tkinter.font.BOLD)
        self.mapPanel.create_oval(x-self.armLabelRadius,y-self.armLabelRadius,x+self.armLabelRadius,y+self.armLabelRadius,width = 3,outline="red",tags=str(armName))
        self.mapPanel.create_text((x,y),text=armName,font=f,tags=str(armName))
        self.currentTag = str(armName)

    def pick_up_line(self):
        self.unbind_all("<BackSpace>")
        self.unbind_all("<Delete>")
        print("unbinding left and right in add arm icon")
        self.unbind("<Left>")
        self.unbind("<Right>")
        #self.mapPanel.bind("<Button-1>", self.finish_arm_line)
        self.mapPanel.bind("<Motion>", self.draw_arm_line)

    def add_arm_icon(self,event):
        print("currentsite is",self.currentSite)
        if self.movingMap == True:
            print("moving map, not allowing left click functionality")
            return
        self.drawingArm = True
        x = event.x - self.mapPanel.canvasx(0)
        y = event.y - self.mapPanel.canvasy(0)
        if self.currentSite["Arms"] == {}:
            armName = "A"
        else:
            armName = chr(ord(sorted(self.currentSite["Arms"].keys())[-1])+1)
        projectmanager.edit_arm(self.currentSite["Site Name"],armName,x,y)
        self.draw_arm_label(armName,x,y)
        self.mapPanel.unbind("<Double-Button-1>")
        self.unbind_all("<BackSpace>")
        self.unbind_all("<Delete>")
        print("unbinding left and right in add arm icon")
        self.unbind("<Left>")
        self.unbind("<Right>")
        #self.update()
        self.armLineStartingCoords = (x,y)
        self.armList.append(armName)
        #self.mapPanel.bind("<Button-1>", self.finish_arm_line)
        self.mapPanel.bind("<Motion>", self.draw_arm_line)
        print("armlist is",self.armList)

    def redraw_arm_line(self,lineCoords):
        self.armLine = self.mapPanel.create_line(lineCoords, fill="red", width=3, tags=(self.currentTag, "line"))
        print("redrawing line, self.armline is now,",self.armLine)
        self.dragInfo["Widget"] =self.armLine
        self.armLine = None

    def delete_most_recent_arm(self,event):
        if not self.allowArmDelete:
            return
        print("deleting arm")
        if self.armList == []:              return
        print("armlist is",self.armList)
        armName = (self.armList.pop(-1))
        self.currentSite["Arms"][armName]["label"].destroy()
        self.mapPanel.delete(armName)
        print("armlist is", self.armList)
        projectmanager.delete_arm_from_site(self.currentSite["Site Name"],armName)
        projectmanager.decrement_arm_label()

    def draw_arm_line(self,event):
        print("in draw arm line,self.armline is",self.armLine)
        #print("unbinding left and right in draw arm line")
        self.unbind("<Left>")
        self.unbind("<Right>")
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)

        allwidgetsWithTag = self.mapPanel.find_withtag(self.currentTag)
        x1,y1,x2,y2 = self.mapPanel.coords(allwidgetsWithTag[0])
        centre_X = x1 + 15
        centre_Y = y1 + 15
        self.mapPanel.delete(self.armLine)

        dx = winX-centre_X
        dy = winY-centre_Y
        if dy != 0:
            theta = np.arctan(dx / dy)
            offsetX = self.armLabelRadius * np.sin(theta)
        else:
            offsetX=(dx/abs(dx))*15
        if dx != 0:
            if dy != 0:
                theta = np.arctan(dx / dy)
                offsetY = offsetX / np.tan(theta)
            else:
                offsetY =0
        else:
            offsetY =15
        if winY >=centre_Y:
            newY =centre_Y + offsetY
            newX = centre_X + offsetX
        else:
            newY = centre_Y - offsetY
            newX = centre_X - offsetX
        self.armLine = self.mapPanel.create_line((newX,newY),(winX,winY),fill="blue",width=3,tags = (self.currentTag,"line"))
        #self.dragInfo["Widget"] = self.armLine

    def finish_arm_line(self):
        print("on entering finishing arm line, all widgets with tag",self.currentTag,"are",self.mapPanel.find_withtag(self.currentTag))
        if self.armLine is None:
            self.drawingArm = False
            return
        self.mapPanel.unbind("<Motion>")
        print("in finish arm line, self.armline widget is",self.armLine)
        print("tags are ",self.mapPanel.gettags(self.armLine))
        self.mapPanel.itemconfigure(self.armLine,fill = "red")
        coords = self.mapPanel.coords(self.armLine)
        dx = coords[0]-coords[2]
        dy = coords[1]-coords[3]
        if dy != 0:
            theta = np.arctan(dx / dy)
        else:
            theta = 1
        print("theta is",theta,np.degrees(theta),dx,dy)
        if theta == 1 and dx < 0:
            print("orientation 90")
            orientation = 90
        elif theta == 1 and dx > 0:
            print("orientation 270")
            orientation = 270
        elif theta == 0.0 and dy > 0:
            print("orientation 0")
            orientation = 0
        elif theta == -0.0 and dy < 0:
            print("orientation 180")
            orientation = 180
        elif dx<0 and dy>0:
            print("orientation",-np.degrees(theta))
            orientation =-np.degrees(theta)
        elif dx<0 and dy<0:
            print("orientation",90 + (90-np.degrees(theta)))
            orientation = 90 + (90-np.degrees(theta))
        elif dx>0 and dy<0:
            print("orientation",180 - np.degrees(theta))
            orientation = 180 - np.degrees(theta)
        elif dx>0 and dy>0:
            print("orientation",270 + (90-np.degrees(theta)))
            orientation = 270 + (90-np.degrees(theta))
        #projectmanager.edit_arm_orientation(self.currentSite["Site Name"],self.currentTag,orientation)
        print("self.currenttag is",self.currentTag)
        self.currentSite["Arms"][self.currentTag]["orientation"] = orientation
        self.currentSite["Arms"][self.currentTag]["line coords"] = self.mapPanel.coords(self.armLine)
        #print("in mainwindow, site is now ", self.currentSite)
        #print("line coords are ",self.mapPanel.coords(self.armLine))
        #self.dragInfo["tag"] = self.mapPanel.gettags(self.armLine)[0]
        self.armLine = None
        self.bind_all("<BackSpace>", self.delete_most_recent_arm)
        self.bind_all("<Delete>", self.delete_most_recent_arm)
        self.pickedUpLine = False
        self.drawingArm = False
        mag = ((dx**2) + (dy**2)) **(1/2)
        unit_x = dx/mag
        unit_y = dy/mag
        if orientation > 250 and orientation < 290:
            x = coords[0] +(100*unit_x)
        elif orientation > 70 and orientation < 110:
            x = coords[0] +(100 *unit_x)
        else:
            x = coords[0] + (80 * unit_x)
        y = coords[1] + (80 * unit_y)

        e = tkinter.Entry(self,width = 20)
        e.insert(0,self.currentSite["Arms"][self.currentTag]["road"])
        e.bind("<Return>",lambda event,x = self.currentTag:self.update_road_name(event,x))
        e.bind("<FocusIn>",lambda event:self.disable_arm_delete(event,focus=True))
        e.bind("<FocusOut>",self.enable_arm_delete)
        print("just before deliting widget,finishing arm line all widgets with tag",self.currentTag,"are",self.mapPanel.find_withtag(self.currentTag))
        try:
            print("type of label is",type(self.currentSite["Arms"][self.currentTag]["label"]))
            self.currentSite["Arms"][self.currentTag]["label"].destroy()
            self.mapPanel.delete(self.mapPanel.find_withtag(self.currentTag)[2])
        except Exception as err:
            # it didnt exist, so do nothing
            print("error deleteing label")
        self.currentSite["Arms"][self.currentTag]["label"] = e
        self.currentSite["Arms"][self.currentTag]["labelcoords"] = (x,y)
        self.mapPanel.create_window((x,y),window=e,tags =(self.currentTag,"label"))
        print("finishing arm line all widgets with tag",self.currentTag,"are",self.mapPanel.find_withtag(self.currentTag))
        #self.focus_set()

    def disable_arm_delete(self,event,focus=False):
        self.allowArmDelete = False
        if focus:
            ###
            ### we need to lose focus of the job details text boxes when we go over the map panel, so that
            ### users can delete arms with the Delete key. But if we are editing road names, we dont want to lose focus
            ### when the user mouses over the map panel, so we disable that
            ###
            event.widget.config(bg="white")
            self.mapPanel.unbind("<Enter>")
            self.mapPanel.unbind("<Leave>")

    def enable_arm_delete(self,event):
        self.allowArmDelete = True
        self.mapPanel.bind("<Enter>", self.mouse_over_map_panel)
        self.mapPanel.bind("<Leave>", self.mouse_leave_map_panel)

    def update_road_name(self,event,armLabel):
        print(event.widget.get(),armLabel)
        event.widget.config(bg="light blue")
        self.currentSite["Arms"][armLabel]["road"] = event.widget.get()
        self.groupList.focus_force()

    def on_right_click_to_move_map(self,event):
        if self.drawingArm == True:
            print("drawing arm, not allowing movement of map")
            return
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("clicked at", winX, winY)
        closestWidget = self.mapPanel.find_closest(event.x, event.y, halo=10)[0]

        tags = self.mapPanel.gettags(closestWidget)
        print("tags are",tags)
        if "map" in tags:
            self.movingMap = True
            print("clicked on the map")
            self.dragInfo["Widget"] = closestWidget
            self.dragInfo["xCoord"] = winX
            self.dragInfo["yCoord"] = winY
            self.dragInfo["tag"] = -1
            self.dragInfo["tag"] = "map"
            self.mapClickedCoords = (winX, winY)
            self.mapPanel.bind("<B3-Motion>", self.onright_click_movement)
            self.mapPanel.bind("<ButtonRelease-3>", self.onReleaseRightClickToMove)
            return

    def onReleaseRightClickToMove(self,event):
        if self.drawingArm == True:
            return
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("binding")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
        #print("map was moved", winX - self.mapClickedCoords[0], winY - self.mapClickedCoords[1])
        self.mapPanel.unbind("<B3-Motion>")
        self.mapPanel.unbind("<ButtonRelease-3>")
        if self.movingMap == True:
            if winX - self.mapClickedCoords[0] != 0 and winY - self.mapClickedCoords[1] != 0:
                projectmanager.change_site_centre_point(self.currentSite["Site Name"], winX - self.mapClickedCoords[0],winY - self.mapClickedCoords[1])
                self.redraw_map_with_labels()
        self.movingMap = False

    def onright_click_movement(self, event):
        if self.dragInfo["tag"] == -1:
            return
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("mouse is now at",winX,winY)
        newX = winX - self.dragInfo["xCoord"]
        newY = winY - self.dragInfo["yCoord"]
        if self.dragInfo["tag"] == "map":
            for child in self.mapPanel.find_all():
                self.mapPanel.move(child, newX, newY)
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY

    def on_press_to_move(self,event):
        print("self.activity is",self.activity)
        if self.activity is None:
            if self.controlDown:
                self.activity = "drawing line"
                x = event.x - self.mapPanel.canvasx(0)
                y = event.y - self.mapPanel.canvasy(0)
                if self.currentSite["Arms"] == {}:
                    armName = "A"
                else:
                    armName = chr(ord(sorted(self.currentSite["Arms"].keys())[-1]) + 1)
                projectmanager.edit_arm(self.currentSite["Site Name"], armName, x, y)
                self.draw_arm_label(armName, x, y)
                self.currentTag = armName
                self.armLineStartingCoords = (x, y)
                self.armList.append(armName)
                self.pick_up_line()
            else:
                selectedWidget = self.mapPanel.find_closest(event.x, event.y, halo=10)[0]
                tags = self.mapPanel.gettags(selectedWidget)
                allwidgetsWithTag = self.mapPanel.find_withtag(tags[0])
                self.currentTag = tags[0]
                print("tags of closest widget are",tags,allwidgetsWithTag)
                if "map" in tags:
                    return
                if "line" in tags:
                    self.activity = "drawing line"
                    self.armLine = selectedWidget
                    self.pick_up_line()
                else:
                    # clicked a circle
                    print("clicked a circle")
                    self.activity = "circle"
                    self.mapPanel.bind("<B1-Motion>", self.onMovement)
                    self.mapPanel.bind("<ButtonRelease>", self.onReleaseToMove)
                    self.mapPanel.itemconfigure(allwidgetsWithTag[0], outline="blue")
                    self.mapPanel.itemconfigure(allwidgetsWithTag[1], fill="blue")
                    self.widgetCoords = self.mapPanel.coords(selectedWidget)
                    print("widgetcoords are",self.widgetCoords)
                self.mapPanel.itemconfigure(allwidgetsWithTag[2], fill="blue")
        else:
            if self.activity == "drawing line":
                print("clicked while drawing line active")
                "<motion"
                self.finish_arm_line()
                self.activity = None

    def onReleaseToMove(self, event):  # reset data on release
        if self.activity == "circle":
            print("in onreleasetomove, self.currenttag is",self.currentTag)
            allwidgetsWithTag = self.mapPanel.find_withtag(self.currentTag)
            print("allwidgets with tag are", allwidgetsWithTag)
            self.mapPanel.itemconfigure(allwidgetsWithTag[0], outline="red")
            self.mapPanel.itemconfigure(allwidgetsWithTag[1], fill="black")
            self.mapPanel.itemconfigure(allwidgetsWithTag[2], fill="red")
            self.mapPanel.unbind("<B1-Motion>")
            self.mapPanel.unbind("<ButtonRelease>")
            self.currentSite["Arms"][self.currentTag]["line coords"] = self.mapPanel.coords(allwidgetsWithTag[2])
            print(",line coords are",self.currentSite["Arms"][self.currentTag]["line coords"])
            coords = self.mapPanel.coords(allwidgetsWithTag[0])
            self.currentSite["Arms"][self.currentTag]["coords"] = (coords[0]+self.armLabelRadius,coords[1]+self.armLabelRadius)
            self.currentSite["Arms"][self.currentTag]["labelcoords"] = self.mapPanel.coords(allwidgetsWithTag[3])
            print("coords of label are",self.mapPanel.coords(allwidgetsWithTag[3]))
            self.activity = None
            print("finished onreleasetomove")

    def onMovement(self, event):
        print("tag is",self.currentTag)
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("mouse is now at",winX,winY)
        newX = winX - self.widgetCoords[0]
        newY = winY - self.widgetCoords[1]
        if self.activity == "map":
            for child in self.mapPanel.find_all():
                self.mapPanel.move(child, newX, newY)
        else:
            for child in self.mapPanel.find_withtag(self.currentTag):
                self.mapPanel.move(child, newX, newY)
            self.widgetCoords = (winX,winY)

    ########################################################################################################

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