import tkinter
from PIL import Image,ImageDraw,ImageTk
import projectmanager
import mapmanager
from tkinter import font
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
        self.mapPanel = tkinter.Canvas(self,relief=tkinter.RAISED,borderwidth=1)
        self.mapPanelImage = None
        self.overviewImage = None
        self.mapPanelSize = 800 ### TODO change this to deal with different screen res
        self.armLabelRadius = 15
        self.fontsize = 10
        self.pickedUpLine = False

        ### set up the menu bar

        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Load Project", command=self.load_project)
        #menu.add_command(label="Occupancy Mismatch", command=self.get_occupancy_mismatch)
        self.menubar.add_cascade(label="File", menu=menu)
        self.config(menu=self.menubar)


        self.mapPanelHasFocus = False
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        f2 = tkinter.font.Font(family='Helvetica', size=8)
        tkinter.Label(self, text="Job Details", font=f, fg=self.tracsisBlue).grid(row=0, column=0)
        self.detailsPanel = tkinter.Frame(self,relief=tkinter.GROOVE,borderwidth=2)
        tkinter.Label(self.detailsPanel,text = "Job Name",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =0,column=0)
        tkinter.Label(self.detailsPanel,text = "Job No",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =1,column=0)
        tkinter.Label(self.detailsPanel,text = "Survey Date",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =2,column=0)
        tkinter.Label(self.detailsPanel,text = "Times",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =3,column=0)
        tkinter.Label(self.detailsPanel,text = "Period",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =4,column=0)

        self.jobNameVar = tkinter.StringVar()
        self.jobNumVar = tkinter.StringVar()
        self.surveyDateVar = tkinter.StringVar()
        self.timesVar = tkinter.StringVar()

        tkinter.Entry(self.detailsPanel,textvariable = self.jobNameVar,font = f2).grid(row =0,column=1)
        tkinter.Entry(self.detailsPanel, textvariable=self.jobNumVar,font = f2).grid(row =1,column=1)
        tkinter.Entry(self.detailsPanel, textvariable=self.surveyDateVar,font = f2).grid(row =2,column=1)
        self.timesTextBox = tkinter.Text(self.detailsPanel,height = 3,width = 20,wrap=tkinter.WORD,font = f2)
        self.timesTextBox.grid(row =3,column=1)
        self.periodBox = ttk.Combobox(self.detailsPanel,width = 16)
        self.periodBox["values"] = ["5","15","30","60"]
        self.periodBox.grid(row = 4,column=1)


        tkinter.Label(self.detailsPanel,text = "Classes",fg = self.tracsisBlue).grid(row = 5,column = 0,columnspan = 2)
        cols = ["Class", "Description", "PCU"]
        self.classesTree = ttk.Treeview(self.detailsPanel,columns = cols,height = 8,show = "headings",selectmode = "browse")
        self.classesTree.bind("<Double-Button-1>", self.edit_class)
        self.classesTree.tag_configure("odd", background="white", foreground=self.tracsisBlue)
        self.classesTree.tag_configure("even", background="azure2", foreground=self.tracsisBlue)
        for i,c in enumerate(cols):
            self.classesTree.heading(i,text = c)
        self.classesTree.column(0, width=60, anchor=tkinter.CENTER)
        self.classesTree.column(1, width=150, anchor=tkinter.CENTER)
        self.classesTree.column(2, width=40, anchor=tkinter.CENTER)
        self.classesTree.grid(row = 6,column = 0,columnspan = 2)
        for i,row in enumerate(baseClasses):
            if i%2 == 0:
                self.classesTree.insert("","end",values =row,tags=("tree","even"))
            else:
                self.classesTree.insert("", "end", values=row, tags=("tree", "odd"))

        tkinter.Button(self.detailsPanel,text = "Add",command=self.add_class,width = 6).grid(row = 7,column = 0,columnspan = 2)
        tkinter.Button(self.detailsPanel, text="Delete", command=self.delete_class,width = 6).grid(row=8, column=0, columnspan=2)

        ####
        ### Groups
        ###


        tkinter.Label(self.detailsPanel, text="Groups", font=f, fg=self.tracsisBlue).grid(row = 9,column = 0,columnspan = 2)
        cols = ["Group"]
        self.groupsTree = ttk.Treeview(self.detailsPanel, columns=cols, height=8, show="headings", selectmode="browse")
        self.groupsTree.bind("<<TreeviewSelect>>", self.display_group)
        self.groupsTree.bind("<Double-Button-1>",self.delete_group)
        self.groupsTree.tag_configure("odd", background="white", foreground=self.tracsisBlue)
        self.groupsTree.tag_configure("even", background="azure2", foreground=self.tracsisBlue)
        for i, c in enumerate(cols):
            self.groupsTree.heading(i, text=c)#
        self.groupsTree.column(0, width=100, anchor=tkinter.CENTER)
        self.groupsTree.grid(row = 10,column = 0,columnspan = 2)
        #self.groupsTree.insert("","end",values= ["Group 1"],tags =("tree", "odd") )

        self.groupList = tkinter.Listbox(self.detailsPanel)
        self.groupList.bind("<Double-Button-1>", self.delete_site_from_group)
        self.groupList.grid(row = 12,column = 0,columnspan = 2)
        tkinter.Button(self.detailsPanel,text = "Add",command=self.add_group,width = 6).grid(row = 11,column = 0,columnspan = 2)
        #tkinter.Button(self.detailsPanel, text="Delete", command=self.delete_class,width = 6).grid(row=13, column=0, columnspan=2)

        self.winSpawned = False
        self.detailsPanel.grid(row=1,column=0,sticky="n")


        #self.currentSite = projectmanager.load_project()
        #projectDetails = projectmanager.get_project_details()
        #self.jobNameVar.set(projectDetails[0])
        #self.jobNumVar.set(projectDetails[1])
        #self.surveyDateVar.set(datetime.datetime.strftime(projectDetails[2],"%d/%m/%Y"))
        #self.timesTextBox.insert("0.0",projectDetails[3])
        #self.focus_force()
        #self.armLine = None

        #self.mapLabel = tkinter.Label(self,text = self.currentSite["Site Name"],font=f,fg=self.tracsisBlue)
        self.mapLabel = tkinter.Label(self, text="", font=f, fg=self.tracsisBlue)
        self.mapLabel.grid(row = 0,column = 1)
        tkinter.Button(self,text="Export",command=self.export_to_excel).grid(row=4,column=0)
        frame = tkinter.Frame(self)
        tkinter.Button(frame, text="<", command=lambda:self.decrement_map(None),width = 4,height = 2).grid(row=0, column=0,padx = 5)
        tkinter.Button(frame, text="+", command=lambda:self.change_site_zoom("+"),width = 4,height = 2).grid(row=0, column=1,padx = 5)
        tkinter.Button(frame, text="-", command=lambda:self.change_site_zoom("-"),width = 4,height = 2).grid(row=0, column=2,padx = 5)
        tkinter.Button(frame, text=">", command=lambda:self.increment_map(None),width = 4,height = 2).grid(row=0, column=3,padx = 5)
        frame.grid(row = 4,column=1)



        tkinter.Label(self, text="Overview", font=f, fg=self.tracsisBlue).grid(row=0, column=2)
        self.overviewPanel = tkinter.Canvas(self,bg="white",relief=tkinter.RAISED,borderwidth=1)
        self.overviewPanel.bind("<Button-1>",self.overview_map_clicked)
        self.overviewPanel.grid(row = 1,column = 2)
        self.addingArmLabel = False
        self.armLineStartingCoords = None
        self.armList = []
        self.mapPanel.grid(row=1,column=1,rowspan=3)
        self.mapPanel.bind("<Double-Button-1>",self.add_arm_icon)
        self.mapPanel.bind("<Button-1>",self.on_press_to_move)
        self.mapPanel.bind("<Button-3>", self.on_right_click_to_move_map)

        self.mapPanel.bind("<ButtonRelease-1>",self.onReleaseToMove)
        self.mapPanel.bind("<ButtonRelease-3>", self.onReleaseRightClickToMove)
        print("binding left and right")
        self.bind("<Left>",self.decrement_map)
        self.bind("<Right>", self.increment_map)
        self.mapPanel.bind("<Enter>",self.mouse_over_map_panel)
        self.mapPanel.bind("<Leave>",self.mouse_leave_map_panel)

        #self.load_map_panel_map(self.currentSite["Site Name"])
        #self.load_overview_map()
        #self.currentTag = ""
        #self.dragInfo = {}


    ##########################################################################################################################
    ###
    ### Functions to deal with the overview panel, defining and selecting groups
    ###

    def overview_map_clicked(self,event):
        print(event.x,event.y)
        widget = self.overviewPanel.find_closest(event.x, event.y, halo=10)[0]
        print("widget is",widget)
        tags = self.overviewPanel.gettags(widget)
        print("tags are",tags)
        print("closest site is",tags[0])
        if "site" in tags[0].lower():
            self.add_site_to_group(tags[0])



    def mouse_over_map_panel(self,event):
        print("mouse over")
        #self.mapPanel.config(highlightbackground="red")
        self.mapPanelHasFocus = True
        self.mapPanel.focus_set()

    def mouse_leave_map_panel(self,event):
        print("mouse left")
        #self.mapPanel.config(highlightbackground="grey")
        self.mapPanelHasFocus = False

    def return_clicked(self,event):
        print("ohohowoeroiwj")

    def load_overview_map(self):
        circleRadius = 10
        self.overviewDetails = projectmanager.get_overview_map()
        self.overviewPanel.create_image(5, 5, image=self.overviewDetails[0], anchor=tkinter.NW, tags=("map",))
        self.overviewPanel.configure(width=800, height=800)
        self.groupsTree.delete(*self.groupsTree.get_children())
        for name,grp in sorted(projectmanager.get_groups().items()):
            rowCount = len(self.classesTree.get_children())
            if rowCount % 2 == 0:
                self.groupsTree.insert("", "end", values=[name], tags=("tree", "even"))
            else:
                self.groupsTree.insert("", "end", values=[name], tags=("tree", "odd"))
        self.display_group(None)


    def draw_overview_site_labels(self):
        circleRadius = 10
        colour = "black"
        for child in self.overviewPanel.find_all():
            tags = self.overviewPanel.gettags(child)
            print("tags are", tags)
            if "site" in tags[0].lower():
                print("deleteing",child)
                self.overviewPanel.delete(child)
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
            self.overviewPanel.create_oval(coords[0]-circleRadius,coords[1]-circleRadius,coords[0]+circleRadius,coords[1]+circleRadius,width = 3,outline=colour,tags=[str(siteName)])
            self.overviewPanel.create_text((coords[0],coords[1]),text=siteName.split(" ")[1],tags=[str(siteName)])
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
        curItem = self.groupsTree.selection()[0]
        groupName = self.groupsTree.item(curItem)["values"][0]
        print("selected group", groupName)
        if groupName != "ALL":
            self.groupsTree.delete(curItem)
            projectmanager.delete_group(groupName)

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

    def spawn_edit_window(self,className = "",desc = "",pcu = ""):
        if not self.winSpawned:
            self.winSpawned = True
            self.win = tkinter.Toplevel(self)
            self.classesTree.configure(selectmode = "none")
            tkinter.Label(self.win, text="Class", anchor=tkinter.E, width=12).grid(row=0, column=0)
            tkinter.Label(self.win, text="Description", anchor=tkinter.E, width=12).grid(row=1, column=0)
            tkinter.Label(self.win, text="PCU", anchor=tkinter.E, width=12).grid(row=2, column=0)

            self.classVar = tkinter.StringVar()
            self.descVar = tkinter.StringVar()
            self.PCUVar = tkinter.StringVar()
            self.classVar.set(className)
            self.descVar.set(desc)
            self.PCUVar.set(pcu)
            tkinter.Entry(self.win, textvariable=self.classVar).grid(row=0, column=1,columnspan =2)
            tkinter.Entry(self.win, textvariable=self.descVar).grid(row=1, column=1,columnspan =2)
            tkinter.Entry(self.win, textvariable=self.PCUVar).grid(row=2, column=1,columnspan =2)

            tkinter.Button(self.win, text="Cancel",command=self.edit_window_closed).grid(row=3, column=1)
            tkinter.Button(self.win, text="Save",command=self.edit_window_saved,width=6).grid(row=3, column=2)

    def edit_window_closed(self):
        self.winSpawned = False
        self.classesTree.configure(selectmode="browse")
        self.win.destroy()

    def edit_window_saved(self):
        values = [self.classVar.get(), self.descVar.get(), self.PCUVar.get()]
        if self.addClass:
            rowCount = len(self.classesTree.get_children())
            if rowCount % 2 == 0:
                self.classesTree.insert("", "end", values=values,tags=("tree", "even"))
            else:
                self.classesTree.insert("", "end", values=values, tags=("tree", "odd"))
        else:
            curItem = self.classesTree.selection()[0]
            self.classesTree.item(curItem,values = values)
        self.addClass=False
        self.edit_window_closed()

    def edit_class(self,event):
        self.addClass = False
        widget = event.widget
        curItem = widget.selection()[0]
        values = widget.item(curItem)["values"]
        self.spawn_edit_window(className=values[0],desc=values[1],pcu=values[2])

    def add_class(self):
        self.addClass = True
        self.spawn_edit_window()

    def delete_class(self):
        try:
            curItem = self.classesTree.selection()[0]
            print("curitem is",curItem)
            self.classesTree.delete(curItem)
            for i,child in enumerate(self.classesTree.get_children()):
                if i % 2 == 0:
                    self.classesTree.item(child,tags=("tree", "even"))
                else:
                    self.classesTree.item(child,tags=("tree", "odd"))
        except IndexError as e:
            pass

    ########################################################################################################################
    ###
    ### methods to deal with the site maps,importing, exporting projects etc
    ###

    def load_project(self):
        self.currentSite = projectmanager.load_project()
        projectDetails = projectmanager.get_project_details()
        self.jobNameVar.set(projectDetails[0])
        self.jobNumVar.set(projectDetails[1])
        self.surveyDateVar.set(datetime.datetime.strftime(projectDetails[2], "%d/%m/%Y"))
        self.timesTextBox.insert("0.0", projectDetails[3])
        self.focus_force()
        self.armLine = None
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.load_overview_map()
        self.currentTag = ""
        self.dragInfo = {}

    def change_site_zoom(self,value):
        projectmanager.change_site_zoom(self.currentSite["Site Name"],value)
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
        messagebox.showinfo(message="Export Finished")

    def increment_map(self,event):
        print("pressed right arrow")
        self.currentSite = projectmanager.load_next_site(self.currentSite["Site Name"])
        self.redraw_map_with_labels()

    def decrement_map(self,event):
        print("pressed left arrow")
        self.currentSite = projectmanager.load_previous_site(self.currentSite["Site Name"])
        self.redraw_map_with_labels()

    def redraw_map_with_labels(self):
        self.mapPanel.delete(tkinter.ALL)
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.armLineStartingCoords = None
        self.armList = []
        self.currentTag = ""
        self.dragInfo = {}
        for key, item in self.currentSite["Arms"].items():
            self.draw_arm_label(key, item["coords"][0], item["coords"][1])
            self.redraw_arm_line(item["line coords"])
            self.armList.append(key)

    def load_map_panel_map(self,siteName):
        self.mapPanelImage = projectmanager.get_site_map(siteName)
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

    def add_arm_icon(self,event):
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
        self.mapPanel.bind("<Button-1>", self.finish_arm_line)
        self.mapPanel.bind("<Motion>", self.draw_arm_line)
        print("armlist is",self.armList)

    def draw_arm_label(self,armName,x,y):
        print("Drawing a label at ",x,y)
        f = tkinter.font.Font(family='Helvetica', size=self.fontsize, weight=tkinter.font.BOLD)
        self.mapPanel.create_oval(x-self.armLabelRadius,y-self.armLabelRadius,x+self.armLabelRadius,y+self.armLabelRadius,width = 3,outline="red",tags=str(armName))
        self.mapPanel.create_text((x,y),text=armName,font=f,tags=str(armName))
        self.currentTag = str(armName)

    def redraw_arm_line(self,lineCoords):
        self.armLine = self.mapPanel.create_line(lineCoords, fill="red", width=3, tags=(self.currentTag, "line"))
        print("redrawing line, self.armline is now,",self.armLine)
        self.dragInfo["Widget"] =self.armLine

    def delete_most_recent_arm(self,event):
        if self.mapPanelHasFocus:
            if self.armList == []:              return
            armName = (self.armList.pop(-1))
            self.mapPanel.delete(armName)
            projectmanager.delete_arm_from_site(self.currentSite["Site Name"],armName)
            projectmanager.decrement_arm_label()

    def draw_arm_line(self,event):
        print("in draw arm line,self.armline is",self.armLine)
        #print("unbinding left and right in draw arm line")
        self.unbind("<Left>")
        self.unbind("<Right>")
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        if self.armLine is not None:
            tags = self.mapPanel.gettags(self.armLine)
            self.currentTag = tags[0]
            allwidgetsWithTag = self.mapPanel.find_withtag(tags[0])
            x1,y1,x2,y2 = self.mapPanel.coords(allwidgetsWithTag[0])
            centre_X = x1 + 15
            centre_Y = y1 + 15
            #print("centre of circle",centre_X,centre_Y)
            self.mapPanel.delete(self.armLine)
        else:
            centre_X,centre_Y = self.armLineStartingCoords
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
        self.dragInfo["Widget"] = self.armLine

    def finish_arm_line(self,event):
        if self.armLine is None:
            return
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        self.mapPanel.unbind("<Motion>")
        self.mapPanel.bind("<Double-Button-1>", self.add_arm_icon)
        self.mapPanel.bind("<Button-1>", self.on_press_to_move)
        print("binding left and right in finish arm line")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
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
        self.currentSite["Arms"][self.currentTag]["orientation"] = orientation
        self.currentSite["Arms"][self.currentTag]["line coords"] = self.mapPanel.coords(self.armLine)
        print("in mainwindow, site is now ", self.currentSite)
        print("line coords are ",self.mapPanel.coords(self.armLine))
        self.armLine = None
        self.bind_all("<BackSpace>", self.delete_most_recent_arm)
        self.bind_all("<Delete>", self.delete_most_recent_arm)
        self.pickedUpLine = False
        #self.focus_set()

    def on_right_click_to_move_map(self,event):
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("clicked at", winX, winY)
        closestWidget = self.mapPanel.find_closest(event.x, event.y, halo=10)[0]

        tags = self.mapPanel.gettags(closestWidget)
        if "map" in tags:
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
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("binding")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
        print("map was moved", winX - self.mapClickedCoords[0], winY - self.mapClickedCoords[1])
        self.mapPanel.unbind("<B3-Motion>")
        self.mapPanel.unbind("<ButtonRelease-3>")
        if winX - self.mapClickedCoords[0] != 0 and winY - self.mapClickedCoords[1] != 0:
            projectmanager.change_site_centre_point(self.currentSite["Site Name"], winX - self.mapClickedCoords[0],winY - self.mapClickedCoords[1])
            self.redraw_map_with_labels()
        return

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
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("clicked at", winX, winY)
        self.dragInfo["Widget"] = self.mapPanel.find_closest(event.x, event.y, halo=10)[0]
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY
        self.dragInfo["tag"] = -1
        tags = self.mapPanel.gettags(self.dragInfo["Widget"])
        allwidgetsWithTag = self.mapPanel.find_withtag(tags[0])
        print("unbinding left and right in on press to move")
        self.unbind("<Left>")
        self.unbind("<Right>")
        if "line" in (tags):
            self.pickedUpLine = True
            self.mapPanel.unbind("<ButtonRelease>")
            print("picked up line,widget",self.dragInfo["Widget"])
            print("tags on line are",tags)
            print("allwidgets with tag",tags[0],allwidgetsWithTag)
            self.armLine = self.dragInfo["Widget"]
            self.mapPanel.bind("<Motion>", self.draw_arm_line)
            self.mapPanel.bind("<Button-1>", self.finish_arm_line)
            self.mapPanel.unbind_all("<ButtonRelease>")

        else:
            if "map" in tags:
                print("clicked on the map")
                self.dragInfo["tag"] = "map"
                return
                self.mapClickedCoords = (winX,winY)
                self.mapPanel.bind("<B1-Motion>", self.onMovement)
                self.mapPanel.bind("<ButtonRelease>", self.onReleaseToMove)
                return
            else:
                print("clicked on a circle")
                self.mapPanel.bind("<B1-Motion>", self.onMovement)
                self.mapPanel.bind("<ButtonRelease>", self.onReleaseToMove)
                self.mapPanel.itemconfigure(allwidgetsWithTag[0], outline="blue")
                self.mapPanel.itemconfigure(allwidgetsWithTag[1], fill="blue")
        print("-"*200)
        self.dragInfo["tag"] = tags[0]
        print("setting draginfo tag to",self.dragInfo["tag"])
        self.mapPanel.itemconfigure(allwidgetsWithTag[2], fill="blue")

    def onReleaseToMove(self, event):  # reset data on release
        if self.pickedUpLine:
            print("picked up line is true")
            return
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        if self.dragInfo["tag"] == "map":
            print("binding")
            self.bind("<Left>", self.decrement_map)
            self.bind("<Right>", self.increment_map)
            return
            print("map was moved",winX - self.mapClickedCoords[0],winY - self.mapClickedCoords[1])
            self.mapPanel.unbind("<B1-Motion>")
            self.mapPanel.unbind("<ButtonRelease>")
            if winX - self.mapClickedCoords[0]!= 0  and winY - self.mapClickedCoords[1] != 0:
                projectmanager.change_site_centre_point(self.currentSite["Site Name"],winX - self.mapClickedCoords[0],winY - self.mapClickedCoords[1])
                self.redraw_map_with_labels()
            return
        print("in onreleasetomove, self.dragInfo[Widget] is",self.dragInfo["Widget"])
        tags = self.mapPanel.gettags(self.dragInfo["Widget"])
        print("tags are ",tags)
        allwidgetsWithTag = self.mapPanel.find_withtag(tags[0])
        print("allwidgets with tag are", allwidgetsWithTag)
        self.mapPanel.itemconfigure(allwidgetsWithTag[0], outline="red")
        self.mapPanel.itemconfigure(allwidgetsWithTag[1], fill="black")
        self.mapPanel.itemconfigure(allwidgetsWithTag[2], fill="red")
        self.dragInfo["Widget"] = None
        self.dragInfo["xCoord"] = 0
        self.dragInfo["yCoord"] = 0

        self.mapPanel.unbind("<B1-Motion>")
        self.mapPanel.unbind("<ButtonRelease>")
        print("binding left and right in onrelease to move")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
        self.currentSite["Arms"][self.dragInfo["tag"]]["line coords"] = self.mapPanel.coords(allwidgetsWithTag[2])
        coords = self.mapPanel.coords(allwidgetsWithTag[0])
        self.currentSite["Arms"][self.dragInfo["tag"]]["coords"] = (coords[0]+self.armLabelRadius,coords[1]+self.armLabelRadius)
        self.dragInfo["tag"] = -1
        print("finished onreleasetomove")

    def onMovement(self, event):
        if self.dragInfo["tag"] == -1:
            return

        print("tag is",self.dragInfo["tag"])


        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("mouse is now at",winX,winY)
        newX = winX - self.dragInfo["xCoord"]
        newY = winY - self.dragInfo["yCoord"]

        if self.dragInfo["tag"] == "map":
            for child in self.mapPanel.find_all():
                self.mapPanel.move(child, newX, newY)
        else:

            for child in self.mapPanel.find_withtag(self.dragInfo["tag"]):
                self.mapPanel.move(child, newX, newY)
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY

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