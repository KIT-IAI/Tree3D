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
        self.ChoiceCrownHeightCol.SetItems(colitemlist)

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

        # set variable to generate generic CityGML attributes
        exporter.set_generate_generic_attributes(self.check_generate_generic.GetValue())
        exporter.set_col_datatypes(self.GetParent().db.get_column_datatypes())
        exporter.set_col_names(self.GetParent().db.get_column_names())

        # configure what type of tree (deciduous or coniferous) should be used
        # this type is used if class code is invalid (not 1060 or 1070) or no class column is specified
        default_type = 0
        if self.default_choice.GetSelection() == 0:
            default_type = 0000
        elif self.default_choice.GetSelection() == 1:
            default_type = 1070
        elif self.default_choice.GetSelection() == 2:
            default_type = 1060
        exporter.set_default_export_type(default_type)

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
                                "1/2 the tree height": 1,
                                "2/3 the tree height": 2,
                                "3/4 the tree height": 3,
                                "4/5 the tree height": 4,
                                "from column": 5
                                }
        crown_height_code = crown_height_to_code[self.crown_height_choice.GetStringSelection()]
        exporter.set_crown_height_code(crown_height_code)

        if crown_height_code == 5:
            exporter.set_crown_height_col_index(self.ChoiceCrownHeightCol.GetSelection())

        # start the export
        export_status = exporter.export(self.progress)

        # show dialog after export with short report
        message = "Export to CityGML finished.\n" \
                  "%s SolitaryVegetationObjects exported to CityGML file." % export_status[0]

        if export_status[1] > 0:
            message += "\nLOD1: %s geometries could not be created" % export_status[1]

        if export_status[2] > 0:
            message += "\nLOD2: %s geometries could not be created" % export_status[2]

        if export_status[3] > 0:
            message += "\nLOD3: %s geometries could not be created" % export_status[3]

        if export_status[4] > 0:
            message += "\nLOD4: %s geometries could not be created" % export_status[4]

        if export_status[1] > 0 or export_status[2] > 0 or export_status[3] > 0 or export_status[4] > 0:
            message += '\nSee "Analyze > Geometry validation" for details.'
        msg = wx.MessageDialog(self, message, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()

        # reset gauge to 0
        self.progress.SetValue(0)

    def on_crown_height_options( self, event ):
        if self.crown_height_choice.GetSelection() == 5:
            self.CrownHeightColText.Show()
            self.ChoiceCrownHeightCol.Show()
            self.Layout()
        else:
            self.CrownHeightColText.Show(False)
            self.ChoiceCrownHeightCol.Show(False)

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

        if self.crown_height_choice.GetSelection() == 5 and self.ChoiceCrownHeightCol.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Crown height columnn must be specified"

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

        self.__generate_generic_attributes = None  # variable to generate generic attributes (Trud/False)
        self.__col_datatypes = None
        self.__col_names = None

        self.__crown_height_col_index = None

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

        self.__current_lod = ""

        self.__current_tree_gmlid = ""
        self.__stem_gmlids = []
        self.__crown_deciduous_gmlids = []
        self.__crown_coniferous_gmlids = []

    # method to initiate citygml export
    def export(self, progressbar):
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        exported_trees = 0
        invalid_lod1 = 0
        invalid_lod2 = 0
        invalid_lod3 = 0
        invalid_lod4 = 0

        # list to keep track of what columns are used. All other will be used for generic attributes
        used_cols = [self.__x_value_col_index,
                     self.__y_value_col_index,
                     self.__ref_height_col_index,
                     self.__height_col_index,
                     self.__crown_diam_col_index,
                     self.__trunk_diam_col_index,
                     self.__class_col_index,
                     self.__species_col_index]

        self.fill_data_cursor()
        for row in self.__DataCursor:

            self.__current_tree_gmlid = "tree%s" % exported_trees

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
            if crown_diam is not None and self.__crown_height_code == 0:
                crown_height = crown_diam
            elif tree_height is not None and self.__crown_height_code == 1:
                crown_height = 0.5 * tree_height
            elif tree_height is not None and self.__crown_height_code == 2:
                crown_height = (2/3.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 3:
                crown_height = (3/4.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 4:
                crown_height = (4/5.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 5:
                crown_height = row[self.__crown_height_col_index]

            # converting everything into its correct units
            # converting cm -> m and circumferences -> diameter
            if self.__height_col_index is not None and self.__height_unit == "cm":
                tree_height = tree_height / 100.0

            if self.__trunk_diam_col_index is not None and trunk_diam is not None:
                if self.__trunk_diam_unit == "cm":
                    trunk_diam = trunk_diam/100.0
                if self.__trunk_is_circ:
                    trunk_diam = trunk_diam / math.pi

            if self.__crown_diam_col_index is not None and crown_diam is not None:
                if self.__crown_diam_unit == "cm":
                    crown_diam = crown_diam/100.0
                if self.__crown_is_circ:
                    crown_diam = crown_diam / math.pi

            # validate tree parametrs
            validator = analysis.AnalyzeTreeGeoms(tree_height, trunk_diam, crown_diam, crown_height)
            lod1_valid = False
            lod2_valid = False
            lod3_valid = False
            lod4_valid = False

            # validate tree parameters for LOD1 geometry
            if self.__lod1_geomtype == 0:
                lod1_valid, _ = validator.analyze_height()
            elif self.__lod1_geomtype == 1 or self.__lod1_geomtype == 2:
                lod1_valid, _ = validator.analyze_height_crown()
            elif self.__lod1_geomtype == 3 or self.__lod1_geomtype == 4 or self.__lod1_geomtype == 5:
                if self.__crown_height_code == 0:
                    lod1_valid, _ = validator.analyze_height_crown_trunk_sphere()
                elif 0 < self.__crown_height_code < 5:
                    lod1_valid, _ = validator.analyze_height_crown_trunk()
                elif self.__crown_height_code == 5:
                    lod1_valid, _ = validator.analyze_height_crown_trunk_nosphere()

            # validate tree parameters for LOD2 geometry
            if self.__lod2_geomtype == 0:
                lod2_valid, _ = validator.analyze_height()
            elif self.__lod2_geomtype == 1 or self.__lod2_geomtype == 2:
                lod2_valid, _ = validator.analyze_height_crown()
            elif self.__lod2_geomtype == 3 or self.__lod2_geomtype == 4 or self.__lod2_geomtype == 5:
                if self.__crown_height_code == 0:
                    lod2_valid, _ = validator.analyze_height_crown_trunk_sphere()
                elif 0 < self.__crown_height_code < 5:
                    lod2_valid, _ = validator.analyze_height_crown_trunk()
                elif self.__crown_height_code == 5:
                    lod2_valid, _ = validator.analyze_height_crown_trunk_nosphere()

            # validate tree parameters for LOD3 geometry
            if self.__lod3_geomtype == 0:
                lod3_valid, _ = validator.analyze_height()
            elif self.__lod3_geomtype == 1 or self.__lod3_geomtype == 2:
                lod3_valid, _ = validator.analyze_height_crown()
            elif self.__lod3_geomtype == 3 or self.__lod3_geomtype == 4 or self.__lod3_geomtype == 5:
                if self.__crown_height_code == 0:
                    lod3_valid, _ = validator.analyze_height_crown_trunk_sphere()
                elif 0 < self.__crown_height_code < 5:
                    lod3_valid, _ = validator.analyze_height_crown_trunk()
                elif self.__crown_height_code == 5:
                    lod3_valid, _ = validator.analyze_height_crown_trunk_nosphere()

            # validate tree parameters for LOD4 geometry
            if self.__lod4_geomtype == 0:
                lod4_valid, _ = validator.analyze_height()
            elif self.__lod4_geomtype == 1 or self.__lod4_geomtype == 2:
                lod4_valid, _ = validator.analyze_height_crown()
            elif self.__lod4_geomtype == 3 or self.__lod4_geomtype == 4 or self.__lod4_geomtype == 5:
                if self.__crown_height_code == 0:
                    lod4_valid, _ = validator.analyze_height_crown_trunk_sphere()
                elif 0 < self.__crown_height_code < 5:
                    lod4_valid, _ = validator.analyze_height_crown_trunk()
                elif self.__crown_height_code == 5:
                    lod4_valid, _ = validator.analyze_height_crown_trunk_nosphere()

            # create CityObjectMember in XML Tree
            city_object_member = ET.SubElement(self.__root, "cityObjectMember")

            # Create SolitaryVegetationObject in XML Tree
            solitary_vegetation_object = ET.SubElement(city_object_member, "veg:SolitaryVegetationObject")
            solitary_vegetation_object.set("gml:id", self.__current_tree_gmlid)

            # compare thiw row's x and y vlaues with values in bounding box object
            # boung box updates if new boundries are detected
            self.__bbox.compare(row[self.__x_value_col_index], row[self.__y_value_col_index])

            # add creationDate into the model: Today's date is always used for CreationDate
            creationdate = ET.SubElement(solitary_vegetation_object, "creationDate")
            creationdate.text = str(date.today())

            # generate generic attributes if requested
            if self.__generate_generic_attributes:
                for index, value in enumerate(row):
                    if index in used_cols:
                        continue
                    if value is None:
                        continue

                    typ = self.__col_datatypes[index]
                    col_name = self.__col_names[index]

                    if typ == "GEOM":
                        continue
                    elif typ == "INTEGER":
                        int_attribute = ET.SubElement(solitary_vegetation_object, "gen:intAttribute")
                        int_attribute.set("name", col_name)
                        val = ET.SubElement(int_attribute, "gen:value")
                        val.text = str(value)
                    elif typ == "REAL":
                        double_attribute = ET.SubElement(solitary_vegetation_object, "gen:doubleAttribute")
                        double_attribute.set("name", col_name)
                        val = ET.SubElement(double_attribute, "gen:value")
                        val.text = str(value)
                    elif typ == "TEXT":
                        string_attribute = ET.SubElement(solitary_vegetation_object, "gen:stringAttribute")
                        string_attribute.set("name", col_name)
                        val = ET.SubElement(string_attribute, "gen:value")
                        val.text = str(value)

            # Add class attribute to parameterized tree model
            if self.__class_col_index is not None and row[self.__class_col_index] is not None:
                klasse = ET.SubElement(solitary_vegetation_object, "veg:class")
                klasse.text = str(row[self.__class_col_index])

            # Add species attribute to parameterized tree model
            if self.__species_col_index is not None and row[self.__species_col_index] is not None:
                species = ET.SubElement(solitary_vegetation_object, "veg:species")
                species.text = str(row[self.__species_col_index])

            # Add hight attribute to parameterized tree model
            if self.__height_col_index is not None and row[self.__height_col_index] is not None:
                height = ET.SubElement(solitary_vegetation_object, "veg:height")
                height.text = str(tree_height)
                height.set("uom", "m")

            # Add trunk (stem) diameter attribute to parameterized tree model
            if self.__trunk_diam_col_index is not None and row[self.__trunk_diam_col_index] is not None:
                trunk = ET.SubElement(solitary_vegetation_object, "veg:trunkDiameter")
                trunk.text = str(trunk_diam)
                trunk.set("uom", "m")

            # Add crown diameter attribute to parameterized tree model
            if self.__crown_diam_col_index is not None and row[self.__crown_diam_col_index] is not None:
                crown = ET.SubElement(solitary_vegetation_object, "veg:crownDiameter")
                crown.text = str(crown_diam)
                crown.set("uom", "m")

            # Create explicit geometries
            # geomtype 0 -> linie, geomtype 1 -> cylinder, geomtype 2 -> rectangles,
            # geomtype 3 -> polygons, geomtype 4 -> cuboid, geomtype 5 -> detailled
            # vegetation class 1060 -> coniferous, vegetation class 1070 -> deciduous, anything else -> default
            if self.__geom_type == "EXPLICIT":
                # Calls methods to generate geometries for LOD1 if it is valid, depending on user input
                if self.__use_lod1 and lod1_valid:
                    lod_1_geom = ET.SubElement(solitary_vegetation_object, "veg:lod1Geometry")
                    self.__current_lod = "lod1"
                    if self.__lod1_geomtype == 0:
                        self.generate_line_geometry(lod_1_geom, x_value, y_value, ref_height, tree_height)

                    elif self.__lod1_geomtype == 1:
                        self.generate_cylinder_geometry(lod_1_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_1_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod1_segments)
                    elif self.__lod1_geomtype == 3:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod1_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod1_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod1_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod1_segments, crown_height)
                    elif self.__lod1_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod1_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod1_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod1_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_1_geom, x_value, y_value, ref_height,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod1_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_geometry_deciduous(lod_1_geom, x_value, y_value, ref_height,
                                                                 tree_height, crown_diam, trunk_diam,
                                                                 self.__lod1_segments, crown_height)
                else:
                    if self.__use_lod1:
                        invalid_lod1 += 1

                # Calls methods to generate geometries for LOD2, depending on user input
                if self.__use_lod2 and lod2_valid:
                    lod_2_geom = ET.SubElement(solitary_vegetation_object, "veg:lod2Geometry")
                    self.__current_lod = "lod2"
                    if self.__lod2_geomtype == 0:
                        self.generate_line_geometry(lod_2_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod2_geomtype == 1:
                        self.generate_cylinder_geometry(lod_2_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_2_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod2_segments)
                    elif self.__lod2_geomtype == 3:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod2_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod2_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod2_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod2_segments, crown_height)
                    elif self.__lod2_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod2_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod2_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod2_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_2_geom, x_value, y_value, ref_height,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod2_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_geometry_deciduous(lod_2_geom, x_value, y_value, ref_height,
                                                                 tree_height, crown_diam, trunk_diam,
                                                                 self.__lod2_segments, crown_height)
                else:
                    if self.__use_lod2:
                        invalid_lod2 += 1

                # Calls methods to generate geometries for LOD3, depending on user input
                if self.__use_lod3 and lod3_valid:
                    lod_3_geom = ET.SubElement(solitary_vegetation_object, "veg:lod3Geometry")
                    self.__current_lod = "lod3"
                    if self.__lod3_geomtype == 0:
                        self.generate_line_geometry(lod_3_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod3_geomtype == 1:
                        self.generate_cylinder_geometry(lod_3_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_3_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod3_segments)
                    elif self.__lod3_geomtype == 3:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod3_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod3_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod3_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod3_segments, crown_height)
                    elif self.__lod3_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod3_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod3_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod3_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_3_geom, x_value, y_value, ref_height,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod3_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_geometry_deciduous(lod_3_geom, x_value, y_value, ref_height,
                                                                 tree_height, crown_diam, trunk_diam,
                                                                 self.__lod3_segments, crown_height)
                else:
                    if self.__use_lod3:
                        invalid_lod3 += 1

                # Calls methods to generate geometries for LOD4, depending on user input
                if self.__use_lod4 and lod4_valid:
                    lod_4_geom = ET.SubElement(solitary_vegetation_object, "veg:lod4Geometry")
                    self.__current_lod = "lod4"
                    if self.__lod4_geomtype == 0:
                        self.generate_line_geometry(lod_4_geom, x_value, y_value, ref_height, tree_height)
                    elif self.__lod4_geomtype == 1:
                        self.generate_cylinder_geometry(lod_4_geom, x_value, y_value, ref_height,
                                                        tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 2:
                        self.generate_billboard_rectangle_geometry(lod_4_geom, x_value, y_value, ref_height,
                                                                   tree_height, crown_diam, self.__lod4_segments)
                    elif self.__lod4_geomtype == 3:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod4_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod4_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod4_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod4_segments, crown_height)
                    elif self.__lod4_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod4_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod4_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod4_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_4_geom, x_value, y_value, ref_height,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod4_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_geometry_deciduous(lod_4_geom, x_value, y_value, ref_height,
                                                                 tree_height, crown_diam, trunk_diam,
                                                                 self.__lod4_segments, crown_height)
                else:
                    if self.__use_lod4:
                        invalid_lod4 += 1

            # Create implicit geometries
            elif self.__geom_type == "IMPLICIT":
                if self.__use_lod1 and lod1_valid:
                    lod1_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod1ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod1_implicit_geometry, "ImplicitGeometry")
                    self.__current_lod = "lod1"

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
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_1_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod1_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_1_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod1_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_1_geom, 0, 0, 0,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod1_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_1_geom, 0, 0, 0,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod1_segments, crown_height)
                    elif self.__lod1_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_1_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_1_geom, 0, 0, 0,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod1_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod1_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_1_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod1_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_1_geom, 0, 0, 0,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod1_segments, crown_height)
                            elif self.__default_export_type == 1070:
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

                else:
                    if self.__use_lod1:
                        invalid_lod1 += 1

                # Calls methods to generate geometries for LOD2, depending on user input
                if self.__use_lod2 and lod2_valid:
                    lod2_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod2ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod2_implicit_geometry, "ImplicitGeometry")
                    self.__current_lod = "lod2"

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
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_2_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod2_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_2_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod2_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_2_geom, 0, 0, 0,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod2_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_2_geom, 0, 0, 0,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod2_segments, crown_height)
                    elif self.__lod2_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_2_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_2_geom, 0, 0, 0,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod2_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod2_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_2_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod2_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_2_geom, 0, 0, 0,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod2_segments, crown_height)
                            elif self.__default_export_type == 1070:
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

                else:
                    if self.__use_lod2:
                        invalid_lod2 += 1

                # Calls methods to generate geometries for LOD3, depending on user input
                if self.__use_lod3 and lod3_valid:
                    lod3_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod3ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod3_implicit_geometry, "ImplicitGeometry")
                    self.__current_lod = "lod3"

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
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_3_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod3_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_3_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod3_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_3_geom, 0, 0, 0,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod3_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_3_geom, 0, 0, 0,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod3_segments, crown_height)
                    elif self.__lod3_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_3_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_3_geom, 0, 0, 0,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod3_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod3_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_3_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod3_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_3_geom, 0, 0, 0,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod3_segments, crown_height)
                            elif self.__default_export_type == 1070:
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

                else:
                    if self.__use_lod3:
                        invalid_lod3 += 1

                # Calls methods to generate geometries for LOD4, depending on user input
                if self.__use_lod4 and lod4_valid:
                    lod4_implicit_geometry = ET.SubElement(solitary_vegetation_object, "veg:lod4ImplicitRepresentation")
                    implicit_geometry = ET.SubElement(lod4_implicit_geometry, "ImplicitGeometry")
                    self.__current_lod = "lod4"

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
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_billboard_polygon_coniferous(lod_4_geom, 0, 0, 0,
                                                                       tree_height, crown_diam, trunk_diam,
                                                                       self.__lod4_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_billboard_polygon_deciduous(lod_4_geom, 0, 0, 0,
                                                                      tree_height, crown_diam, trunk_diam,
                                                                      self.__lod4_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_billboard_polygon_coniferous(lod_4_geom, 0, 0, 0,
                                                                           tree_height, crown_diam, trunk_diam,
                                                                           self.__lod4_segments, crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_billboard_polygon_deciduous(lod_4_geom, 0, 0, 0,
                                                                          tree_height, crown_diam, trunk_diam,
                                                                          self.__lod4_segments, crown_height)
                    elif self.__lod4_geomtype == 4:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_cuboid_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                                     tree_height, crown_diam, trunk_diam, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index] == 1070:
                            self.generate_cuboid_geometry_deciduous(lod_4_geom, 0, 0, 0,
                                                                    tree_height, crown_diam, trunk_diam, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_cuboid_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                                         tree_height, crown_diam, trunk_diam,
                                                                         crown_height)
                            elif self.__default_export_type == 1070:
                                self.generate_cuboid_geometry_deciduous(lod_4_geom, 0, 0, 0,
                                                                        tree_height, crown_diam, trunk_diam,
                                                                        crown_height)
                    elif self.__lod4_geomtype == 5:
                        if self.__class_col_index is not None and row[self.__class_col_index] == 1060:
                            self.generate_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                              tree_height, crown_diam, trunk_diam,
                                                              self.__lod4_segments, crown_height)
                        elif self.__class_col_index is not None and row[self.__class_col_index == 1070]:
                            self.generate_geometry_deciduous(lod_4_geom, 0, 0, 0,
                                                             tree_height, crown_diam, trunk_diam,
                                                             self.__lod4_segments, crown_height)
                        else:
                            if self.__default_export_type == 1060:
                                self.generate_geometry_coniferous(lod_4_geom, 0, 0, 0,
                                                                  tree_height, crown_diam, trunk_diam,
                                                                  self.__lod4_segments, crown_height)
                            elif self.__default_export_type == 1070:
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

                else:
                    if self.__use_lod4:
                        invalid_lod4 += 1

            # update couter for valid trees
            exported_trees += 1

            # update gauge in GUI
            progressbar.SetValue(progressbar.GetValue() + 1)

        # add bounding box information to root
        self.bounded_by()

        # add appearence model
        self.add_appearance()

        # reformat to prettyprint xml output
        if self.__prettyprint:
            CityGmlExport.indent(self.__root)

        # write tree to output file
        tree = ET.ElementTree(self.__root)
        tree.write(self.__filepath, encoding="UTF-8", xml_declaration=True, method="xml")

        # return number of exported valid trees and number of trees that were not exported
        return exported_trees, invalid_lod1, invalid_lod2, invalid_lod3, invalid_lod4

    # method to add namespaces and schema location to xml file
    def add_namespaces(self):
        self.__root.set("xmlns", "http://www.opengis.net/citygml/2.0")
        self.__root.set("xmlns:xs", "https://www.w3.org/2001/XMLSchema")
        self.__root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self.__root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
        self.__root.set("xmlns:gml", "http://www.opengis.net/gml")
        self.__root.set("xmlns:veg", "http://www.opengis.net/citygml/vegetation/2.0")
        self.__root.set("xmlns:gen", "http://www.opengis.net/citygml/generics/2.0")
        self.__root.set("xmlns:app", "http://www.opengis.net/citygml/appearance/2.0")
        self.__root.set("xsi:schemaLocation",
                        "http://www.opengis.net/citygml/2.0 "
                        "http://schemas.opengis.net/citygml/2.0/cityGMLBase.xsd "
                        "http://www.opengis.net/citygml/generics/2.0 "
                        "http://schemas.opengis.net/citygml/generics/2.0/generics.xsd "
                        "http://www.opengis.net/citygml/appearance/2.0 "
                        "http://schemas.opengis.net/citygml/appearance/2.0/appearance.xsd "
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

    def add_appearance(self):
        self.add_appearance_color("0.47", "0.24", "0", self.__stem_gmlids)
        self.add_appearance_color("0.26", "0.65", "0.15", self.__crown_deciduous_gmlids)
        self.add_appearance_color("0.08", "0.37", "0", self.__crown_coniferous_gmlids)

    def add_appearance_color(self, r, g, b, id_list):
        appearance_member = ET.Element("app:appearanceMember")
        appearance = ET.SubElement(appearance_member, "app:Appearance")
        theme = ET.SubElement(appearance, "app:theme")
        theme.text = "Material"

        surface_data_member = ET.SubElement(appearance, "app:surfaceDataMember")
        x3dmaterial = ET.SubElement(surface_data_member, "app:X3DMaterial")

        front = ET.SubElement(x3dmaterial, "app:isFront")
        front.text = "true"

        diffuse_color = ET.SubElement(x3dmaterial, "app:diffuseColor")
        diffuse_color.text = "%s %s %s" % (r, g, b)

        for identifyer in id_list:
            target = ET.SubElement(x3dmaterial, "app:target")
            target.text = identifyer

        self.__root.insert(1, appearance_member)

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

        for segment in range(0, segments):
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

            # add gml id to polygon
            gml_id = "%s_%s_stempolygon%s" % (self.__current_tree_gmlid, self.__current_lod, str(segment))
            self.__stem_gmlids.append(gml_id)
            polygon.set("gml:id", gml_id)

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

            # add gml id to polygon
            gml_id = "%s_%s_crownpolygon%s" % (self.__current_tree_gmlid, self.__current_lod, str(segment))
            self.__crown_deciduous_gmlids.append(gml_id)
            polygon.set("gml:id", gml_id)

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
        for segment in range(0, segments):
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

            # add gml id to polygon
            gml_id = "%s_%s_stempolygon%s" % (self.__current_tree_gmlid, self.__current_lod, str(segment))
            self.__stem_gmlids.append(gml_id)
            polygon.set("gml:id", gml_id)

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

            # add gml id to polygon
            gml_id = "%s_%s_crownpolygon%s" % (self.__current_tree_gmlid, self.__current_lod, str(segment))
            self.__crown_coniferous_gmlids.append(gml_id)
            polygon.set("gml:id", gml_id)

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

        # add gml id to composite surface
        gml_id = "%s_%s_stem_compositesurface" % (self.__current_tree_gmlid, self.__current_lod)
        self.__stem_gmlids.append(gml_id)
        stem_exterior_composite_surface.set("gml:id", gml_id)

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

        # add gml id to composite surface
        gml_id = "%s_%s_crown_compositesurface" % (self.__current_tree_gmlid, self.__current_lod)
        self.__crown_deciduous_gmlids.append(gml_id)
        crown_exterior_composite_surface.set("gml:id", gml_id)

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

        # add gml id to composite surface
        gml_id = "%s_%s_crown_compositesurface" % (self.__current_tree_gmlid, self.__current_lod)
        self.__crown_coniferous_gmlids.append(gml_id)
        crown_exterior_composite_surface.set("gml:id", gml_id)

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

    def set_generate_generic_attributes(self, val):
        self.__generate_generic_attributes = val

    def set_col_names(self, names):
        self.__col_names = names

    def set_col_datatypes(self, types):
        self.__col_datatypes = types

    def set_prettyprint(self, value):
        self.__prettyprint = value

    def set_geomtype(self, geomtype):
        self.__geom_type = geomtype

    def set_crown_height_code(self, code):
        self.__crown_height_code = code

    def set_crown_height_col_index(self, val):
        self.__crown_height_col_index = val

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
