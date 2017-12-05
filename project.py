

class Site():
    def __init__(self, name,surveyType, coords):
        self.name = name
        self.surveyType = surveyType
        self.arms = {}
        self.coords = coords


    def add_image(self,image):
        self.image = image

    def set_zoom(self,zoom):
        self.zoom = zoom


class Arm():
    def __init__(self, label):
        self.label = label
