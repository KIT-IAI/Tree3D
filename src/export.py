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
        self.choiceRefheight.SetItems(colitemlist)
        self.choiceHeight.SetItems(colitemlist)
        self.choiceTrunk.SetItems(colitemlist)
        self.choiceCrown.SetItems(colitemlist)
        self.choiceSpecies.SetItems(colitemlist)
        self.choiceClass.SetItems(colitemlist)

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

        if self.choiceRefheight.GetSelection() != wx.NOT_FOUND:
            exporter.set_ref_height_col_idx(self.choiceRefheight.GetSelection())

        if self.epsg.GetValue() != "":
            exporter.set_EPSG(int(self.epsg.GetValue()))

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

        if self.choiceClass.GetSelection() != wx.NOT_FOUND:
            exporter.set_class_col_index(self.choiceClass.GetSelection())

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

        try:
            int(self.epsg.GetValue())
        except:
            valid = False
            warningmessage = "EPSG Code must be an integer number."

        if self.epsg.GetValue() == "":
            valid = False
            warningmessage = "EPSG Code must not be empty."

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
        self.__ref_height_col_index = None  # index of column in which reference height is stored
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

        self.__species_col_index = None  # index of CityGML species code column
        self.__class_col_index = None  # index of CityGML class code column
        self.__default_export_type = None  # decides what tree type should be used if it is not clear (1060 or 1070)

    # method to initiate citygml export
    def export(self, progressbar):
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        valid_trees = 0
        invalid_trees = 0
        self.fill_data_cursor()
        for row in self.__DataCursor:

            x_value = row[self.__x_value_col_index]
            y_value =row[self.__y_value_col_index]
            ref_height = row[self.__ref_height_col_index]
            tree_height = row[self.__height_col_index]
            trunk_diam = row[self.__trunk_diam_col_index]
            crown_diam = row[self.__crown_diam_col_index]

            # validate tree parametrs
            valid = self.validate_tree_parameters(tree_height, trunk_diam, crown_diam)

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

            if self.__class_col_index is not None and row[self.__class_col_index] is not None:
                klasse = ET.SubElement(SolitaryVegetationObject, "veg:class")
                klasse.text = str(row[self.__class_col_index])

            if self.__species_col_index is not None and row[self.__species_col_index] is not None:
                species = ET.SubElement(SolitaryVegetationObject, "veg:species")
                species.text = str(row[self.__species_col_index])

            if self.__height_col_index is not None:
                height = ET.SubElement(SolitaryVegetationObject, "veg:height")
                if self.__height_unit == "cm":
                    tree_height = tree_height / 100.0
                height.text = str(tree_height)
                height.set("uom", "m")

            if self.__trunk_diam_col_index is not None:
                trunk = ET.SubElement(SolitaryVegetationObject, "veg:trunkDiameter")
                if self.__trunk_diam_unit == "cm":
                    trunk_diam = trunk_diam/100.0
                if self.__trunk_is_circ:
                    trunk_diam = trunk_diam / math.pi
                trunk.text = str(trunk_diam)
                trunk.set("uom", "m")

            if self.__crown_diam_col_index is not None:
                crown = ET.SubElement(SolitaryVegetationObject, "veg:crownDiameter")
                value = crown_diam
                if self.__crown_diam_unit == "cm":
                    crown_diam = crown_diam/100.0
                if self.__crown_is_circ:
                    crown_diam = crown_diam / math.pi
                else:
                    diam = value
                crown.text = str(crown_diam)
                crown.set("uom", "m")

            #lod_1_geom = ET.SubElement(SolitaryVegetationObject, "veg:lod1Geometry")
            #self.generate_line_geometry(lod_1_geom, x_value, y_value, ref_height, tree_height)

            #lod_1_geom = ET.SubElement(SolitaryVegetationObject, "veg:lod1Geometry")
            #self.generate_billboard_rectangle_geometry(lod_1_geom, x_value, y_value, ref_height, tree_height, crown_diam, 4)

            lod_1_geom = ET.SubElement(SolitaryVegetationObject, "veg:lod1Geometry")
            self.generate_cuboid_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height, tree_height, crown_diam, trunk_diam)

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
        envelope.set("srsDimension", "2")
        envelope.set("srsName", "EPSG:%s" % self.__EPSG)

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

    # method to generate a vertiecal line geometry
    def generate_line_geometry(self, parent, x, y, ref_h, tree_h):
        l_pos_list = [x, y, ref_h, x, y, ref_h+tree_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)

        line_string = ET.SubElement(parent, "gml:LineString")
        line_string.set("srsName", "EPSG:%s" % self.__EPSG)
        line_string.set("srsDimension", str(3))

        element_pos_list = ET.SubElement(line_string, "gml:posList")
        element_pos_list.set("srsDimension", str(3))
        element_pos_list.text = s_pos_list

    # method to generate rectangle billboard geometries
    def generate_billboard_rectangle_geometry(self, parent, tree_x, tree_y, ref_h, tree_h, crown_dm, segments):
        composite_surface = ET.SubElement(parent, "gml:CompositeSurface")
        composite_surface.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_surface.set("srsDimension", "3")

        angle = 0
        rotate = 360./segments
        for _ in range(0, segments):
            x = math.cos(math.radians(angle)) * (crown_dm/2.0)
            y = math.sin(math.radians(angle)) * (crown_dm/2.0)
            l_pos_list = [tree_x, tree_y, ref_h,
                          tree_x, tree_y, ref_h + tree_h,
                          tree_x + x, tree_y + y, ref_h + tree_h,
                          tree_x + x, tree_y + y, ref_h,
                          tree_x, tree_y, ref_h]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            surface_member = ET.SubElement(composite_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            pos_list.text = s_pos_list
            angle += rotate

    def generate_cuboid_geometry_stem(self, parent, tree_x, tree_y, ref_h, stem_dm, laubansatz):
        stem_solidmember = ET.SubElement(parent, "gml:solidMember")
        stem_solid = ET.SubElement(stem_solidmember, "gml:Solid")
        stem_exterior = ET.SubElement(stem_solid, "gml:exterior")
        stem_exterior_composite_surface = ET.SubElement(stem_exterior, "gml:CompositeSurface")

        # generate bottom polygon of stem
        surfacemember_stem_bottom = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_bottom = ET.SubElement(surfacemember_stem_bottom, "gml:Polygon")
        polygon_stem_bottom_exterior = ET.SubElement(polygon_stem_bottom, "gml:exterior")
        polygon_stem_bottom_exterior_linearring = ET.SubElement(polygon_stem_bottom_exterior, "gml:LinearRing")
        polygon_stem_bottom_exterior_linearring_poslist = ET.SubElement(polygon_stem_bottom_exterior_linearring,
                                                                        "gml:posList")
        polygon_stem_bottom_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_bottom_exterior_linearring_poslist.text = s_pos_list

        # gemerate left side polygon for stem
        surfacemember_stem_left = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_left = ET.SubElement(surfacemember_stem_left, "gml:Polygon")
        polygon_stem_left_exterior = ET.SubElement(polygon_stem_left, "gml:exterior")
        polygon_stem_left_exterior_linearring = ET.SubElement(polygon_stem_left_exterior, "gml:LinearRing")
        polygon_stem_left_exterior_linearring_poslist = ET.SubElement(polygon_stem_left_exterior_linearring,
                                                                      "gml:posList")
        polygon_stem_left_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_left_exterior_linearring_poslist.text = s_pos_list

        # gemerate back side polygon for stem
        surfacemember_stem_back = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_back = ET.SubElement(surfacemember_stem_back, "gml:Polygon")
        polygon_stem_back_exterior = ET.SubElement(polygon_stem_back, "gml:exterior")
        polygon_stem_back_exterior_linearring = ET.SubElement(polygon_stem_back_exterior, "gml:LinearRing")
        polygon_stem_back_exterior_linearring_poslist = ET.SubElement(polygon_stem_back_exterior_linearring,
                                                                      "gml:posList")
        polygon_stem_back_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_back_exterior_linearring_poslist.text = s_pos_list

        # gemerate right side polygon for stem
        surfacemember_stem_right = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_right = ET.SubElement(surfacemember_stem_right, "gml:Polygon")
        polygon_stem_right_exterior = ET.SubElement(polygon_stem_right, "gml:exterior")
        polygon_stem_right_exterior_linearring = ET.SubElement(polygon_stem_right_exterior, "gml:LinearRing")
        polygon_stem_right_exterior_linearring_poslist = ET.SubElement(polygon_stem_right_exterior_linearring,
                                                                       "gml:posList")
        polygon_stem_right_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_right_exterior_linearring_poslist.text = s_pos_list

        # gemerate front side polygon for stem
        surfacemember_stem_front = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_front = ET.SubElement(surfacemember_stem_front, "gml:Polygon")
        polygon_stem_front_exterior = ET.SubElement(polygon_stem_front, "gml:exterior")
        polygon_stem_front_exterior_linearring = ET.SubElement(polygon_stem_front_exterior, "gml:LinearRing")
        polygon_stem_front_exterior_linearring_poslist = ET.SubElement(polygon_stem_front_exterior_linearring,
                                                                       "gml:posList")
        polygon_stem_front_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_front_exterior_linearring_poslist.text = s_pos_list

        # generate top polygon of stem
        surfacemember_stem_top = ET.SubElement(stem_exterior_composite_surface, "gml:surfaceMember")
        polygon_stem_top = ET.SubElement(surfacemember_stem_top, "gml:Polygon")
        polygon_stem_top_exterior = ET.SubElement(polygon_stem_top, "gml:exterior")
        polygon_stem_top_exterior_linearring = ET.SubElement(polygon_stem_top_exterior, "gml:LinearRing")
        polygon_stem_top_exterior_linearring_poslist = ET.SubElement(polygon_stem_top_exterior_linearring,
                                                                     "gml:posList")
        polygon_stem_top_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz,
                      tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz,
                      tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_stem_top_exterior_linearring_poslist.text = s_pos_list

    def generate_cuboid_geometry_deciduous(self, parent, tree_x, tree_y, ref_h, tree_h, crown_dm, stem_dm, laubansatz = None):
        if laubansatz is None:
            laubansatz = ref_h + tree_h - crown_dm
        tree_h = tree_h + ref_h

        composite_solid = ET.SubElement(parent, "gml:CompositeSolid")
        composite_solid.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_solid.set("srsDimension", "3")

        # --- generate stem geometry ---
        self.generate_cuboid_geometry_stem(composite_solid, tree_x, tree_y, ref_h, stem_dm, laubansatz)

        # --- generate crown geometry ---
        crown_solidmember = ET.SubElement(composite_solid, "gml:solidMember")
        crown_solid = ET.SubElement(crown_solidmember, "gml:Solid")
        crown_exterior = ET.SubElement(crown_solid, "gml:exterior")
        crown_exterior_composite_surface = ET.SubElement(crown_exterior, "gml:CompositeSurface")

        # generate bottom polygon of crown
        surfacemember_crown_bottom = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_bottom = ET.SubElement(surfacemember_crown_bottom, "gml:Polygon")
        polygon_crown_bottom_exterior = ET.SubElement(polygon_crown_bottom, "gml:exterior")
        polygon_crown_bottom_exterior_linearring = ET.SubElement(polygon_crown_bottom_exterior, "gml:LinearRing")
        polygon_crown_bottom_exterior_linearring_poslist = ET.SubElement(polygon_crown_bottom_exterior_linearring,
                                                                         "gml:posList")
        polygon_crown_bottom_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_bottom_exterior_linearring_poslist.text = s_pos_list

        # gemerate left side polygon for crown
        surfacemember_crown_left = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_left = ET.SubElement(surfacemember_crown_left, "gml:Polygon")
        polygon_crown_left_exterior = ET.SubElement(polygon_crown_left, "gml:exterior")
        polygon_crown_left_exterior_linearring = ET.SubElement(polygon_crown_left_exterior, "gml:LinearRing")
        polygon_crown_left_exterior_linearring_poslist = ET.SubElement(polygon_crown_left_exterior_linearring,
                                                                       "gml:posList")
        polygon_crown_left_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_left_exterior_linearring_poslist.text = s_pos_list

        # gemerate back side polygon for crown
        surfacemember_crown_back = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_back = ET.SubElement(surfacemember_crown_back, "gml:Polygon")
        polygon_crown_back_exterior = ET.SubElement(polygon_crown_back, "gml:exterior")
        polygon_crown_back_exterior_linearring = ET.SubElement(polygon_crown_back_exterior, "gml:LinearRing")
        polygon_crown_back_exterior_linearring_poslist = ET.SubElement(polygon_crown_back_exterior_linearring,
                                                                       "gml:posList")
        polygon_crown_back_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_back_exterior_linearring_poslist.text = s_pos_list

        # gemerate right side polygon for crown
        surfacemember_crown_right = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_right = ET.SubElement(surfacemember_crown_right, "gml:Polygon")
        polygon_crown_right_exterior = ET.SubElement(polygon_crown_right, "gml:exterior")
        polygon_crown_right_exterior_linearring = ET.SubElement(polygon_crown_right_exterior, "gml:LinearRing")
        polygon_crown_right_exterior_linearring_poslist = ET.SubElement(polygon_crown_right_exterior_linearring,
                                                                        "gml:posList")
        polygon_crown_right_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_right_exterior_linearring_poslist.text = s_pos_list

        # gemerate front side polygon for crown
        surfacemember_crown_front = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_front = ET.SubElement(surfacemember_crown_front, "gml:Polygon")
        polygon_crown_front_exterior = ET.SubElement(polygon_crown_front, "gml:exterior")
        polygon_crown_front_exterior_linearring = ET.SubElement(polygon_crown_front_exterior, "gml:LinearRing")
        polygon_crown_front_exterior_linearring_poslist = ET.SubElement(polygon_crown_front_exterior_linearring,
                                                                        "gml:posList")
        polygon_crown_front_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_front_exterior_linearring_poslist.text = s_pos_list

        # generate top polygon of crown
        surfacemember_crown_top = ET.SubElement(crown_exterior_composite_surface, "gml:surfaceMember")
        polygon_crown_top = ET.SubElement(surfacemember_crown_top, "gml:Polygon")
        polygon_crown_top_exterior = ET.SubElement(polygon_crown_top, "gml:exterior")
        polygon_crown_top_exterior_linearring = ET.SubElement(polygon_crown_top_exterior, "gml:LinearRing")
        polygon_crown_top_exterior_linearring_poslist = ET.SubElement(polygon_crown_top_exterior_linearring,
                                                                      "gml:posList")
        polygon_crown_top_exterior_linearring_poslist.set("srsDimension", "3")
        l_pos_list = [tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h,
                      tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_top_exterior_linearring_poslist.text = s_pos_list

    def set_x_col_idx(self, idx):
        self.__x_value_col_index = idx

    def set_y_col_idx(self, idx):
        self.__y_value_col_index = idx

    def set_ref_height_col_idx(self, idx):
        self.__ref_height_col_index = idx

    def set_EPSG(self, epsg_code):
        self.__EPSG = epsg_code

    def set_height_col_index(self, idx):
        self.__height_col_index = idx

    def set_trunk_diam_col_index(self, idx):
        self.__trunk_diam_col_index = idx

    def set_crown_diam_col_index(self, idx):
        self.__crown_diam_col_index = idx

    def set_species_col_index(self, index):
        self.__species_col_index = index

    def set_class_col_index(self, index):
        self.__class_col_index = index

    def set_default_export_type(self, type):
        self.__default_export_type = type

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

    def poslist_list_to_string(self, poslist):
        s_poslist = ""
        l_poslist = poslist
        for element in poslist:
            s_poslist += "%.2f " % element
        s_poslist = s_poslist[:-2]
        return s_poslist
