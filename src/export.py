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

        # configure if pretty print should be used in output file
        exporter.set_prettyprint(self.box_prettyprint.GetValue())

        # configure x column index
        if self.choiceXvalue.GetSelection() != wx.NOT_FOUND:
            exporter.set_x_col_idx(self.choiceXvalue.GetSelection())

        # configure y column index
        if self.choiceYvalue.GetSelection() != wx.NOT_FOUND:
            exporter.set_y_col_idx(self.choiceYvalue.GetSelection())

        # configure reference height value index
        if self.choiceRefheight.GetSelection() != wx.NOT_FOUND:
            exporter.set_ref_height_col_idx(self.choiceRefheight.GetSelection())

        # set epsg code for output geometries
        if self.epsg.GetValue() != "":
            exporter.set_epsg(int(self.epsg.GetValue()))

        # configure tree height column index
        if self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            exporter.set_height_col_index(self.choiceHeight.GetSelection())
            exporter.set_height_unit(self.choiceHeightUnit.GetString(self.choiceHeightUnit.GetSelection()))

        # configure trunk diameter column index
        if self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
            exporter.set_trunk_diam_col_index(self.choiceTrunk.GetSelection())
            exporter.set_trunk_diam_unit(self.choiceTrunkUnit.GetString(self.choiceTrunkUnit.GetSelection()))
            trunk_circ = self.trunk_circ.GetSelection()
            if trunk_circ == 1:
                exporter.set_trunk_is_circ(True)

        # configure crown diameter column index
        if self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            exporter.set_crown_diam_col_index(self.choiceCrown.GetSelection())
            exporter.set_crown_diam_unit(self.choiceCrownUnit.GetString(self.choiceCrownUnit.GetSelection()))
            crown_circ = self.crown_circ.GetSelection()
            if crown_circ == 1:
                exporter.set_crown_is_circ(True)

        # configure species column index
        if self.choiceSpecies.GetSelection() != wx.NOT_FOUND:
            exporter.set_species_col_index(self.choiceSpecies.GetSelection())

        # configure vegetation class column index
        if self.choiceClass.GetSelection() != wx.NOT_FOUND:
            exporter.set_class_col_index(self.choiceClass.GetSelection())

        # configure wether explicit or implicit geometries should be used
        if self.explicit_geom.GetValue():
            exporter.set_geomtype("EXPLICIT")
        else:
            exporter.set_geomtype("IMPLICIT")

        # Dictionary to find the geometry code to each geometry type
        geomtype_to_geomcode = {"line": 0,
                                "cylinder": 1,
                                "rectangle": 2,
                                "polygon outlines": 3,
                                "cuboid": 4,
                                "detailled": 5}

        # Setup of LOD1-Geometry
        if self.lod1.GetValue():
            geomcode = geomtype_to_geomcode[self.lod1_geomtype.GetStringSelection()]
            try:
                segments = int(self.lod1_segments.GetStringSelection())
            except ValueError:
                segments = None
            exporter.setup_lod1(True, geomcode, segments)

        # Setup of LOD2-Geometry
        if self.lod2.GetValue():
            geomcode = geomtype_to_geomcode[self.lod2_geomtype.GetStringSelection()]
            try:
                segments = int(self.lod2_segments.GetStringSelection())
            except ValueError:
                segments = None
            exporter.setup_lod2(True, geomcode, segments)

        # Setup of LOD3-Geometry
        if self.lod3.GetValue():
            geomcode = geomtype_to_geomcode[self.lod3_geomtype.GetStringSelection()]
            try:
                segments = int(self.lod3_segments.GetStringSelection())
            except:
                segments = None
            exporter.setup_lod3(True, geomcode, segments)

        # Setup of LOD4-Geometry
        if self.lod4.GetValue():
            geomcode = geomtype_to_geomcode[self.lod4_geomtype.GetStringSelection()]
            try:
                segments = int(self.lod4_segments.GetStringSelection())
            except:
                segments = None
            exporter.setup_lod4(True, geomcode, segments)

        # configure, how crown height should be calculated
        crown_height_to_code = {"same as crown diameter": 0,
                                "1/2 the height": 1,
                                "2/3 the height": 2,
                                "3/4 the height": 3,
                                "4/5 the height": 4
                                }
        crown_height_code = crown_height_to_code[self.crown_height_choice.GetStringSelection()]
        exporter.set_crown_height_code(crown_height_code)

        # start the export
        export_status = exporter.export(self.progress)

        # show dialog after export with short report
        message = "Export to CityGML finished.\n" \
                  "%s trees exported successfully.\n" \
                  "%s trees left out from export due to invalid parameters.\n" \
                  'See "Analyze > Geometry validation" for details.' % export_status
        msg = wx.MessageDialog(self, message, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()

        # reset gauge to 0
        self.progress.SetValue(0)

    # method to check what geometries can be generated
    # called whenever dropdowns to tree parameters (height, stem-diam, crown-diam) change
    def check_geometries_to_generate(self, event):
        height = self.choiceHeight.GetSelection()
        stem = self.choiceTrunk.GetSelection()
        crown = self.choiceCrown.GetSelection()

        geom_types = []

        if height != wx.NOT_FOUND:
            geom_types.append("line")

        if height != wx.NOT_FOUND and crown != wx.NOT_FOUND:
            geom_types.append("cylinder")
            geom_types.append("rectangle")

        if height != wx.NOT_FOUND and crown != wx.NOT_FOUND and stem != wx.NOT_FOUND:
            geom_types.append("polygon outlines")
            geom_types.append("cuboid")
            geom_types.append("detailled")

        # set dropdown lists
        self.lod1_geomtype.SetItems(geom_types)
        self.lod2_geomtype.SetItems(geom_types)
        self.lod3_geomtype.SetItems(geom_types)
        self.lod4_geomtype.SetItems(geom_types)

        # set dropdown values
        self.lod1_geomtype.SetSelection(0)
        self.lod2_geomtype.SetSelection(0)
        self.lod3_geomtype.SetSelection(0)
        self.lod4_geomtype.SetSelection(0)

    # method is called when LOD1-Checkbox is hit in GUI: enables/disables LOD1-Options
    def on_lod1_checkbox(self, event):
        if self.lod1_geomtype.GetSelection() == wx.NOT_FOUND:
            self.lod1.SetValue(False)
            msg = "Specify tree attributes first!"
            dlg = wx.MessageDialog(self, msg, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            dlg.ShowModal()
            return

        val = self.lod1.GetValue()
        self.lod1_geomtype.Enable(val)
        if not val:
            self.lod1_geomtype.SetSelection(0)
            self.lod1_segments_text.Show(val)
            self.lod1_segments.Show(val)

    # method is called when LOD2-Checkbox is hit in GUI: enables/disables LOD2-Options
    def on_lod2_checkbox(self, event):
        if self.lod2_geomtype.GetSelection() == wx.NOT_FOUND:
            self.lod2.SetValue(False)
            msg = "Specify tree attributes first!"
            dlg = wx.MessageDialog(self, msg, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            dlg.ShowModal()
            return

        val = self.lod2.GetValue()
        self.lod2_geomtype.Enable(val)
        if not val:
            self.lod2_geomtype.SetSelection(0)
            self.lod2_segments_text.Show(val)
            self.lod2_segments.Show(val)

    # method is called when LOD3-Checkbox is hit in GUI: enables/disables LOD3-Options
    def on_lod3_checkbox(self, event):
        if self.lod3_geomtype.GetSelection() == wx.NOT_FOUND:
            self.lod3.SetValue(False)
            msg = "Specify tree attributes first!"
            dlg = wx.MessageDialog(self, msg, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            dlg.ShowModal()
            return

        val = self.lod3.GetValue()
        self.lod3_geomtype.Enable(val)
        if not val:
            self.lod3_geomtype.SetSelection(0)
            self.lod3_segments_text.Show(val)
            self.lod3_segments.Show(val)

    # method is called when LOD4-Checkbox is hit in GUI: enables/disables LOD4-Options
    def on_lod4_checkbox(self, event):
        if self.lod4_geomtype.GetSelection() == wx.NOT_FOUND:
            self.lod4.SetValue(False)
            msg = "Specify tree attributes first!"
            dlg = wx.MessageDialog(self, msg, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            dlg.ShowModal()
            return

        val = self.lod4.GetValue()
        self.lod4_geomtype.Enable(val)
        if not val:
            self.lod4_geomtype.SetSelection(0)
            self.lod4_segments_text.Show(val)
            self.lod4_segments.Show(val)

    # method is called when LOD1-geomtype choice changes: enables/disables further geomtype options
    def on_lod1_choice(self, event):
        val = self.lod1_geomtype.GetSelection()
        if val == 1 or val == 2 or val == 3 or val == 5:
            self.lod1_segments_text.Show(True)
            self.lod1_segments.Show(True)
        else:
            self.lod1_segments_text.Show(False)
            self.lod1_segments.Show(False)

        if val == 2 or val == 3:
            self.lod1_segments.SetItems(["4", "6", "8"])
            self.lod1_segments.SetSelection(0)
        elif val == 1 or val == 5:
            self.lod1_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod1_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD2-geomtype choice changes: enables/disables further geomtype options
    def on_lod2_choice(self, event):
        val = self.lod2_geomtype.GetSelection()
        if val == 1 or val == 2 or val == 3 or val == 5:
            self.lod2_segments_text.Show(True)
            self.lod2_segments.Show(True)
        else:
            self.lod2_segments_text.Show(False)
            self.lod2_segments.Show(False)

        if val == 2 or val == 3:
            self.lod2_segments.SetItems(["4", "6", "8"])
            self.lod2_segments.SetSelection(0)
        elif val == 1 or val == 5:
            self.lod2_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod2_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD3-geomtype choice changes: enables/disables further geomtype options
    def on_lod3_choice(self, event):
        val = self.lod3_geomtype.GetSelection()
        if val == 1 or val == 2 or val == 3 or val == 5:
            self.lod3_segments_text.Show(True)
            self.lod3_segments.Show(True)
        else:
            self.lod3_segments_text.Show(False)
            self.lod3_segments.Show(False)

        if val == 2 or val == 3:
            self.lod3_segments.SetItems(["4", "6", "8"])
            self.lod3_segments.SetSelection(0)
        elif val == 1 or val == 5:
            self.lod3_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod3_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD4-geomtype choice changes: enables/disables further geomtype options
    def on_lod4_choice(self, event):
        val = self.lod4_geomtype.GetSelection()
        if val == 1 or val == 2 or val == 3 or val == 5:
            self.lod4_segments_text.Show(True)
            self.lod4_segments.Show(True)
        else:
            self.lod4_segments_text.Show(False)
            self.lod4_segments.Show(False)

        if val == 2 or val == 3:
            self.lod4_segments.SetItems(["4", "6", "8"])
            self.lod4_segments.SetSelection(0)
        elif val == 1 or val == 5:
            self.lod4_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod4_segments.SetSelection(1)
        self.Layout()

    # method to validate user input and show error message is user input is invalid
    def validate_input(self):
        valid = True
        warningmessage = ""

        if self.choiceHeight.GetSelection() == self.choiceRefheight.GetSelection()\
                and self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Tree height cannot be the same column as reference height"

        if self.choiceCrown.GetSelection() == self.choiceTrunk.GetSelection()\
                and self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Crown diameter cannot be the same column as Trunk diameter"

        if self.choiceHeight.GetSelection() == self.choiceCrown.GetSelection()\
                and self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            valid = False
            warningmessage = "Height cannot be the same column as Crown diameter"

        if self.choiceHeight.GetSelection() == self.choiceTrunk.GetSelection()\
                and self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
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

        if self.choiceClass.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Vegetation class must be specified"

        if self.choiceRefheight.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Reference Height must be specified"

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

        self.__geom_type = ""  # configures geom type: Only EXPLICIT or IMPLICIT are allowed values
        self.__crown_height_code = None  # configures how crown hight should be calulated (only values between 0-4)

        self.__use_lod1 = False  # variable determines if LOD1 is generated
        self.__lod1_geomtype = None  # variable determines type of geometry that should be generated for LOD1 (0-5)
        self.__lod1_segments = None  # variable determines number of segments to be used in geometry (not always used)

        self.__use_lod2 = False
        self.__lod2_geomtype = None
        self.__lod2_segments = None

        self.__use_lod3 = False
        self.__lod3_geomtype = None
        self.__lod3_segments = None

        self.__use_lod4 = False
        self.__lod4_geomtype = None
        self.__lod4_segments = None

    # method to initiate citygml export
    def export(self, progressbar):
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        valid_trees = 0
        invalid_trees = 0
        self.fill_data_cursor()
        for row in self.__DataCursor:

            # assign geometric values to variables
            x_value = row[self.__x_value_col_index]
            y_value = row[self.__y_value_col_index]
            ref_height = row[self.__ref_height_col_index]
            if self.__height_col_index is not None:
                tree_height = row[self.__height_col_index]
            else:
                tree_height = None
            if self.__trunk_diam_col_index is not None:
                trunk_diam = row[self.__trunk_diam_col_index]
            else:
                trunk_diam = None
            if self.__crown_diam_col_index is not None:
                crown_diam = row[self.__crown_diam_col_index]
            else:
                crown_diam = None

            # calculate crown height
            crown_height = 0
            if self.__crown_diam_col_index is not None:
                if self.__crown_height_code == 0:
                    crown_height = crown_diam
                elif self.__crown_height_code == 1:
                    crown_height = 0.5 * tree_height
                elif self.__crown_height_code == 2:
                    crown_height = (2/3.0) * tree_height
                elif self.__crown_height_code == 3:
                    crown_height = (3/4.0) * tree_height
                elif self.__crown_height_code == 4:
                    crown_height = (4/5.0) * tree_height

            # validate tree parametrs
            valid = self.validate_tree_parameters(tree_height, trunk_diam, crown_diam)

            # continue, if this tree's parameters are invalid
            if not valid:
                progressbar.SetValue(progressbar.GetValue() + 1)
                invalid_trees += 1
                continue

            city_object_member = ET.SubElement(self.__root, "cityObjectMember")

            solitary_vegetation_object = ET.SubElement(city_object_member, "veg:SolitaryVegetationObject")

            # compare thiw row's x and y vlaues with values in bounding box object
            # boung box updates if new boundries are detected
            self.__bbox.compare(row[self.__x_value_col_index], row[self.__y_value_col_index])

            # add creationDate into the model
            creationdate = ET.SubElement(solitary_vegetation_object, "creationDate")
            creationdate.text = str(date.today())

            # Add class attribute to parameterized tree model
            if self.__class_col_index is not None and row[self.__class_col_index] is not None:
                klasse = ET.SubElement(solitary_vegetation_object, "veg:class")
                klasse.text = str(row[self.__class_col_index])

            # Add species attribute to parameterized tree model
            if self.__species_col_index is not None and row[self.__species_col_index] is not None:
                species = ET.SubElement(solitary_vegetation_object, "veg:species")
                species.text = str(row[self.__species_col_index])

            # Add hight attribute to parameterized tree model
            if self.__height_col_index is not None:
                height = ET.SubElement(solitary_vegetation_object, "veg:height")
                if self.__height_unit == "cm":
                    tree_height = tree_height / 100.0
                height.text = str(tree_height)
                height.set("uom", "m")

            # Add trunk (stem) diameter attribute to parameterized tree model
            if self.__trunk_diam_col_index is not None:
                trunk = ET.SubElement(solitary_vegetation_object, "veg:trunkDiameter")
                if self.__trunk_diam_unit == "cm":
                    trunk_diam = trunk_diam/100.0
                if self.__trunk_is_circ:
                    trunk_diam = trunk_diam / math.pi
                trunk.text = str(trunk_diam)
                trunk.set("uom", "m")

            # Add crown diameter attribute to parameterized tree model
            if self.__crown_diam_col_index is not None:
                crown = ET.SubElement(solitary_vegetation_object, "veg:crownDiameter")
                if self.__crown_diam_unit == "cm":
                    crown_diam = crown_diam/100.0
                if self.__crown_is_circ:
                    crown_diam = crown_diam / math.pi
                crown.text = str(crown_diam)
                crown.set("uom", "m")

            # Create explicit geometries
            if self.__geom_type == "EXPLICIT":
                # Calls methods to generate geometries for LOD1, depending on user input
                if self.__use_lod1:
                    lod_1_geom = ET.SubElement(solitary_vegetation_object, "veg:lod1Geometry")
                    if self.__lod1_geomtype == 0:
                        self.generate_line_geometry(lod_1_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod1_geomtype == 1:
                        self.generate_cylinder_geometry(lod_1_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_1_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod1_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod1_segments, crown_height)
                    elif self.__lod1_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod1_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod1_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod1_segments, crown_height)

                # Calls methods to generate geometries for LOD2, depending on user input
                if self.__use_lod2:
                    lod_2_geom = ET.SubElement(solitary_vegetation_object, "veg:lod2Geometry")
                    if self.__lod2_geomtype == 0:
                        self.generate_line_geometry(lod_2_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod2_geomtype == 1:
                        self.generate_cylinder_geometry(lod_2_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_2_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod2_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod2_segments, crown_height)
                    elif self.__lod2_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod2_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod2_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod2_segments, crown_height)

                # Calls methods to generate geometries for LOD3, depending on user input
                if self.__use_lod3:
                    lod_3_geom = ET.SubElement(solitary_vegetation_object, "veg:lod3Geometry")
                    if self.__lod3_geomtype == 0:
                        self.generate_line_geometry(lod_3_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod3_geomtype == 1:
                        self.generate_cylinder_geometry(lod_3_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_3_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod3_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod3_segments, crown_height)
                    elif self.__lod3_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod3_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod3_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod3_segments, crown_height)

                # Calls methods to generate geometries for LOD4, depending on user input
                if self.__use_lod4:
                    lod_4_geom = ET.SubElement(solitary_vegetation_object, "veg:lod4Geometry")
                    if self.__lod4_geomtype == 0:
                        self.generate_line_geometry(lod_4_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod4_geomtype == 1:
                        self.generate_cylinder_geometry(lod_4_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_4_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod4_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod4_segments, crown_height)
                    elif self.__lod4_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod4_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod4_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod4_segments, crown_height)

            # Create implicit geometries
            elif self.__geom_type == "IMPLICIT":
                if self.__use_lod1:
                    lod1_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod1ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod1_implicit_geometry, "ImplicitGeometry")

                    # add transformation matrix
                    matrix = ET.SubElement(implicit_geometry, "transformationMatrix")
                    matrix.text = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"

                    lod_1_geom = ET.SubElement(implicit_geometry, "relativeGMLGeometry")
                    if self.__lod1_geomtype == 0:
                        self.generate_line_geometry(lod_1_geom, 0, 0, 0, tree_height)
                    elif self.__lod1_geomtype == 1:
                        self.generate_cylinder_geometry(lod_1_geom, 0, 0, 0,
                                                        tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_1_geom, 0, 0, 0,
                                                                   tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_1_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod1_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_1_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod1_segments, crown_height)
                    elif self.__lod1_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_1_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod1_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod1_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_1_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod1_segments, crown_height)

                    # add reference point
                    ref_point = ET.SubElement(implicit_geometry, "referencePoint")
                    gml_point = ET.SubElement(ref_point, "gml:Point")
                    gml_point.set("srsName", "EPSG:%s" % self.__EPSG)
                    gml_point.set("srsDimension", "3")
                    gml_pos = ET.SubElement(gml_point, "gml:pos")
                    gml_pos.set("srsDimension", "3")
                    pos_list = [x_value, y_value, ref_height]
                    gml_pos.text = self.poslist_list_to_string(pos_list)

                # Calls methods to generate geometries for LOD2, depending on user input
                if self.__use_lod2:
                    lod2_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod2ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod2_implicit_geometry, "ImplicitGeometry")

                    # add transformation matrix
                    matrix = ET.SubElement(implicit_geometry, "transformationMatrix")
                    matrix.text = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"

                    lod_2_geom = ET.SubElement(implicit_geometry, "relativeGMLGeometry")
                    if self.__lod2_geomtype == 0:
                        self.generate_line_geometry(lod_2_geom, 0, 0, 0, tree_height)
                    elif self.__lod2_geomtype == 1:
                        self.generate_cylinder_geometry(lod_2_geom, 0, 0, 0,
                                                        tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_2_geom, 0, 0, 0,
                                                                   tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_2_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod2_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_2_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod2_segments, crown_height)
                    elif self.__lod2_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_2_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod2_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod2_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_2_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod2_segments, crown_height)

                    # add reference point
                    ref_point = ET.SubElement(implicit_geometry, "referencePoint")
                    gml_point = ET.SubElement(ref_point, "gml:Point")
                    gml_point.set("srsName", "EPSG:%s" % self.__EPSG)
                    gml_point.set("srsDimension", "3")
                    gml_pos = ET.SubElement(gml_point, "gml:pos")
                    gml_pos.set("srsDimension", "3")
                    pos_list = [x_value, y_value, ref_height]
                    gml_pos.text = self.poslist_list_to_string(pos_list)

                # Calls methods to generate geometries for LOD3, depending on user input
                if self.__use_lod3:
                    lod3_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod3ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod3_implicit_geometry, "ImplicitGeometry")

                    # add transformation matrix
                    matrix = ET.SubElement(implicit_geometry, "transformationMatrix")
                    matrix.text = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"

                    lod_3_geom = ET.SubElement(implicit_geometry, "relativeGMLGeometry")
                    if self.__lod3_geomtype == 0:
                        self.generate_line_geometry(lod_3_geom, 0, 0, 0, tree_height)
                    elif self.__lod3_geomtype == 1:
                        self.generate_cylinder_geometry(lod_3_geom, 0, 0, 0,
                                                        tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_3_geom, 0, 0, 0,
                                                                   tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_3_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod3_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_3_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod3_segments, crown_height)
                    elif self.__lod3_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_3_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod3_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod3_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_3_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod3_segments, crown_height)

                    # add reference point
                    ref_point = ET.SubElement(implicit_geometry, "referencePoint")
                    gml_point = ET.SubElement(ref_point, "gml:Point")
                    gml_point.set("srsName", "EPSG:%s" % self.__EPSG)
                    gml_point.set("srsDimension", "3")
                    gml_pos = ET.SubElement(gml_point, "gml:pos")
                    gml_pos.set("srsDimension", "3")
                    pos_list = [x_value, y_value, ref_height]
                    gml_pos.text = self.poslist_list_to_string(pos_list)

                # Calls methods to generate geometries for LOD4, depending on user input
                if self.__use_lod4:
                    lod4_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod4ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod4_implicit_geometry, "ImplicitGeometry")

                    # add transformaiton matrix
                    matrix = ET.SubElement(implicit_geometry, "transformationMatrix")
                    matrix.text = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"

                    lod_4_geom = ET.SubElement(implicit_geometry, "relativeGMLGeometry")
                    if self.__lod4_geomtype == 0:
                        self.generate_line_geometry(lod_4_geom, 0, 0, 0, tree_height)
                    elif self.__lod4_geomtype == 1:
                        self.generate_cylinder_geometry(lod_4_geom, 0, 0, 0,
                                                        tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_4_geom, 0, 0, 0,
                                                                   tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 3:
                        if row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_4_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod4_segments, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_4_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod4_segments, crown_height)
                    elif self.__lod4_geomtype == 4:
                        if row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_4_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                    elif self.__lod4_geomtype == 5:
                        if row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod4_segments, crown_height)
                        elif row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_4_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod4_segments, crown_height)

                    # add reference point
                    ref_point = ET.SubElement(implicit_geometry, "referencePoint")
                    gml_point = ET.SubElement(ref_point, "gml:Point")
                    gml_point.set("srsName", "EPSG:%s" % self.__EPSG)
                    gml_point.set("srsDimension", "3")
                    gml_pos = ET.SubElement(gml_point, "gml:pos")
                    gml_pos.set("srsDimension", "3")
                    pos_list = [x_value, y_value, ref_height]
                    gml_pos.text = self.poslist_list_to_string(pos_list)

            # update couter for valid trees
            valid_trees += 1

            # update gauge in GUI
            progressbar.SetValue(progressbar.GetValue() + 1)

        # add bounding box information to root
        self.bounded_by()

        # reformat to prettyprint xml output
        if self.__prettyprint:
            CityGmlExport.indent(self.__root)

        # write tree to output file
        tree = ET.ElementTree(self.__root)
        tree.write(self.__filepath, encoding="UTF-8", xml_declaration=True, method="xml")

        # return number of exported valid trees and number of trees that were not exported
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
    def generate_billboard_rectangle_geometry(self, parent, tree_x, tree_y, ref_h,
                                              tree_h, crown_dm, segments):
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

    # generate billboard from polygon outlines for deciduous trees
    def generate_billboard_polygon_deciduous(self, parent, tree_x, tree_y, ref_h,
                                             tree_h, crown_dm, stem_dm, segments, crown_height):
        laubansatz = ref_h + tree_h - crown_height
        tree_h = tree_h + ref_h

        composite_surface = ET.SubElement(parent, "gml:CompositeSurface")
        composite_surface.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_surface.set("srsDimension", "3")

        angle = 0.
        rotate = (2*math.pi) / segments

        alpha = math.asin((stem_dm/2.0)/(crown_dm/2.0))
        delta = (tree_h-laubansatz)/2.0 - (crown_height/2.0)*math.cos(alpha)

        for _ in range(0, segments):
            sinx = math.sin(angle)
            cosx = math.cos(angle)

            # creating stem polygon
            l_pos_list = [tree_x, tree_y, ref_h,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), ref_h,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz+delta,
                          tree_x, tree_y, laubansatz+delta,
                          tree_x, tree_y, ref_h]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            surface_member = ET.SubElement(composite_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            pos_list.text = s_pos_list

            # create crown polygon
            l_pos_list = [tree_x, tree_y, laubansatz+delta,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz + delta]

            # generate circle points for crown
            for v_angle in range(0, 180, 10):
                if math.radians(v_angle) < alpha:
                    continue
                l_pos_list.append(tree_x + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * cosx)
                l_pos_list.append(tree_y + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * sinx)
                l_pos_list.append(laubansatz + crown_height/2.0 +
                                  (crown_height/2.0) * math.cos(math.radians(180-v_angle)))

            # finish crown geometry
            l_pos_list.extend([tree_x, tree_y, tree_h])
            l_pos_list.extend([tree_x, tree_y, laubansatz+delta])

            s_pos_list = self.poslist_list_to_string(l_pos_list)
            surface_member = ET.SubElement(composite_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            pos_list.text = s_pos_list

            angle += rotate

    # generate billboard from polygon outlines for coniferous trees
    def generate_billboard_polygon_coniferous(self, parent, tree_x, tree_y, ref_h,
                                              tree_h, crown_dm, stem_dm, segments, crown_height):
        laubansatz = ref_h + tree_h - crown_height
        tree_h = tree_h + ref_h

        composite_surface = ET.SubElement(parent, "gml:CompositeSurface")
        composite_surface.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_surface.set("srsDimension", "3")

        angle = 0.
        rotate = (2*math.pi) / segments
        for _ in range(0, segments):
            sinx = math.sin(angle)
            cosx = math.cos(angle)

            # creating stem polygon
            l_pos_list = [tree_x, tree_y, ref_h,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), ref_h,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz,
                          tree_x, tree_y, laubansatz,
                          tree_x, tree_y, ref_h]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            surface_member = ET.SubElement(composite_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            pos_list.text = s_pos_list

            # creatin crown polygon
            l_pos_list = [tree_x, tree_y, laubansatz,
                          tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz,
                          tree_x + cosx * (crown_dm / 2.0), tree_y + sinx * (crown_dm / 2.0), laubansatz,
                          tree_x, tree_y, tree_h,
                          tree_x, tree_y, laubansatz]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            surface_member = ET.SubElement(composite_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            pos_list.text = s_pos_list
            angle += rotate

    # method to generate cylinder geometry
    def generate_cylinder_geometry(self, parent, tree_x, tree_y, ref_h,
                                   tree_h, crown_dm, segments):
        tree_h = tree_h + ref_h

        solid = ET.SubElement(parent, "gml:Solid")
        solid.set("srsName", "EPSG:%s" % self.__EPSG)
        solid.set("srsDimension", "3")
        exterior = ET.SubElement(solid, "gml:exterior")
        comp_surface = ET.SubElement(exterior, "gml:CompositeSurface")

        angle = 0
        rotate = 2*math.pi / segments

        coordinates = []
        for _ in range(0, segments):
            pnt = [tree_x + (crown_dm/2) * math.cos(angle), tree_y + (crown_dm/2) * math.sin(angle)]
            coordinates.append(pnt)
            angle += rotate

        # generate walls of cylinder
        for index in range(0, len(coordinates)):
            surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")

            l_pos_list = [coordinates[index][0], coordinates[index][1], ref_h,
                          coordinates[index][0], coordinates[index][1], tree_h,
                          coordinates[index-1][0], coordinates[index-1][1], tree_h,
                          coordinates[index-1][0], coordinates[index-1][1], ref_h,
                          coordinates[index][0], coordinates[index][1], ref_h]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            pos_list.text = s_pos_list

        # generate top of cylinder
        top_poslsit = []
        for point in coordinates:
            top_poslsit.extend([point[0], point[1], tree_h])
        top_poslsit.extend([coordinates[0][0], coordinates[0][1], tree_h])

        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        s_pos_list = self.poslist_list_to_string(top_poslsit)
        pos_list.text = s_pos_list

        # generate bottom of cylinder
        bototm_poslist = []
        for point in reversed(coordinates):
            bototm_poslist.extend([point[0], point[1], ref_h])
        bototm_poslist.extend([coordinates[-1][0], coordinates[-1][1], ref_h])

        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        s_pos_list = self.poslist_list_to_string(bototm_poslist)
        pos_list.text = s_pos_list

    # method to generate the stem for cuboid geometries
    def generate_cuboid_geometry_stem(self, parent, tree_x, tree_y, ref_h,
                                      stem_dm, laubansatz):
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

    # method to generate a cuboid geometry for deciduous trees
    def generate_cuboid_geometry_deciduous(self, parent, tree_x, tree_y, ref_h,
                                           tree_h, crown_dm, stem_dm, crown_height):
        laubansatz = ref_h + tree_h - crown_height
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

    # method to generate a cuboid geometry for deciduous trees
    def generate_cuboid_geometry_coniferous(self, parent, tree_x, tree_y, ref_h, tree_h,
                                            crown_dm, stem_dm, crown_height):
        laubansatz = ref_h + tree_h - crown_height
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
                      tree_x, tree_y, tree_h,
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
                      tree_x, tree_y, tree_h,
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
                      tree_x, tree_y, tree_h,
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
                      tree_x, tree_y, tree_h,
                      tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz,
                      tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz]
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        polygon_crown_front_exterior_linearring_poslist.text = s_pos_list

    # generate stem for geometries: cylinder
    def generate_geometry_stem(self, parent, tree_x, tree_y, ref_h,
                               stem_dm, laubansatz, segments):
        stem_solidmember = ET.SubElement(parent, "gml:solidMember")
        stem_solid = ET.SubElement(stem_solidmember, "gml:Solid")
        stem_exterior = ET.SubElement(stem_solid, "gml:exterior")
        comp_surface = ET.SubElement(stem_exterior, "gml:CompositeSurface")

        angle = 0
        rotate = 2 * math.pi / segments

        coordinates = []
        for _ in range(0, segments):
            pnt = [tree_x + (stem_dm / 2) * math.cos(angle), tree_y + (stem_dm / 2) * math.sin(angle)]
            coordinates.append(pnt)
            angle += rotate

        # generate walls of cylinder
        for index in range(0, len(coordinates)):
            surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")

            l_pos_list = [coordinates[index][0], coordinates[index][1], ref_h,
                          coordinates[index][0], coordinates[index][1], laubansatz,
                          coordinates[index - 1][0], coordinates[index - 1][1], laubansatz,
                          coordinates[index - 1][0], coordinates[index - 1][1], ref_h,
                          coordinates[index][0], coordinates[index][1], ref_h]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            pos_list.text = s_pos_list

        # generate top of cylinder
        top_poslsit = []
        for point in coordinates:
            top_poslsit.extend([point[0], point[1], laubansatz])
        top_poslsit.extend([coordinates[0][0], coordinates[0][1], laubansatz])

        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        s_pos_list = self.poslist_list_to_string(top_poslsit)
        pos_list.text = s_pos_list

        # generate bottom of cylinder
        bototm_poslist = []
        for point in reversed(coordinates):
            bototm_poslist.extend([point[0], point[1], ref_h])
        bototm_poslist.extend([coordinates[-1][0], coordinates[-1][1], ref_h])

        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        s_pos_list = self.poslist_list_to_string(bototm_poslist)
        pos_list.text = s_pos_list

    # generate most detailed geometry for coniferous trees
    # cylinder for stem, cone for crown
    def generate_geometry_coniferous(self, parent, tree_x, tree_y, ref_h,
                                     tree_h, crown_dm, stem_dm, segments, crown_height):
        laubansatz = ref_h + tree_h - crown_height
        tree_h = tree_h + ref_h

        composite_solid = ET.SubElement(parent, "gml:CompositeSolid")
        composite_solid.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_solid.set("srsDimension", "3")

        # generate stem geometry
        self.generate_geometry_stem(composite_solid, tree_x, tree_y, ref_h, stem_dm, laubansatz, segments)

        # generate crown geometry (cone)
        solid_member_stem = ET.SubElement(composite_solid, "gml:solidMember")
        solid = ET.SubElement(solid_member_stem, "gml:Solid")
        crown_exterior = ET.SubElement(solid, "gml:exterior")
        comp_surface = ET.SubElement(crown_exterior, "gml:CompositeSurface")

        # generate walls of cone
        angle = 0
        rotate = 2 * math.pi / segments

        coordinates = []
        for _ in range(0, segments):
            pnt = [tree_x + (crown_dm / 2) * math.cos(angle), tree_y + (crown_dm / 2) * math.sin(angle)]
            coordinates.append(pnt)
            angle += rotate

        for index in range(0, len(coordinates)):
            surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            l_pos_list = [coordinates[index][0], coordinates[index][1], laubansatz,
                          tree_x, tree_y, tree_h,
                          coordinates[index-1][0], coordinates[index-1][1], laubansatz,
                          coordinates[index][0], coordinates[index][1], laubansatz]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            pos_list.text = s_pos_list

        # generate bottom of cone
        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        l_pos_list = []
        for point in reversed(coordinates):
            l_pos_list.extend([point[0], point[1], laubansatz])
        l_pos_list.extend([coordinates[-1][0], coordinates[-1][1], laubansatz])
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        pos_list.text = s_pos_list

    # generate most detailed geometry for deciduous trees:
    # cylinder for stem, ellipsoid for crown
    def generate_geometry_deciduous(self, parent, tree_x, tree_y, ref_h,
                                    tree_h, crown_dm, stem_dm, segments, crown_height):
        laubansatz = ref_h + tree_h - crown_height
        tree_h = tree_h + ref_h

        alpha = math.asin((stem_dm / 2.0) / (crown_dm / 2.0))
        delta = (tree_h - laubansatz) / 2.0 - (crown_height / 2.0) * math.cos(alpha)

        composite_solid = ET.SubElement(parent, "gml:CompositeSolid")
        composite_solid.set("srsName", "EPSG:%s" % self.__EPSG)
        composite_solid.set("srsDimension", "3")

        # generate stem geometry
        self.generate_geometry_stem(composite_solid, tree_x, tree_y, ref_h, stem_dm, laubansatz+delta, segments)

        # generate crown geometry (ellipsoid)
        solid_member_stem = ET.SubElement(composite_solid, "gml:solidMember")
        solid = ET.SubElement(solid_member_stem, "gml:Solid")
        crown_exterior = ET.SubElement(solid, "gml:exterior")
        comp_surface = ET.SubElement(crown_exterior, "gml:CompositeSurface")

        # generate ellipsoid points: first row
        coordinates = []
        row = []
        for h_angle in range(0, 360, int(360/segments)):
            pnt = [tree_x - (crown_dm/2.0) * math.sin(2*math.pi-alpha) * math.cos(math.radians(h_angle)),
                   tree_y - (crown_dm/2.0) * math.sin(2*math.pi-alpha) * math.sin(math.radians(h_angle)),
                   laubansatz + delta]
            row.append(pnt)
        coordinates.append(row)

        # generate ellipsoid points: all other rows
        for v_angle in range(0, 180, int(180/(segments/2))):
            if math.radians(v_angle) < alpha:
                continue
            row = []
            for h_angle in range(0, 360, int(360/segments)):
                pnt = [tree_x + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * math.cos(math.radians(h_angle)),
                       tree_y + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * math.sin(math.radians(h_angle)),
                       laubansatz + (tree_h-laubansatz)/2 + ((tree_h-laubansatz)/2) * math.cos(math.radians(180-v_angle))]
                row.append(pnt)
            coordinates.append(row)

        # generate side segments for ellipsoid
        for row_index in range(1, len(coordinates)):
            for pnt_index in range(0, len(coordinates[row_index])):
                surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
                polygon = ET.SubElement(surface_member, "gml:Polygon")
                exterior = ET.SubElement(polygon, "gml:exterior")
                linear_ring = ET.SubElement(exterior, "gml:LinearRing")
                pos_list = ET.SubElement(linear_ring, "gml:posList")
                pos_list.set("srsDimension", "3")
                l_pos_list = []

                pnt1 = [coordinates[row_index][pnt_index][0],
                        coordinates[row_index][pnt_index][1],
                        coordinates[row_index][pnt_index][2]]
                pnt2 = [coordinates[row_index][pnt_index-1][0],
                        coordinates[row_index][pnt_index-1][1],
                        coordinates[row_index][pnt_index-1][2]]
                pnt3 = [coordinates[row_index-1][pnt_index - 1][0],
                        coordinates[row_index-1][pnt_index - 1][1],
                        coordinates[row_index-1][pnt_index - 1][2]]
                pnt4 = [coordinates[row_index - 1][pnt_index][0],
                        coordinates[row_index - 1][pnt_index][1],
                        coordinates[row_index - 1][pnt_index][2]]

                l_pos_list.extend(pnt1)
                l_pos_list.extend(pnt2)
                l_pos_list.extend(pnt3)
                l_pos_list.extend(pnt4)
                l_pos_list.extend(pnt1)
                s_pos_list = self.poslist_list_to_string(l_pos_list)
                pos_list.text = s_pos_list

        # generate top triangle segments
        top_row = coordinates[-1]
        for index in range(0, len(top_row)):
            surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
            polygon = ET.SubElement(surface_member, "gml:Polygon")
            exterior = ET.SubElement(polygon, "gml:exterior")
            linear_ring = ET.SubElement(exterior, "gml:LinearRing")
            pos_list = ET.SubElement(linear_ring, "gml:posList")
            pos_list.set("srsDimension", "3")
            l_pos_list = [top_row[index][0], top_row[index][1], top_row[index][2],
                          tree_x, tree_y, tree_h,
                          top_row[index-1][0], top_row[index-1][1], top_row[index-1][2],
                          top_row[index][0], top_row[index][1], top_row[index][2]]
            s_pos_list = self.poslist_list_to_string(l_pos_list)
            pos_list.text = s_pos_list

        # generate bottom polygon
        bottom_row = coordinates[0]
        l_pos_list = []
        for point in reversed(bottom_row):
            l_pos_list.extend([point[0], point[1], point[2]])
        surface_member = ET.SubElement(comp_surface, "gml:surfaceMember")
        polygon = ET.SubElement(surface_member, "gml:Polygon")
        exterior = ET.SubElement(polygon, "gml:exterior")
        linear_ring = ET.SubElement(exterior, "gml:LinearRing")
        pos_list = ET.SubElement(linear_ring, "gml:posList")
        pos_list.set("srsDimension", "3")
        s_pos_list = self.poslist_list_to_string(l_pos_list)
        pos_list.text = s_pos_list

    def set_x_col_idx(self, idx):
        self.__x_value_col_index = idx

    def set_y_col_idx(self, idx):
        self.__y_value_col_index = idx

    def set_ref_height_col_idx(self, idx):
        self.__ref_height_col_index = idx

    def set_epsg(self, epsg_code):
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

    def set_default_export_type(self, typ):
        self.__default_export_type = typ

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

    def set_geomtype(self, geomtype):
        self.__geom_type = geomtype

    def set_crown_height_code(self, code):
        self.__crown_height_code = code

    # method to setup LOD1 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod1(self, value, geomtype, segments=None):
        self.__use_lod1 = value
        self.__lod1_geomtype = geomtype
        if segments is not None:
            self.__lod1_segments = segments

    # method to setup LOD2 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod2(self, value, geomtype, segments=None):
        self.__use_lod2 = value
        self.__lod2_geomtype = geomtype
        if segments is not None:
            self.__lod2_segments = segments

    # method to setup LOD3 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod3(self, value, geomtype, segments=None):
        self.__use_lod3 = value
        self.__lod3_geomtype = geomtype
        if segments is not None:
            self.__lod3_segments = segments

    # method to setup LOD4 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod4(self, value, geomtype, segments=None):
        self.__use_lod4 = value
        self.__lod4_geomtype = geomtype
        if segments is not None:
            self.__lod4_segments = segments

    # a list of coordinates to a string to be used in posList
    # [x1, y1, z1, x2, y, z2, ...] --> "x1 y1 z1 x2 y2 z2 ..."
    def poslist_list_to_string(self, poslist):
        s_poslist = ""
        for element in poslist:
            s_poslist += "%.3f " % element
        s_poslist = s_poslist[:-1]
        return s_poslist
