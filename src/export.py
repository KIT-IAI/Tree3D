import xml.etree.ElementTree as ET
import math
from datetime import date

import default_gui
import analysis

import wx


class ExportDialog(default_gui.CityGmlExport):
    def __init__(self, parent):
        default_gui.CityGmlExport.__init__(self, parent)
        self.__pathname = ""

        self.populate_dropdown()

        self.DoLayoutAdaptation()
        self.Layout()

        self.progress.SetRange(self.GetParent().db.get_number_of_tablerecords())

        self.ShowModal()

    # method to populate dropdown menus in export window
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.choiceXvalue.SetItems(colitemlist)
        self.choiceYvalue.SetItems(colitemlist)
        self.choiceHeight.SetItems(colitemlist)
        self.choiceTrunk.SetItems(colitemlist)
        self.choiceCrown.SetItems(colitemlist)
        self.choiceSpecies.SetItems(colitemlist)

    # method to be called when "Browse" button is pushed
    def on_browse(self, event):
        with wx.FileDialog(self, "Export as CityGML", wildcard="CityGML (*.citygml)|*.citygml",
                           style=wx.FD_SAVE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.__pathname = fileDialog.GetPath()

        self.filepat_textbox.SetValue(self.__pathname)

    # method to be called when "export" button is pressed in export-window
    def on_export(self, event):
        if not self.validate_input():
            return

        exporter = CityGmlExport(self.__pathname, self.GetParent().db)

        exporter.set_prettyprint(self.box_prettyprint.GetValue())

        if self.choiceXvalue.GetSelection() != wx.NOT_FOUND:
            exporter.set_x_col_idx(self.choiceXvalue.GetSelection())

        if self.choiceYvalue.GetSelection() != wx.NOT_FOUND:
            exporter.set_y_col_idx(self.choiceYvalue.GetSelection())

        if self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            exporter.set_height_col_index(self.choiceHeight.GetSelection())
            exporter.set_height_unit(self.choiceHeightUnit.GetString(self.choiceHeightUnit.GetSelection()))

        if self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
            exporter.set_trunk_diam_col_index(self.choiceTrunk.GetSelection())
            exporter.set_trunk_diam_unit(self.choiceTrunkUnit.GetString(self.choiceTrunkUnit.GetSelection()))
            trunk_circ = self.trunk_circ.GetSelection()
            if trunk_circ == 1:
                exporter.set_trunk_is_circ(True)

        if self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            exporter.set_crown_diam_col_index(self.choiceCrown.GetSelection())
            exporter.set_crown_diam_unit(self.choiceCrownUnit.GetString(self.choiceCrownUnit.GetSelection()))
            crown_circ = self.crown_circ.GetSelection()
            if crown_circ == 1:
                exporter.set_crown_is_circ(True)

        if self.choiceSpecies.GetSelection() != wx.NOT_FOUND:
            exporter.set_species_col_index(self.choiceSpecies.GetSelection())

        export_status = exporter.export(self.progress)

        message = "Export to CityGML finished.\n" \
                  "%s trees exported successfully.\n" \
                  "%s trees left out from export due to invalid parameters.\n" \
                  'See "Analyze > Geometry validation" for details.' % export_status
        msg = wx.MessageDialog(self, message, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()
        self.progress.SetValue(0)

    # method to validate user input and show error message is user input is invalid
    def validate_input(self):
        valid = True
        warningmessage = ""

        if self.choiceCrown.GetSelection() == self.choiceTrunk.GetSelection()and self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Crown diameter cannot be the same column as Trunk diameter"

        if self.choiceHeight.GetSelection() == self.choiceCrown.GetSelection() and self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Height cannot be the same column as Crown diameter"

        if self.choiceHeight.GetSelection() == self.choiceTrunk.GetSelection() and self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Height cannot be the same column as Trunk diameter"

        if self.choiceXvalue.GetSelection() == self.choiceYvalue.GetSelection():
            valid = False
            warningmessage = "X Value and Y Value must not be the same column"

        if self.choiceYvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Y Value column must be specified"

        if self.choiceXvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "X Value column must be specified"

        if self.__pathname == "":
            valid = False
            warningmessage = "Please specify CityGML output file path"

        if not valid:
            msg = wx.MessageDialog(self, warningmessage, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()

        return valid


class CityGmlExport:
    def __init__(self, savepath, dataobj):
        self.__db = dataobj  # db object from specialized_gui.MainTableFrame

        self.__filepath = savepath  # output file path (where citygml will be saved)
        self.__root = None  # ElementTree Root Node

        self.__DataCursor = None  # Data cursor table from database (list of lists)

        self.__bbox = analysis.BoundingBox()  # Bounding box object

        self.__prettyprint = None  # boolean variable to determine if xml output should be formatted
        self.__x_value_col_index = None  # index of column in which x value is stored
        self.__y_value_col_index = None  # index of column in which y value is stored
        self.__EPSG = None  # EPSG-Code of coordinates
        self.__EPSG_output = None  # EPSG-Code of coordinates in output

        self.__height_col_index = None  # index of height column
        self.__height_unit = None  # variable to store the unit of the hight value

        self.__trunk_diam_col_index = None  # index of trunk diameter column
        self.__trunk_diam_unit = None  # varialbe to store the unit of trunk diameter
        self.__trunk_is_circ = None  # boolean variable to indicate if trunk diam must be calculated from circumference

        self.__crown_diam_col_index = None  # index of crown diameter column
        self.__crown_diam_unit = None  # variable to store the unit of the crown diameter
        self.__crown_is_circ = None  # boolean variable to indicate if crown diam must be calculated from circumference

        self.__species_col_index = None  # index of species column

    # method to initiate citygml export
    def export(self, progressbar):
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        valid_trees = 0
        invalid_trees = 0
        self.fill_data_cursor()
        for row in self.__DataCursor:

            # validate tree parametrs
            valid = self.validate_tree_parameters(row[self.__height_col_index], row[self.__trunk_diam_col_index],
                                                  row[self.__crown_diam_col_index])

            # continue, if this trees parameters are invalid
            if not valid:
                progressbar.SetValue(progressbar.GetValue() + 1)
                invalid_trees += 1
                continue

            cityObjectMember = ET.SubElement(self.__root, "cityObjectMember")

            SolitaryVegetationObject = ET.SubElement(cityObjectMember, "veg:SolitaryVegetationObject")

            # compare thiw row's x and y vlaues with values in bounding box object
            # boung box updates if new boundries are detected
            self.__bbox.compare(row[self.__x_value_col_index], row[self.__y_value_col_index])

            # add creationDate into the model
            creationdate = ET.SubElement(SolitaryVegetationObject, "creationDate")
            creationdate.text = str(date.today())

            if self.__species_col_index is not None and row[self.__species_col_index] is not None:
                species = ET.SubElement(SolitaryVegetationObject, "veg:species")
                species.text = str(row[self.__species_col_index])

            if self.__height_col_index is not None:
                height = ET.SubElement(SolitaryVegetationObject, "veg:height")
                height.text = str(row[self.__height_col_index])
                height.set("uom", self.__height_unit)

            if self.__trunk_diam_col_index is not None:
                trunk = ET.SubElement(SolitaryVegetationObject, "veg:trunkDiameter")
                value = row[self.__trunk_diam_col_index]
                if self.__trunk_is_circ:
                    diam = value / math.pi
                else:
                    diam = value
                trunk.text = str(diam)
                trunk.set("uom", self.__trunk_diam_unit)

            if self.__crown_diam_col_index is not None:
                crown = ET.SubElement(SolitaryVegetationObject, "veg:crownDiameter")
                value = row[self.__crown_diam_col_index]
                if self.__crown_is_circ:
                    diam = value / math.pi
                else:
                    diam = value
                crown.text = str(diam)
                crown.set("uom", self.__crown_diam_unit)

            valid_trees += 1
            progressbar.SetValue(progressbar.GetValue() + 1)

        # add bounding box information to root
        self.bounded_by()

        if self.__prettyprint:
            CityGmlExport.indent(self.__root)

        tree = ET.ElementTree(self.__root)
        tree.write(self.__filepath, encoding="UTF-8", xml_declaration=True, method="xml")

        return valid_trees, invalid_trees

    # method to add namespaces and schema location to xml file
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

    # method to add bound-by-element to xml file with bounding box
    def bounded_by(self):
        bbox = self.__bbox.get_bbox()
        boundedby = ET.Element("gml:boundedBy")
        envelope = ET.SubElement(boundedby, "gml:Envelope")

        lower_corner = ET.SubElement(envelope, "gml:lowerCorner")
        upper_corner = ET.SubElement(envelope, "gml:upperCorner")

        lower_corner.text = "{0:.2f} {1:.2f}".format(bbox[0][0], bbox[0][1])
        upper_corner.text = "{0:.2f} {1:.2f}".format(bbox[1][0], bbox[1][1])

        # add bounded-by-element to the top root subelements
        self.__root.insert(0, boundedby)

    # method to check if tree parameters are valid
    # uses same method as in analyze > geometry validation
    def validate_tree_parameters(self, hight, trunk, crown):
        if self.__height_unit == "cm":
            try:
                hight = hight / 100
            except TypeError:
                pass

        if self.__trunk_diam_unit == "cm":
            try:
                trunk = trunk / 100
            except TypeError:
                pass
        if self.__trunk_is_circ:
            try:
                trunk = trunk / math.pi
            except TypeError:
                pass

        if self.__crown_diam_unit == "cm":
            try:
                crown = crown / 100
            except TypeError:
                pass
        if self.__crown_is_circ:
            try:
                crown = crown / math.pi
            except TypeError:
                pass

        analyzer = analysis.AnalyzeTreeGeoms(hight, trunk, crown)
        valid, _ = analyzer.analyze()
        return valid

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

    # method adds data to cursor again, so it can be iterated
    def fill_data_cursor(self):
        self.__DataCursor = self.__db.get_data()

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

    def set_height_unit(self, unit):
        self.__height_unit = unit

    def set_trunk_diam_unit(self, unit):
        self.__trunk_diam_unit = unit

    def set_crown_diam_unit(self, unit):
        self.__crown_diam_unit = unit

    def set_trunk_is_circ(self, val):
        self.__trunk_is_circ = val

    def set_crown_is_circ(self, val):
        self.__crown_is_circ = val

    def set_prettyprint(self, value):
        self.__prettyprint = value
