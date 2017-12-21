import tkinter
from tkinter import font
from PIL import Image,ImageDraw,ImageTk
import projectmanager
import mapmanager
import numpy as np
import math

class MapViewer(tkinter.Canvas):
    def __init__(self,master,width,height,surveyType):
        super(MapViewer, self).__init__(master=master,width=width,height=height,relief = tkinter.RAISED,borderwidth=2)
        self.activity = None
        self.surveyType = surveyType
        self.armLabelRadius = 15
        self.fontsize = 10
        self.controlDown = False
        self.currentArmLabel = "A"
        self.bind("<Button-1>", self.left_mouse_clicked)
        self.bind_all("<Delete>", self.delete_arm)
        self.bind("<Enter>",self.mouse_hovered)
        self.bind("<Leave>", self.mouse_left)
        self.bind("<Visibility>", lambda event:self.bind_control())
        self.width = width
        self.height = height
        self.mapWidthInPixels=640


    def mouse_hovered(self,event):
        print("mouse entered")
        self.bind_all("<Delete>", self.delete_arm)

    def mouse_left(self,event):
        print("mouse left")
        self.unbind_all("<Delete>")
        self.unbind_all("<Escape>")

    def bind_control(self):
        self.bind_all("<Control_L>", self.control_pressed)
        self.bind_all("<KeyRelease-Control_L>", self.control_released)

    def unbind_control(self):
        self.unbind_all("<Control_L>")
        self.unbind_all("<KeyRelease-Control_L>")

    def control_pressed(self,event):
        self.controlDown = True
        #print("control pressed in ",self.surveyType," self.controlDown is",self.controlDown)

    def control_released(self,event):
        self.controlDown = False
        #print("control released in ",self.surveyType," self.controlDown is",self.controlDown)

    def set_site(self,site):
        self.site=site
        label = "A"
        numArms = len(self.site["surveys"][self.surveyType]["Arms"].items())
        self.currentArmLabel = chr(ord(self.currentArmLabel) + numArms)
        self.metresPerPixel=metres_per_pixel(self.site["surveys"][self.surveyType]["latlon"][0],self.site["surveys"][self.surveyType]["zoom"])

    def display_site(self):
        #self.delete(tkinter.ALL)
        for child in self.find_all():
            tags = self.gettags(child)
            print("tags are",tags)
            if "window" not in tags and "header" not in tags:
                self.delete(child)
        if self.surveyType not in self.site["surveys"]:
            return
        self.mapPanelImage = ImageTk.PhotoImage(self.site["surveys"][self.surveyType]["image"])
        map = self.create_image(5, 5, image=self.mapPanelImage, anchor=tkinter.NW, tags=("map",))
        self.lower(map)
        arms = self.site["surveys"][self.surveyType]["Arms"]
        for label,arm in arms.items():
            print("drawing", label, arm)
            self.draw_arm_label(label, arm["coords"][0], arm["coords"][1])
            self.draw_arm_line(label,arm["line vertices"])
            self.draw_arm_road_label(label)

    def draw_arm_road_label(self,armName):
        coords = self.site["surveys"][self.surveyType]["Arms"][armName]["line vertices"]
        if self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget coords"] is None:
            x1, y1, x2, y2 = coords[:4]
            dx = x1 - x2
            dy = y1 - y2
            orientation= self.site["surveys"][self.surveyType]["Arms"][armName]["orientation"]
            print("orientation is",orientation)
            mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
            unit_x = dx / mag
            unit_y = dy / mag
            ###
            ### swap unit vectors about to get perpendicular vector
            ###
            #temp = unit_y
           #unit_y = -unit_x
            #unit_x = temp

            if orientation > 250 and orientation < 350:
                x = coords[0] + (150 * unit_x)
            elif orientation > 70 and orientation < 110:
                x = coords[0] + (100 * unit_x)
            else:
                x = coords[0] + (80 * unit_x)
            y = coords[1] + (120 * unit_y)
        else:
            x,y = self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget coords"]
        if self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"] is None:
            print("adding new widget")
            frame = tkinter.Frame()
            l = tkinter.Label(frame, text="ARM " + armName)
            l.grid(row=0, column=0,columnspan = 2,sticky="nsew")
            e = tkinter.Entry(frame, width=20)
            e.insert(0,self.site["surveys"][self.surveyType]["Arms"][armName]["road name"])
            e.grid(row=1,column=0,columnspan=2,sticky="nsew")
            #l.bind("<Button-1>",lambda event,label=armName:self.pick_up_window(event,label))
            spinCommand = self.register(lambda w,d,l=armName:self.spinbutton_pressed(w,d,l))
            if self.surveyType == "Q":
                tkinter.Label(frame,text="Lanes").grid(row=2,column=0)
                s = tkinter.Spinbox(frame,command=(spinCommand,'%W', '%d'),from_=1, to=6,width=2)
                s.grid(row=2,column=1)
                s.delete(0, tkinter.END)
                s.insert(0, self.site["surveys"][self.surveyType]["Arms"][armName]["lanes"])
                lineLength = length_of_line_in_pixels(coords)
                length = round(self.mapWidthInPixels * lineLength * self.metresPerPixel/self.width,2)
                tkinter.Label(frame,text=str(length) + "m").grid(row=3,column=0,columnspan=2)
            e.bind("<Return>", lambda event, x=armName: self.edit_road_name(event, x))
            e.bind("<FocusIn>", self.unbind_delete)
            e.bind("<FocusOut>", lambda event, x=armName:self.display_current_road_name(event,x))
            item = self.create_window((x, y), window=frame,tags=(armName,"window"),anchor=tkinter.NW)
            print("item is",item)
            frame.update()
            self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"] = item
            self.create_line((x,y,x+frame.winfo_reqwidth(),y), fill="black", width=23,tags = [armName,"header"])
        else:
            item = self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"]
            currentCoords = self.coords(item)
            dx = x -currentCoords[0]
            dy = y - currentCoords[1]
            self.move_widget(armName,dx,dy)

    def spinbutton_pressed(self,widget,dir,armName):
        widget = self.nametowidget(widget)
        print(widget,dir,widget.get(),armName)
        self.site["surveys"][self.surveyType]["Arms"][armName]["lanes"] = int(widget.get())

    def clear_all(self):
        self.delete(tkinter.ALL)

    def lanes_changed(self,varname,elementname,mode):
        print(varname.get(),elementname,mode)

    def unbind_delete(self,event):
        event.widget.config(bg="white")
        self.unbind_all("<Delete>")

    def edit_road_name(self,event,armName):
        self.site["surveys"][self.surveyType]["Arms"][armName]["road name"] = event.widget.get()
        event.widget.config(bg = "light blue")
        self.bind_all("<Delete>", self.delete_arm)
        self.focus_force()

    def display_current_road_name(self,event,armName):
        event.widget.delete(0,"end")
        event.widget.insert(0,self.site["surveys"][self.surveyType]["Arms"][armName]["road name"])

    def draw_arm_label(self,armName,x,y):
        #print("Drawing a label at ",x,y)
        f = tkinter.font.Font(family='Helvetica', size=self.fontsize, weight=tkinter.font.BOLD)
        self.create_oval(x-self.armLabelRadius,y-self.armLabelRadius,x+self.armLabelRadius,y+self.armLabelRadius,width = 3,outline="red",tags=(str(armName),"circle"))
        self.create_text((x,y),text=armName,font=f,tags=(str(armName),"textlabel"))

    def draw_arm_line(self,armName,coords):
        coords = list(coords)
        print("coords are",coords)
        x1,y1,x2,y2 = coords[:4]
        centre_X = x1 #+ 15
        centre_Y = y1 #+ 15
        dx = x2 - centre_X
        dy = y2 - centre_Y
        if dy != 0:
            theta = np.arctan(dx / dy)
            offsetX = self.armLabelRadius * np.sin(theta)
        else:
            theta = 1
            if dx != 0:
                offsetX=(dx/abs(dx))*15
            else:
                offsetX = 15
        if dx != 0:
            if dy != 0:
                theta = np.arctan(dx / dy)
                offsetY = offsetX / np.tan(theta)
            else:
                offsetY = 0
        else:
            offsetY = 15
        if y2 >= centre_Y:
            newY = centre_Y + offsetY
            newX = centre_X + offsetX
        else:
            newY = centre_Y - offsetY
            newX = centre_X - offsetX
        #coords[0] = newX
        #coords[1]=newY
        if theta == 1 and dx < 0:
            orientation = 90
        elif theta == 1 and dx > 0:
            orientation = 270
        elif theta == 0.0 and dy > 0:
            orientation = 0
        elif theta == -0.0 and dy < 0:
            orientation = 180
        elif dx<0 and dy>0:
            orientation =-np.degrees(theta)
        elif dx<0 and dy<0:
            orientation = 90 + (90-np.degrees(theta))
        elif dx>0 and dy<0:
            orientation = 180 - np.degrees(theta)
        elif dx>0 and dy>0:
            orientation = 270 + (90-np.degrees(theta))
        self.site["surveys"][self.surveyType]["Arms"][armName]["orientation"] = orientation
        #print("coords are",coords)
        self.create_line([newX,newY,coords[2],coords[3]], fill="red", width=3, tags=(armName, "line_0" ))
        for index in range(2,len(coords[:-2]),2):
            #print("drawing line segment",index,coords[index:index+4])
            self.create_line(coords[index:index+4], fill="red", width=3, tags=(armName, "line_" + str(index//2)))
        if self.surveyType == "Q":
            lineLength = length_of_line_in_pixels(coords)
            length = round(self.mapWidthInPixels * lineLength * self.metresPerPixel / self.width, 2)
            if not self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"] is None:
                window = self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"]
                window = self.nametowidget(self.itemcget(window,"window"))
                print("type of window is",window,type(window))
                for child in window.winfo_children():
                    print(child,type(child))
                window.winfo_children()[4].config(text = str(length) + "m")

    def move_widget(self,armName,dx,dy):
        if not self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"] is None:
            item = self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget"]
            self.move(item,dx,dy)
            for child in self.find_withtag(armName):

                tags = self.gettags(child)
                #print("tags are", tags)
                if "header" in tags :
                    self.move(child,dx,dy)
            #self.site["surveys"][self.surveyType]["Arms"][armName]["entry widget coords"] = self.coords(item)

    def left_mouse_clicked(self,event):
        print("self.activity is",self.activity,"control down is",self.controlDown)
        x = event.x - self.canvasx(0)
        y = event.y - self.canvasy(0)
        if self.activity is None:
            if self.controlDown:
                self.activity = "drawing line"
                self.currentSelectedArm = self.currentArmLabel
                self.selectedVertex = 1
                arm = {}
                arm["coords"] = [x,y]
                armLatLon = mapmanager.get_lat_lon_from_x_y(self.site["surveys"][self.surveyType]["latlon"], x, y, self.site["surveys"][self.surveyType]["zoom"])
                arm["road name"] = mapmanager.get_road_name(armLatLon[0], armLatLon[1])
                arm["entry widget coords"] = None
                arm["line vertices"] = [x,y,x+10,y+10]
                arm["lanes"] = 1
                self.currentArmLabel = chr(ord(self.currentArmLabel) + 1)
                self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm] = arm
                self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["entry widget"] = None
                self.display_site()
                self.bind("<Motion>", self.animate_line)
                #self.pick_up_line()
            else:
                selectedWidget = self.find_closest(event.x, event.y, halo=10)
                if len(selectedWidget) == 0:
                    return
                for widget in selectedWidget:
                    print("tags for selected widget are",self.gettags(widget))
                selectedWidget = selectedWidget[0]
                tags = self.gettags(selectedWidget)
                print("tags of closest widget are",tags)
                allwidgetsWithTag = self.find_withtag(tags[0])
                self.currentSelectedArm = tags[0]
                print("tags of closest widget are",tags,allwidgetsWithTag)
                if "map" in tags:
                    return
                if len(tags) > 1 and "line" in tags[1]:
                    print("clicked a line")
                    self.activity = "editing line"
                    self.selectedVertex = int(tags[1].split("_")[1]) + 1
                    self.currentSelectedArm = tags[0]
                    self.bind("<Motion>", self.animate_line)
                if len(tags) > 1 and "header" in tags:
                    print("found window")
                    self.activity = "moving window"
                    self.bind("<B1-Motion>", self.on_movement)
                    self.bind("<ButtonRelease>", self.on_release_movement)
                    self.widgetCoords = self.coords(selectedWidget)
                if len(tags) > 1 and ("circle" in tags[1] or "textlabel" in tags[1]):
                    # clicked a circle
                    print("clicked a circle")
                    self.activity = "circle"
                    self.bind("<B1-Motion>", self.on_movement)
                    self.bind("<ButtonRelease>", self.on_release_movement)
                    for widget in allwidgetsWithTag:
                        tags = self.gettags(widget)
                        #print("tags are",tags)
                        if "circle" in tags:
                            self.itemconfigure(widget, outline="blue")
                        elif "header" in tags:
                            self.itemconfigure(widget, fill="black")
                        elif not "window" in tags:
                            self.itemconfigure(widget, fill="blue")


                    self.widgetCoords = self.coords(selectedWidget)
                    print("widgetcoords are",self.widgetCoords)
                #self.itemconfigure(allwidgetsWithTag[2], fill="blue")
        else:
            if self.activity == "drawing line":
                print("clicked while drawing line active")
                self.selectedVertex+=1
                if not self.controlDown:
                    self.activity = None
                    self.unbind("<Motion>")
                else:
                    self.bind_all("<Escape>",self.stop_line)
                    self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] = self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] + [x,y]
            if self.activity == "editing line":
                self.activity = None
                self.unbind("<Motion>")

    def delete_arm(self,event):
        #print("delete pressed")
        armToDelete = chr(ord(self.currentArmLabel) - 1)
        if armToDelete in self.site["surveys"][self.surveyType]["Arms"]:
            self.delete(self.site["surveys"][self.surveyType]["Arms"][armToDelete]["entry widget"])
            del self.site["surveys"][self.surveyType]["Arms"][armToDelete]
            self.currentArmLabel = armToDelete
            self.delete(armToDelete)
            self.display_site()
            self.activity = None

    def stop_line(self,event):
        print("Escape pressed")
        self.activity = None
        self.unbind("<Motion>")
        self.unbind_all("<Escape>")
        print("vertices are",self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"])
        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] = \
        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"][:-2]
        self.display_site()

    def animate_line(self,event):
        winX = event.x - self.canvasx(0)
        winY = event.y - self.canvasy(0)
        coords = self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"]
        print("in animate line, coords are",coords,"selected vertex is",self.selectedVertex)
        coords[2*self.selectedVertex] = winX
        coords[(2*self.selectedVertex) + 1] = winY
        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] = coords
        self.display_site()

    def on_movement(self,event):
        winX = event.x - self.canvasx(0)
        winY = event.y - self.canvasy(0)
        newX = winX - self.widgetCoords[0]
        newY = winY - self.widgetCoords[1]
        #print("activity is",self.activity)
        if self.activity == "map":
            for child in self.find_all():
                self.move(child, newX, newY)
        elif self.activity == "moving window":
            #print("moving wuindow")
            for child in self.find_withtag(self.currentSelectedArm):
                tags = self.gettags(child)
                #print("tags are", tags)
                if "header" in tags or "window" in tags:
                    self.move(child,newX,newY)
        else:
            for child in self.find_withtag(self.currentSelectedArm):
                self.move(child, newX, newY)
        self.widgetCoords = (winX, winY)

    def on_release_movement(self,event):
        if self.activity == "circle":
            print("_"*100)
            allwidgetsWithTag = self.find_withtag(self.currentSelectedArm)
            linecoords = []
            for widget in allwidgetsWithTag:
                tags = self.gettags(widget)
                print("tags are",tags)
                if "textlabel" in tags:
                    #print("coords of textlabel are",self.coords(widget))
                    self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["coords"] = self.coords(widget)
                    linecoords = list(self.coords(widget))
                    #print("line coords are",linecoords)
                for tag in tags:
                    if "line" in tag:
                        linecoords+=(self.coords(widget)[2:])
                        #print("line coords are", linecoords)
                    if tag == "window" and not self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["entry widget coords"] is None:
                        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["entry widget coords"] = self.coords(widget)

            self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] = linecoords
            self.display_site()
        if self.activity == "moving window":
            allwidgetsWithTag = self.find_withtag(self.currentSelectedArm)
            for widget in allwidgetsWithTag:
                tags = self.gettags(widget)
                if "window" in tags:
                    self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["entry widget coords"] = self.coords(widget)
        self.activity = None
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease>")

def metres_per_pixel(lat, zoom):
    return 156543.03 * math.cos(math.radians(lat)) / 2 ** (zoom)

def length_of_line_in_pixels(coords):
    if len(coords) < 4:
        return 0
    length = 0
    for i in range(0,len(coords)-2,2):
        x1,y1,x2,y2 = coords[i:i+4]
        length+= ((x1-x2)**2 + (y1-y2)**2)**0.5
    return length





site = projectmanager.load_project_from_pickle("test.pkl")
#site["surveys"]["J"]["Arms"]["A"] = {"coords":[100,100],"line vertices":[100,100,200,200],"road name":"Wibble road","entry widget coords":None,"entry widget":None}######
print("site is",site)
#win = tkinter.Tk()
#canvas = MapViewer(win,800,800,"J")
#canvas.grid(row=0,column=0)
#canvas.set_site(site)
#canvas.display_site()
#win.mainloop()
#projectmanager.save_project_to_pickle("test.pkl")