import xml.etree.ElementTree as ET


class CityGmlExport:
    def __init__(self, savepath, dataobj):
        self.__db = dataobj  # db object from specialized_gui.MainTableFrame

        self.__filepath = savepath  # output file path (where citygml will be saved)
        self.__root = None  # ElementTree Root Node

        self.__data = self.__db.get_data()  # Data table from database (list of lists)

        self.__x_value_col_index = None  # index of column in which x value is stored
        self.__y_value_col_index = None  # index of column in which y value is stored
        self.__EPSG = None  # EPSG-Code of coordinates
        self.__EPSG_output = None  # EPSG-Code of coordinates in output
        self.__height_col_index = None  # index of height column
        self.__trunk_diam_col_index = None  # index of trunk diameter column
        self.__crown_diam_col_index = None  # index of crown diameter column
        self.__species_col_index = None  # index of species column

    def export(self):
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        self.bounded_by()

        for row in self.__data:
            cityObjectMember = ET.SubElement(self.__root, "cityObjectMember")

            SolitaryVegetationObject = ET.SubElement(cityObjectMember, "veg:SolitaryVegetationObject")

        CityGmlExport.indent(self.__root)
        tree = ET.ElementTree(self.__root)
        tree.write(self.__filepath, encoding="UTF-8", xml_declaration=True, method="xml")

    def add_namespaces(self):
        self.__root.set("xmlns", "http://www.opengis.net/citygml/2.0")
        self.__root.set("xmlns:xs", "https://www.w3.org/2001/XMLSchema")
        self.__root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self.__root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
        self.__root.set("xmlns:gml", "http://www.opengis.net/gml")
        self.__root.set("xmlns:veg", "http://www.opengis.net/citygml/vegetation/2.0")
        self.__root.set("xsi:schemaLocation",
                        "http://www.opengis.net/citygml/vegetation/2.0 "
                        "http://schemas.opengis.net/citygml/vegetation/2.0/vegetation.xsd")

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

        boundedby = ET.SubElement(self.__root, "gml:boundedBy")
        envelope = ET.SubElement(boundedby, "gml:Envelope")

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

    def set_EPSG(self, epsg_code):
        self.__EPSG = epsg_code

    def set_EPSG_output(self, epsg_code):
        self.__EPSG_output = epsg_code

    def set_height_col_index(self, idx):
        self.__height_col_index = idx

    def set_trunk_diam_col_index(self, idx):
        self.__trunk_diam_col_index = idx

    def set_crown_diam_col_index(self, idx):
        self.__crown_diam_col_index = idx

    def set_species_col_index(self, index):
        self.__species_col_index = index
