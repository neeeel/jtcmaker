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
        self.mapPanelHasFocus = False
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)

        tkinter.Label(self, text="Job Details", font=f, fg=self.tracsisBlue).grid(row=0, column=0)
        self.detailsPanel = tkinter.Frame(self,relief=tkinter.GROOVE,borderwidth=2)
        tkinter.Label(self.detailsPanel,text = "Client",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =0,column=0)
        tkinter.Label(self.detailsPanel,text = "Job No",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =1,column=0)
        tkinter.Label(self.detailsPanel,text = "Survey Date",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =2,column=0)
        tkinter.Label(self.detailsPanel,text = "Times",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =3,column=0)
        tkinter.Label(self.detailsPanel,text = "Period",anchor=tkinter.E,width = 12,fg = self.tracsisBlue).grid(row =4,column=0)

        self.clientVar = tkinter.StringVar()
        self.jobVar = tkinter.StringVar()
        self.surveyDateVar = tkinter.StringVar()
        self.timesVar = tkinter.StringVar()

        tkinter.Entry(self.detailsPanel,textvariable = self.clientVar).grid(row =0,column=1)
        tkinter.Entry(self.detailsPanel, textvariable=self.jobVar).grid(row =1,column=1)
        tkinter.Entry(self.detailsPanel, textvariable=self.surveyDateVar).grid(row =2,column=1)
        tkinter.Entry(self.detailsPanel, textvariable=self.timesVar).grid(row =3,column=1)
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
        self.winSpawned = False
        self.detailsPanel.grid(row=1,column=0)


        self.currentSite = projectmanager.load_project()
        self.focus_force()
        self.armLine = None
        tkinter.Label(self, text="Overview", font=f,fg=self.tracsisBlue).grid(row=2,column=0)
        self.mapLabel = tkinter.Label(self,text = self.currentSite["Site Name"],font=f,fg=self.tracsisBlue)
        self.mapLabel.grid(row = 0,column = 1)
        tkinter.Button(self,text="Export",command=self.export_to_excel).grid(row=4,column=0)
        frame = tkinter.Frame(self)
        tkinter.Button(frame, text="+", command=lambda:self.change_site_zoom("+"),width = 4,height = 2).grid(row=0, column=0,padx = 5)
        tkinter.Button(frame, text="-", command=lambda:self.change_site_zoom("-"),width = 4,height = 2).grid(row=0, column=1)
        frame.grid(row = 4,column=1)
        self.overviewPanel = tkinter.Canvas(self,bg="white",relief=tkinter.RAISED,borderwidth=1)
        self.overviewPanel.grid(row = 3,column = 0)
        self.addingArmLabel = False
        self.armLineStartingCoords = None
        self.armList = []
        self.mapPanel.grid(row=1,column=1,rowspan=3)
        self.mapPanel.bind("<Double-Button-1>",self.add_arm_icon)
        self.mapPanel.bind("<Button-1>",self.on_press_to_move)
        self.mapPanel.bind("<ButtonRelease>",self.onReleaseToMove)
        print("binding left and right")
        self.bind("<Left>",self.decrement_map)
        self.bind("<Right>", self.increment_map)
        self.mapPanel.bind("<Enter>",self.mouse_over_map_panel)
        self.mapPanel.bind("<Leave>",self.mouse_leave_map_panel)

        self.load_map_panel_map(self.currentSite["Site Name"])
        self.load_overview_map()
        self.currentTag = ""
        self.dragInfo = {}


    ##########################################################################################################################
    ###
    ### Functions to deal with the overview panel, defining and selecting groups
    ###


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
    ### methods to deal with the site maps,
    ###

    def change_site_zoom(self,value):
        projectmanager.change_site_zoom(self.currentSite["Site Name"],value)
        self.load_map_panel_map(self.currentSite["Site Name"])

    def export_to_excel(self):
        jobDetails = {}
        try:
            surveyDate = datetime.datetime.strptime(self.surveyDateVar.get(),"%d/%m/%y")
        except Exception as e:
            messagebox.showinfo(message = "Incorrect format for survey date,must be in format dd/mm/yy")
            return
        times  =self.timesVar.get().split(",")
        for t in times:
            if "-" not in t:
                messagebox.showinfo(message = "Incorrect format for times. Must be in format hh:mm-hh:mm, with multiple time periods separated by commas")
                return
            result = t.split("-")
            for r in result:
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

    def get_nearest_site(self,x,y):
        pass

    def increment_map(self,event):
        print("pressed right arrow")
        self.currentSite = projectmanager.load_next_site(self.currentSite["Site Name"])
        self.mapPanel.delete(tkinter.ALL)
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.mapLabel.configure(text =self.currentSite["Site Name"] )
        self.armLineStartingCoords = None
        self.armList = []
        self.currentTag = ""
        self.dragInfo = {}
        for key,item in self.currentSite["Arms"].items():
            self.draw_arm_label(key,item["coords"][0],item["coords"][1])
            self.redraw_arm_line(item["line coords"])
            self.armList.append(key)

    def decrement_map(self,event):
        print("pressed left arrow")
        self.currentSite = projectmanager.load_previous_site(self.currentSite["Site Name"])
        self.mapPanel.delete(tkinter.ALL)
        self.load_map_panel_map(self.currentSite["Site Name"])
        self.mapLabel.configure(text=self.currentSite["Site Name"])
        self.armLineStartingCoords = None
        self.armList = []
        self.currentTag = ""
        self.dragInfo = {}
        for key,item in self.currentSite["Arms"].items():
            self.draw_arm_label(key,item["coords"][0],item["coords"][1])
            self.redraw_arm_line(item["line coords"])
            self.armList.append(key)

    def load_overview_map(self):
        self.overviewImage = projectmanager.get_overview_map()
        self.overviewPanel.create_image(5, 5, image=self.overviewImage, anchor=tkinter.NW, tags=("map",))
        self.overviewPanel.configure(width=400, height=400)

    def load_map_panel_map(self,siteName):
        self.mapPanelImage = projectmanager.get_site_map(siteName)
        self.mapPanel.create_image(5, 5, image=self.mapPanelImage, anchor=tkinter.NW,tags=("map",))
        self.mapPanel.configure(width=self.mapPanelSize,height=self.mapPanelSize)

    def load_overview_panel_map(self):
        pass

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
        self.mapPanel.bind("<Button-1>",self.finish_arm_line)
        self.mapPanel.bind("<Motion>",self.draw_arm_line)
        self.unbind_all("<BackSpace>")
        self.unbind_all("<Delete>")
        print("unbinding left and right in add arm icon")
        self.unbind("<Left>")
        self.unbind("<Right>")
        print("unbopiunnd")
        #self.update()
        self.armLineStartingCoords = (x,y)
        self.armList.append(armName)
        print("armlist is",self.armList)

    def draw_arm_label(self,armName,x,y):
        print("Drawing a label at ",x,y)
        f = tkinter.font.Font(family='Helvetica', size=self.fontsize, weight=tkinter.font.BOLD)
        self.mapPanel.create_oval(x-self.armLabelRadius,y-self.armLabelRadius,x+self.armLabelRadius,y+self.armLabelRadius,width = 3,outline="red",tags=str(armName))
        self.mapPanel.create_text((x,y),text=armName,font=f,tags=str(armName))
        self.currentTag = str(armName)

    def redraw_arm_line(self,lineCoords):
        self.mapPanel.create_line(lineCoords, fill="red", width=3, tags=(self.currentTag, "line"))

    def delete_most_recent_arm(self,event):
        if self.mapPanelHasFocus:
            if self.armList == []:
                return
            armName = (self.armList.pop(-1))
            self.mapPanel.delete(armName)
            projectmanager.delete_arm_from_site(self.currentSite["Site Name"],armName)
            projectmanager.decrement_arm_label()

    def draw_arm_line(self,event):
        print("unbinding left and right in draw arm line")
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

    def finish_arm_line(self,event):
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        self.mapPanel.unbind("<Motion>")
        self.mapPanel.bind("<Double-Button-1>", self.add_arm_icon)
        self.mapPanel.bind("<Button-1>", self.on_press_to_move)
        print("binding left and right in finish arm line")
        self.bind("<Left>", self.decrement_map)
        self.bind("<Right>", self.increment_map)
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
        #self.focus_set()

    def on_press_to_move(self,event):
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("clicked at", winX, winY)
        closest_widgets = self.mapPanel.find_closest(event.x, event.y, halo=10)
        for w in closest_widgets:
            print("widget",w)
            print("tags for closest item are",self.mapPanel.gettags(w))
        self.dragInfo["Widget"] = self.mapPanel.find_closest(event.x, event.y, halo=10)[0]
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY
        tags = self.mapPanel.gettags(self.dragInfo["Widget"])
        allwidgetsWithTag = self.mapPanel.find_withtag(tags[0])
        print("allwidgets with tag are",allwidgetsWithTag)
        print(tags)
        print("unbinding left and right in on press to move")
        self.unbind("<Left>")
        self.unbind("<Right>")
        if "line" in (tags):
            print("allwidgets with tag",tags[0],allwidgetsWithTag)
            self.armLine = self.dragInfo["Widget"]
            self.mapPanel.bind("<Motion>", self.draw_arm_line)
            self.mapPanel.bind("<Button-1>", self.finish_arm_line)
            self.mapPanel.unbind_all("<ButtonRelease>")

        else:
            if "map" in tags:
                print("clicked on the map")
                self.dragInfo["tag"] = -1
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
        print("released mouse")
        if self.dragInfo["tag"] == -1:
            #print("binding")
            self.bind("<Left>", self.decrement_map)
            self.bind("<Right>", self.increment_map)
            return
        print("blah")
        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("in releasetomove",winX,winY)

        tags = self.mapPanel.gettags(self.dragInfo["Widget"])
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
        #projectmanager.edit_arm(self.currentSite["Site Name"], self.currentTag, winX, winY)
        self.currentSite["Arms"][self.dragInfo["tag"]]["line coords"] = self.mapPanel.coords(allwidgetsWithTag[2])
        coords = self.mapPanel.coords(allwidgetsWithTag[0])
        self.currentSite["Arms"][self.dragInfo["tag"]]["coords"] = (coords[0]+self.armLabelRadius,coords[1]+self.armLabelRadius)
        print("coords of circle are now",self.currentSite["Arms"][self.dragInfo["tag"]]["coords"])
        #self.mapPanel.focus_set()
        self.dragInfo["tag"] = -1

    def onMovement(self, event):
        if self.dragInfo["tag"] == -1:
            return
        print("tag is",self.dragInfo["tag"])

        print(self.mapPanel.find_withtag("one"))
        print(self.mapPanel.find_withtag(tkinter.CURRENT))

        winX = event.x - self.mapPanel.canvasx(0)
        winY = event.y - self.mapPanel.canvasy(0)
        print("mouse is now at",winX,winY)
        newX = winX - self.dragInfo["xCoord"]
        newY = winY - self.dragInfo["yCoord"]
        for child in self.mapPanel.find_withtag(self.dragInfo["tag"]):
            self.mapPanel.move(child, newX, newY)
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY

    ########################################################################################################

class DragAndZoomCanvas(tkinter.Canvas):

    def __init__(self):
        super(DragAndZoomCanvas, self).__init__()
        self.baseImage = None
        self.zoom = 0


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