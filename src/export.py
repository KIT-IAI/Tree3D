import xml.etree.ElementTree as ET


class CityGmlExport:
    def __init__(self, savepath, dataobj):
        self.__db = dataobj
        self.__columns = self.__db.get_column_names()

        self.__filepath = savepath
        self.__root = None

        self.__data = self.__db.get_data()

        self.__x_value_col_index = None
        self.__y_value_col_index = None

    def export(self):
        self.__root = ET.Element("core:CityModel")
        self.add_namespaces()

        self.bounded_by()

        for row in self.__data:
            cityObjectMember = ET.SubElement(self.__root, "core:cityObjectMember")

            SolitaryVegetationObject = ET.SubElement(cityObjectMember, "veg:SolitaryVegetationObject")

        CityGmlExport.indent(self.__root)
        tree = ET.ElementTree(self.__root)
        tree.write(self.__filepath, encoding="UTF-8", xml_declaration=True, method="xml")

    def add_namespaces(self):
        self.__root.set("xmlns:xs", "https://www.w3.org/2001/XMLSchema")
        self.__root.set("xmlns:core", "http://www.opengis.net/citygml/2.0")
        self.__root.set("xmlns:gml", "http://www.opengis.net/gml")

    def bounded_by(self):

        xMinValue = float("inf")
        xMaxValue = 0
        yMinValue = float("inf")
        yMaxValue = 0
        for row in self.__data:
            xValue = row[self.__x_value_col_index]
            yValue = row[self.__y_value_col_index]

            if xValue < xMinValue:
                xMinValue = xValue

            if xValue > xMaxValue:
                xMaxValue = xValue

            if yValue < yMinValue:
                yMinValue = yValue

            if yValue > yMaxValue:
                yMaxValue = yValue

        print("Min: ", xMinValue, yMinValue)
        print("Max: ", xMaxValue, yMaxValue)

        envelope = ET.SubElement(self.__root, "gml:Envelope")

        lower_corner = ET.SubElement(envelope, "gml:lowerCorner")
        upper_corner = ET.SubElement(envelope, "gml:upperCorner")

        lower_corner.text = "{0:.2f} {1:.2f}".format(xMinValue, yMinValue)
        upper_corner.text = "{0:.2f} {1:.2f}".format(xMaxValue, yMaxValue)

    # Prints a tree with each node indented according to its depth.
    # This is done by first indenting the tree (see below), and then serializing it as usual.
    # method copied from http://effbot.org/zone/element-lib.htm#prettyprint
    @staticmethod
    def indent(elem, level=0):
        i = "\n" + level * "\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                CityGmlExport.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def set_x_col_idx(self, idx):
        self.__x_value_col_index = idx

    def set_y_col_idx(self, idx):
        self.__y_value_col_index = idx
