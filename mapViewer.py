import tkinter
from tkinter import font
from PIL import Image,ImageDraw,ImageTk
import projectmanager
import numpy as np

class MapViewer(tkinter.Canvas):
    def __init__(self,master,width,height,surveyType):
        super(MapViewer, self).__init__(master=master,width=width,height=height,relief = tkinter.RAISED,borderwidth=2)
        self.activity = None
        self.surveyType = surveyType
        self.armLabelRadius = 15
        self.fontsize = 10
        self.controlDown = False
        self.currentArmLabel = "A"
        self.bind_all("<Control_L>", self.control_pressed)
        self.bind_all("<KeyRelease-Control_L>", self.control_released)
        self.bind("<Button-1>", self.left_mouse_clicked)
        self.bind_all("<Delete>", self.delete_arm)

    def control_pressed(self,event):
        self.controlDown = True

    def control_released(self,event):
        self.controlDown = False

    def set_site(self,site):
        self.site=site

    def display_site(self):
        self.site = site
        self.delete(tkinter.ALL)
        if self.surveyType not in site["surveys"]:
            return
        self.mapPanelImage = ImageTk.PhotoImage(site["surveys"][self.surveyType]["image"])
        self.create_image(5, 5, image=self.mapPanelImage, anchor=tkinter.NW, tags=("map",))
        arms = site["surveys"][self.surveyType]["Arms"]
        for label,arm in arms.items():
            #print("drawing", label, arm)
            self.draw_arm_label(label, arm["coords"][0], arm["coords"][1])
            self.draw_arm_line(label,arm["line vertices"])
            self.draw_arm_road_label(label)
            #e.bind("<FocusOut>", self.enable_arm_delete)

    def draw_arm_road_label(self,armName):
        coords = self.site["surveys"][self.surveyType]["Arms"][armName]["line vertices"]
        x1, y1, x2, y2 = coords[:4]
        dx = x1 - x2
        dy = y1 - y2
        orientation= self.site["surveys"][self.surveyType]["Arms"][armName]["orientation"]
        mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
        unit_x = dx / mag
        unit_y = dy / mag
        if orientation > 250 and orientation < 290:
            x = coords[0] + (100 * unit_x)
        elif orientation > 70 and orientation < 110:
            x = coords[0] + (100 * unit_x)
        else:
            x = coords[0] + (80 * unit_x)
        y = coords[1] + (80 * unit_y)
        e = tkinter.Entry(self, width=20)
        e.insert(0,"wibble road")
        #e.bind("<Return>", lambda event, x=self.currentTag: self.update_road_name(event, x))
        #e.bind("<FocusIn>", lambda event: self.disable_arm_delete(event, focus=True))
        #e.bind("<FocusOut>", self.enable_arm_delete)
        item = self.create_window((x, y), window=e,tags=[armName,"window"])
        window = self.nametowidget(self.itemcget(item,"window"))
        self.site["entry widget"] = item
        print("window is",window,type(window))
        for child in window.winfo_children():
            print(child,type(child))

    def draw_arm_label(self,armName,x,y):
        #print("Drawing a label at ",x,y)
        f = tkinter.font.Font(family='Helvetica', size=self.fontsize, weight=tkinter.font.BOLD)
        self.create_oval(x-self.armLabelRadius,y-self.armLabelRadius,x+self.armLabelRadius,y+self.armLabelRadius,width = 3,outline="red",tags=str(armName))
        self.create_text((x,y),text=armName,font=f,tags=str(armName))

    def draw_arm_line(self,armName,coords):
        coords = list(coords)
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
        coords[0] = newX
        coords[1]=newY
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
        print("coords are",coords)
        for index in range(0,len(coords[:-2]),2):
            print("drawing line segment",index,coords[index:index+4])
            self.create_line(coords[index:index+4], fill="red", width=3, tags=(armName, "line_" + str(index//2)))

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
                arm["road name"] = "wibble road"
                arm["entry widget coords"] = [x,y-20]
                arm["line vertices"] = [x,y,x+10,y+10]
                self.currentArmLabel = chr(ord(self.currentArmLabel) + 1)
                self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm] = arm
                self.display_site()
                self.bind("<Motion>", self.animate_line)
                #self.pick_up_line()
            else:
                selectedWidget = self.find_closest(event.x, event.y, halo=10)[0]
                tags = self.gettags(selectedWidget)
                print("tags of closest widget are",tags)
                allwidgetsWithTag = self.find_withtag(tags[0])
                self.currentSelectedArm = tags[0]
                print("tags of closest widget are",tags,allwidgetsWithTag)
                if "map" in tags:
                    return
                if len(tags) > 1 and "line" in tags[1]:
                    self.activity = "editing line"
                    self.selectedVertex = int(tags[1].split("_")[1]) + 1
                    self.currentSelectedArm = tags[0]
                    self.bind("<Motion>", self.animate_line)
                else:

                    # clicked a circle
                    print("clicked a circle")
                    self.activity = "circle"
                    self.bind("<B1-Motion>", self.on_movement)
                    self.bind("<ButtonRelease>", self.on_release_movement)
                    for widget in allwidgetsWithTag[1:-1]:
                        self.itemconfigure(widget, fill="blue")
                    self.itemconfigure(allwidgetsWithTag[0], outline="blue")

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
        armToDelete = chr(ord(self.currentArmLabel) - 1)
        if armToDelete in self.site["surveys"][self.surveyType]["Arms"]:
            del self.site["surveys"][self.surveyType]["Arms"][armToDelete]
            self.currentArmLabel = armToDelete
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
        if self.activity == "map":
            for child in self.find_all():
                self.move(child, newX, newY)
        else:
            for child in self.find_withtag(self.currentSelectedArm):
                self.move(child, newX, newY)
            self.widgetCoords = (winX, winY)

    def on_release_movement(self,event):
        allwidgetsWithTag = self.find_withtag(self.currentSelectedArm)
        print("num widgets,!",len(allwidgetsWithTag),allwidgetsWithTag)
        coords = self.coords(allwidgetsWithTag[1])
        for widget in allwidgetsWithTag[2:-1]:
            coords += self.coords(widget)[2:]
        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["coords"] = self.coords(allwidgetsWithTag[1])
        self.site["surveys"][self.surveyType]["Arms"][self.currentSelectedArm]["line vertices"] = coords
        self.display_site()
        self.activity = None
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease>")

site = projectmanager.load_project_from_pickle("test.pkl")
#site["surveys"]["J"]["Arms"]["A"] = {"coords":[100,100],"line vertices":[100,100,200,200],"road name":"Wibble road","entry widget coords":[50,50]}

print("site is",site)
win = tkinter.Tk()
canvas = MapViewer(win,800,800,"J")
canvas.grid(row=0,column=0)
canvas.set_site(site)
canvas.display_site()
win.mainloop()
projectmanager.save_project_to_pickle("test.pkl")