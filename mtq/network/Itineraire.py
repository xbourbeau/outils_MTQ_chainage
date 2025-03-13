
class Road:
    def __init__(self, geom, atts={}):
        self.setGeometry(geom)
        self.setAttributs(atts)

    def setGeometry(self, geom):
        self.geom = geom

    def setAttributs(self, atts):
        self.atts = atts

    def attributs(self): return self.atts

    def geometry(self): return self.geom

class Itineraire:

    def __init__(self, list_roads:list=[]):
        self.list_roads = list_roads

    def addRoad(self, road:Road):
        self.list_roads.append(road)

