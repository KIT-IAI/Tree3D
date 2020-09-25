import xml.etree.ElementTree as ET
import math
from datetime import date
from time import gmtime, strftime, time
import threading
import sqlite3
import os
import json
import uuid
import string

import default_gui
import analysis
import geometry
import config

import wx


# parent GUI class for export dialog
# provides export functionality, needed by all export formats
# derived classes then make format-specific alterations to class
class ExportDialog(default_gui.CityGmlExport):
    def __init__(self, parent):
        default_gui.CityGmlExport.__init__(self, parent)
        self.__IfcVersion = None  # will only be used in Ifc Export

        self.__pathname = ""
        self.__dbpath = self.GetParent().db.get_db_filepath()
        self.__TreeTableName = self.GetParent().db.get_tree_table_name()

        self.__col_settings = self.GetParent().get_column_config()

        self.populate_dropdown()

        self.DoLayoutAdaptation()
        self.Layout()

        self.progress.SetRange(self.GetParent().db.get_number_of_tablerecords())

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

        self.load_column_selection()

    # method to load saved column selections
    def load_column_selection(self):
        coords = self.__col_settings.get_coordinates()
        if coords != (None, None):
            self.choiceXvalue.SetStringSelection(coords[0])
            self.choiceYvalue.SetStringSelection(coords[1])

        refheight = self.__col_settings.get_ref_height()
        if refheight is not None:
            self.choiceRefheight.SetStringSelection(refheight)

        treeheight = self.__col_settings.get_tree_height()
        if treeheight != (None, None):
            self.choiceHeight.SetStringSelection(treeheight[0])
            self.choiceHeightUnit.SetStringSelection(treeheight[1])

        trunk = self.__col_settings.get_trunk_diam()
        if trunk != (None, None, None):
            self.choiceTrunk.SetStringSelection(trunk[0])
            self.trunk_circ.SetStringSelection(trunk[1])
            self.choiceTrunkUnit.SetStringSelection(trunk[2])

        crown = self.__col_settings.get_crown_diam()
        if crown != (None, None, None):
            self.choiceCrown.SetStringSelection(crown[0])
            self.crown_circ.SetStringSelection(crown[1])
            self.choiceCrownUnit.SetStringSelection(crown[2])

        classe = self.__col_settings.get_class()
        if classe is not None:
            self.choiceClass.SetStringSelection(classe)

        species = self.__col_settings.get_species()
        if species is not None:
            self.choiceSpecies.SetStringSelection(species)

        crown_height = self.__col_settings.get_crown_height()
        if crown_height is not None:
            self.ChoiceCrownHeightCol.SetStringSelection(crown_height)

        self.check_geometries_to_generate(None)

    # method to be called when "Browse" button is pushed
    def on_browse(self, event):
        name_found = False

        while not name_found:
            with self.load_browse_dialog() as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                if os.path.exists(fileDialog.GetPath()):
                    msg = "This file already exists. Do you want to replace it?"
                    dlg = wx.MessageDialog(self, msg, "Fiel already exists", style=wx.CENTRE | wx.YES_NO)
                    result = dlg.ShowModal()
                    if result == wx.ID_YES:
                        name_found = True
                else:
                    name_found = True

                self.__pathname = fileDialog.GetPath()

        self.filepat_textbox.SetValue(self.__pathname)

    # method to load correct browse dialog (overwritten in subclass)
    def load_browse_dialog(self):
        pass

    # method to be called when "export" button is pressed in export GUI
    def on_export(self, event):
        valid, warningmessage = self.validate_input()
        if not valid:
            msg = wx.MessageDialog(self, warningmessage, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()
            return

        self.buttonExport.Enable(False)

        self.save_column_selection()

        # new thread in which the export takes place
        thread = threading.Thread(target=self.start_export)
        thread.start()

    # method to start export (in a new thread)
    def start_export(self):
        classname = type(self).__name__
        if classname == "ExportDialogCityGML":
            exporter = CityGmlExport(self.__pathname, self.__dbpath)
        elif classname == "ExportDialogCityJson":
            exporter = CityJSONExport(self.__pathname, self.__dbpath)
        elif classname == "ExportDialogIfc":
            exporter = IfcExport(self.__pathname, self.__dbpath, self.__IfcVersion)
        else:
            exporter = GeoJSONExport(self.__pathname, self.__dbpath)
            exporter.setup_transformer(int(self.epsg.GetValue()), 4326)

        exporter.set_tree_table_name(self.__TreeTableName)

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
                                "rectangles": 2,
                                "tree contour polygons": 3,
                                "highly simplified tree": 4,
                                "simplified tree": 5,
                                "point": 6}

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

        # use appearance model and assign materials to polygons
        # value is only set to true, if a supported geometry is exported
        if self.use_appearance.GetValue():
            exporter.set_use_appearance(True)

        if classname == "ExportDialogIfc":
            exporter.generate_header()
            exporter.start_data_section()

        # start the export
        export_status = exporter.export(self.progress)
        # save file
        exporter.save_file()

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
        msg = wx.MessageDialog(self, message, caption="Export finnished", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()

        # reset gauge to 0
        self.progress.SetValue(0)
        self.buttonExport.Enable(True)

    def set_ifc_version(self, ifc_version):
        self.__IfcVersion = ifc_version

    # method is called when dropdown on how to calculated crown height is changed
    def on_crown_height_options(self, event):
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
        x = self.choiceXvalue.GetSelection()
        y = self.choiceYvalue.GetSelection()
        ref_height = self.choiceRefheight.GetSelection()

        height = self.choiceHeight.GetSelection()
        stem = self.choiceTrunk.GetSelection()
        crown = self.choiceCrown.GetSelection()

        geom_types = []

        if wx.NOT_FOUND not in [x, y, ref_height]:
            geom_types.append("point")

        if height != wx.NOT_FOUND:
            geom_types.append("line")

        if height != wx.NOT_FOUND and crown != wx.NOT_FOUND:
            geom_types.append("cylinder")
            geom_types.append("rectangles")

        if height != wx.NOT_FOUND and crown != wx.NOT_FOUND and stem != wx.NOT_FOUND:
            geom_types.append("tree contour polygons")
            geom_types.append("highly simplified tree")
            geom_types.append("simplified tree")

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

        # code is executed when checkbox is disabled
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

        # code is executed when checkbox is disabled
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

        # code is executed when checkbox is disabled
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

        # code is executed when checkbox is disabled
        if not val:
            self.lod4_geomtype.SetSelection(0)
            self.lod4_segments_text.Show(val)
            self.lod4_segments.Show(val)

    # method is called when LOD1-geomtype choice changes: enables/disables further geomtype options
    def on_lod1_choice(self, event):
        val = self.lod1_geomtype.GetSelection()
        if val == 2 or val == 3 or val == 4 or val == 6:
            self.lod1_segments_text.Show(True)
            self.lod1_segments.Show(True)
        else:
            self.lod1_segments_text.Show(False)
            self.lod1_segments.Show(False)

        if val == 3 or val == 4:
            self.lod1_segments.SetItems(["4", "6", "8"])
            self.lod1_segments.SetSelection(0)
        elif val == 2 or val == 6:
            self.lod1_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod1_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD2-geomtype choice changes: enables/disables further geomtype options
    def on_lod2_choice(self, event):
        val = self.lod2_geomtype.GetSelection()
        if val == 2 or val == 3 or val == 4 or val == 6:
            self.lod2_segments_text.Show(True)
            self.lod2_segments.Show(True)
        else:
            self.lod2_segments_text.Show(False)
            self.lod2_segments.Show(False)

        if val == 3 or val == 4:
            self.lod2_segments.SetItems(["4", "6", "8"])
            self.lod2_segments.SetSelection(0)
        elif val == 2 or val == 6:
            self.lod2_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod2_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD3-geomtype choice changes: enables/disables further geomtype options
    def on_lod3_choice(self, event):
        val = self.lod3_geomtype.GetSelection()
        if val == 2 or val == 3 or val == 4 or val == 6:
            self.lod3_segments_text.Show(True)
            self.lod3_segments.Show(True)
        else:
            self.lod3_segments_text.Show(False)
            self.lod3_segments.Show(False)

        if val == 3 or val == 4:
            self.lod3_segments.SetItems(["4", "6", "8"])
            self.lod3_segments.SetSelection(0)
        elif val == 2 or val == 6:
            self.lod3_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod3_segments.SetSelection(1)
        self.Layout()

    # method is called when LOD4-geomtype choice changes: enables/disables further geomtype options
    def on_lod4_choice(self, event):
        val = self.lod4_geomtype.GetSelection()
        if val == 2 or val == 3 or val == 4 or val == 6:
            self.lod4_segments_text.Show(True)
            self.lod4_segments.Show(True)
        else:
            self.lod4_segments_text.Show(False)
            self.lod4_segments.Show(False)

        if val == 3 or val == 4:
            self.lod4_segments.SetItems(["4", "6", "8"])
            self.lod4_segments.SetSelection(0)
        elif val == 2 or val == 6:
            self.lod4_segments.SetItems(["5", "10", "15", "18", "20", "30"])
            self.lod4_segments.SetSelection(1)
        self.Layout()

    # method to validate user input and show error message is user input is invalid
    def validate_input(self):
        valid = True
        warningmessage = ""

        # check, if geom output differenciates between tree classes, and if a class column or default class is set
        distinct_geoms = ["tree contour polygons", "highly simplified tree", "simplified tree"]
        if self.lod4.GetValue() and self.lod4_geomtype.GetStringSelection() in distinct_geoms \
                and self.choiceClass.GetSelection() == wx.NOT_FOUND \
                and self.default_choice.GetStringSelection() == "none":
            valid = False
            warningmessage = "LOD4 differentiates between deciduous trees and coniferous trees\n" \
                             "Please select tree class column or define a default tree class"

        if self.lod3.GetValue() and self.lod3_geomtype.GetStringSelection() in distinct_geoms \
                and self.choiceClass.GetSelection() == wx.NOT_FOUND \
                and self.default_choice.GetStringSelection() == "none":
            valid = False
            warningmessage = "LOD3 differentiates between deciduous trees and coniferous trees\n" \
                             "Please select tree class column or define a default tree class"

        if self.lod2.GetValue() and self.lod2_geomtype.GetStringSelection() in distinct_geoms \
                and self.choiceClass.GetSelection() == wx.NOT_FOUND \
                and self.default_choice.GetStringSelection() == "none":
            valid = False
            warningmessage = "LOD2 differentiates between deciduous trees and coniferous trees\n" \
                             "Please select tree class column or define a default tree class"

        if self.lod1.GetValue() and self.lod1_geomtype.GetStringSelection() in distinct_geoms \
                and self.choiceClass.GetSelection() == wx.NOT_FOUND \
                and self.default_choice.GetStringSelection() == "none":
            valid = False
            warningmessage = "LOD1 differentiates between deciduous trees and coniferous trees\n" \
                             "Please select tree class column or define a default tree class"

        # check for duplicate selected columns
        test_list = [self.choiceXvalue, self.choiceYvalue, self.choiceRefheight, self.choiceHeight, self.choiceTrunk,
                     self.choiceCrown, self.choiceSpecies, self.choiceClass, self.ChoiceCrownHeightCol]
        test_dict = {self.choiceXvalue: "Easting",
                     self.choiceYvalue: "Northing",
                     self.choiceRefheight: "Reference Height",
                     self.choiceHeight: "Tree height",
                     self.choiceTrunk: "Trunk diameter",
                     self.choiceCrown: "Crown diameter",
                     self.choiceSpecies: "Species code",
                     self.choiceClass: "Class code",
                     self.ChoiceCrownHeightCol: "Crown height"}

        for i in range(0, len(test_list)):
            for j in range(i+1, len(test_list)):
                if test_list[i].GetSelection() != wx.NOT_FOUND \
                        and test_list[i].GetStringSelection() == test_list[j].GetStringSelection():
                    valid = False
                    warningmessage = "%s and %s must not be the same column"\
                                     % (test_dict[test_list[i]], test_dict[test_list[j]])

        # check, if epsg is integer
        try:
            int(self.epsg.GetValue())
        except:
            valid = False
            warningmessage = "EPSG Code must be an integer number."

        # check epsg code isnt empty
        if self.epsg.GetValue() == "":
            valid = False
            warningmessage = "EPSG Code must not be empty."

        # check, if required columns are specified
        if self.crown_height_choice.GetSelection() == 5 and self.ChoiceCrownHeightCol.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Crown height columnn must be specified"

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

        return valid, warningmessage

    # save selected column entries for further use
    def save_column_selection(self):
        xcol = self.choiceXvalue.GetStringSelection()
        ycol = self.choiceYvalue.GetStringSelection()
        self.__col_settings.set_coordinates(xcol, ycol)

        self.__col_settings.set_ref_height(self.choiceRefheight.GetStringSelection())

        if self.choiceHeight.GetSelection() != wx.NOT_FOUND:
            col = self.choiceHeight.GetStringSelection()
            unit = self.choiceHeightUnit.GetStringSelection()
            self.__col_settings.set_tree_height(col, unit)

        if self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
            col = self.choiceTrunk.GetStringSelection()
            mode = self.trunk_circ.GetStringSelection()
            unit = self.choiceTrunkUnit.GetStringSelection()
            self.__col_settings.set_trunk_diam(col, mode, unit)

        if self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            col = self.choiceCrown.GetStringSelection()
            mode = self.crown_circ.GetStringSelection()
            unit = self.choiceCrownUnit.GetStringSelection()
            self.__col_settings.set_crown_diam(col, mode, unit)

        if self.choiceClass.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_class(self.choiceClass.GetStringSelection())

        if self.choiceSpecies.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_species(self.choiceSpecies.GetStringSelection())

        if self.ChoiceCrownHeightCol.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_crown_height(self.ChoiceCrownHeightCol.GetStringSelection())


# Export GUI for CityGML export
class ExportDialogCityGML(ExportDialog):
    def __init__(self, parent):
        ExportDialog.__init__(self, parent)

    # method to generate browse dialog in export gui
    def load_browse_dialog(self):
        dlg = wx.FileDialog(self, "Export as CityGML", wildcard="CityGML (*.citygml)|*.citygml", style=wx.FD_SAVE)
        return dlg


# Export GUI for CityJSON export
class ExportDialogCityJson(ExportDialog):
    def __init__(self, parent):
        ExportDialog.__init__(self, parent)

        # renaming some GUI elements
        self.SetTitle("Export as CityJSON")
        self.box_prettyprint.SetLabel("Create pretty-printed JSON output (may be slow for large datasets)")

        self.lod4.Hide()
        self.lod4_geomtype.Hide()
        self.lod4_segments.Hide()
        self.lod4_segments_text.Hide()

        self.DoLayoutAdaptation()
        self.Layout()

    # method to generate browse dialog in export gui
    def load_browse_dialog(self):
        dlg = wx.FileDialog(self, "Export as CityJSON", wildcard="CityJSON (*.json)|*.json", style=wx.FD_SAVE)
        return dlg


class ExportDialogGeoJson(ExportDialog):
    def __init__(self, parent):
        ExportDialog.__init__(self, parent)

        # renaming some GUI elements
        self.SetTitle("Export as GeoJSON")
        self.box_prettyprint.SetLabel("Create pretty-printed JSON output (may be slow for large datasets)")

        self.implicit_geom.Hide()
        self.explicit_geom.Hide()
        self.m_staticText62.Hide()

        self.lod4.Hide()
        self.lod4_geomtype.Hide()
        self.lod4_segments.Hide()
        self.lod4_segments_text.Hide()

        self.lod3.Hide()
        self.lod3_geomtype.Hide()
        self.lod3_segments.Hide()
        self.lod3_segments_text.Hide()

        self.lod2.Hide()
        self.lod2_geomtype.Hide()
        self.lod2_segments.Hide()
        self.lod2_segments_text.Hide()

        self.lod1.SetValue(True)
        self.lod1_geomtype.Enable(True)

        self.DoLayoutAdaptation()
        self.Layout()

    def load_browse_dialog(self):
        dlg = wx.FileDialog(self, "Export as GeoJSON", wildcard="GeoJSON (*.json)|*.json", style=wx.FD_SAVE)
        return dlg

    def on_lod1_checkbox(self, event):
        self.lod1.SetValue(True)
        message = "Cannot suppress geometry output in GeoJSON"
        msg = wx.MessageDialog(self, message, caption="Info", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()

    def validate_input(self):
        valid = True
        warningmessage = ""

        super_valid, super_warningmessage = ExportDialog.validate_input(self)

        if self.lod1_geomtype.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Please select LOD1 geometry"

        if not super_valid:
            valid = super_valid
            warningmessage = super_warningmessage

        return valid, warningmessage


class ExportDialogIfc(ExportDialog):
    def __init__(self, parent):
        ExportDialog.__init__(self, parent)

        # rename some GUI elements
        self.SetTitle("Export as IFC")
        self.box_prettyprint.Hide()

        self.implicit_geom.SetValue(True)
        self.implicit_geom.Hide()
        self.explicit_geom.Hide()
        self.m_staticText62.Hide()

        self.lod4.Hide()
        self.lod4_geomtype.Hide()
        self.lod4_segments.Hide()
        self.lod4_segments_text.Hide()

        self.lod3.Hide()
        self.lod3_geomtype.Hide()
        self.lod3_segments.Hide()
        self.lod3_segments_text.Hide()

        self.lod2.Hide()
        self.lod2_geomtype.Hide()
        self.lod2_segments.Hide()
        self.lod2_segments_text.Hide()

        self.lod1.SetValue(True)
        self.lod1_geomtype.Enable(True)

        self.DoLayoutAdaptation()
        self.Layout()

    def on_lod1_checkbox(self, event):
        self.lod1.SetValue(True)
        message = "Cannot suppress geometry output in IFC"
        msg = wx.MessageDialog(self, message, caption="Info", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
        msg.ShowModal()

    def validate_input(self):
        valid = True
        warningmessage = ""

        super_valid, super_warningmessage = ExportDialog.validate_input(self)

        if self.lod1_geomtype.GetSelection() == wx.NOT_FOUND:
            valid = False
            warningmessage = "Please select LOD1 geometry"

        if not super_valid:
            valid = super_valid
            warningmessage = super_warningmessage

        return valid, warningmessage

    # method to generate browse dialog in export gui
    def load_browse_dialog(self):
        dlg = wx.FileDialog(self, "Export as IFC", wildcard="IFC (*.ifc)|*.ifc", style=wx.FD_SAVE)
        return dlg


# Class to perform the export itself
class Export:
    def __init__(self, savepath, dbfilepath):
        self._con = sqlite3.connect(dbfilepath)
        self._DataCursor = self._con.cursor()  # Data cursor table from database (list of lists)
        self._TreeTableName = ""

        self._filepath = savepath  # output file path (where citygml will be saved)

        self._prettyprint = None  # boolean variable to determine if xml output should be formatted

        self._generate_generic_attributes = None  # variable to generate generic attributes (Trud/False)

        self._bbox = analysis.BoundingBox()  # Bounding box object

        self._col_datatypes = None  # list of data types of columns
        self._col_names = None  # list of names all columns

        self._x_value_col_index = None  # index of column in which x value is stored
        self._y_value_col_index = None  # index of column in which y value is stored
        self._ref_height_col_index = None  # index of column in which reference height is stored
        self._EPSG = None  # EPSG-Code of coordinates
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

        self.__crown_height_code = None  # configures how crown hight should be calulated (only values between 0-4)
        self.__crown_height_col_index = None

        self._default_export_type = None  # decides what tree type should be used if it is not clear (1060 or 1070)

        self._geom_type = ""  # configures geom type: Only EXPLICIT or IMPLICIT are allowed values

        self._use_lod1 = False  # variable determines if LOD1 is generated
        self._lod1_geomtype = None  # variable determines type of geometry that should be generated for LOD1 (0-5)
        self._lod1_segments = None  # variable determines number of segments to be used in geometry (not always used)

        self._use_appearance = False  # variable to determine if appearance model should be used
        self._stem_ids = []  # stores ids of all trunk geometries
        self._crown_deciduous_ids = []  # stores ids of all deciduous crown geometries
        self._crown_coniferous_ids = []  # stores ids of all coniferous crown geometries

    # method to set option if pretty print should be used
    def set_prettyprint(self, value):
        self._prettyprint = value

    # method to set option if generic attributes should be used
    def set_generate_generic_attributes(self, val):
        self._generate_generic_attributes = val

    def set_tree_table_name(self, name):
        self._TreeTableName = name

    def set_col_names(self, names):
        self._col_names = names

    def set_col_datatypes(self, types):
        self._col_datatypes = types

    def set_x_col_idx(self, idx):
        self._x_value_col_index = idx

    def set_y_col_idx(self, idx):
        self._y_value_col_index = idx

    def set_ref_height_col_idx(self, idx):
        self._ref_height_col_index = idx

    def set_epsg(self, epsg_code):
        self._EPSG = epsg_code

    def set_height_col_index(self, idx):
        self.__height_col_index = idx

    def set_height_unit(self, unit):
        self.__height_unit = unit

    def set_trunk_diam_col_index(self, idx):
        self.__trunk_diam_col_index = idx

    def set_trunk_diam_unit(self, unit):
        self.__trunk_diam_unit = unit

    def set_trunk_is_circ(self, val):
        self.__trunk_is_circ = val

    def set_crown_diam_col_index(self, idx):
        self.__crown_diam_col_index = idx

    def set_crown_diam_unit(self, unit):
        self.__crown_diam_unit = unit

    def set_crown_is_circ(self, val):
        self.__crown_is_circ = val

    def set_species_col_index(self, index):
        self.__species_col_index = index

    def set_class_col_index(self, index):
        self.__class_col_index = index

    def set_crown_height_code(self, code):
        self.__crown_height_code = code

    def set_crown_height_col_index(self, val):
        self.__crown_height_col_index = val

    def set_default_export_type(self, typ):
        self._default_export_type = typ

    def set_geomtype(self, geomtype):
        self._geom_type = geomtype

    # method to setup LOD1 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod1(self, value, geomtype, segments=None):
        self._use_lod1 = value
        self._lod1_geomtype = geomtype
        if segments is not None:
            self._lod1_segments = segments

    def set_use_appearance(self, val):
        supported_geoms = [3, 4, 5]
        if self._lod1_geomtype in supported_geoms:
            self._use_appearance = val

    # method adds data to cursor again, so it can be iterated
    def fill_data_cursor(self):
        if self._col_names[0] != "ROWID":
            self._DataCursor.execute("SELECT * FROM %s" % self._TreeTableName)
        else:
            self._DataCursor.execute("SELECT ROWID, * FROM %s" % self._TreeTableName)

    # method to perform export
    # generates an internal tree model for each tree
    # internal tree model is later converted to format-specific tree model
    def export(self, progressbar):
        exported_trees = 0
        invalid_lod1 = 0
        invalid_lod2 = 0
        invalid_lod3 = 0
        invalid_lod4 = 0

        # list to keep track of what columns are used. All other will be used for generic attributes
        used_cols = [self._x_value_col_index,
                     self._y_value_col_index,
                     self._ref_height_col_index,
                     self.__height_col_index,
                     self.__crown_diam_col_index,
                     self.__trunk_diam_col_index,
                     self.__class_col_index,
                     self.__species_col_index]

        self.fill_data_cursor()

        for row in self._DataCursor:
            tree_model = TreeModel()

            tree_model.set_id("tree%s" % exported_trees)

            # assign geometric values to variables
            x_value = row[self._x_value_col_index]
            y_value = row[self._y_value_col_index]
            ref_height = row[self._ref_height_col_index]
            tree_model.set_position(self._EPSG, x_value, y_value, ref_height)

            # compare thiw row's x and y vlaues with values in bounding box object
            # boung box updates if new boundries are detected
            self._bbox.compare(x_value, y_value)

            # Add class attribute to parameterized tree model
            if self.__class_col_index is not None and row[self.__class_col_index] is not None:
                tree_model.set_class(row[self.__class_col_index])

            # Add species attribute to parameterized tree model
            if self.__species_col_index is not None and row[self.__species_col_index] is not None:
                tree_model.set_species(row[self.__species_col_index])

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
                crown_height = (2 / 3.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 3:
                crown_height = (3 / 4.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 4:
                crown_height = (4 / 5.0) * tree_height
            elif tree_height is not None and self.__crown_height_code == 5:
                crown_height = row[self.__crown_height_col_index]

            # converting everything into its correct units
            # converting cm -> m and circumferences -> diameter
            if self.__height_col_index is not None and self.__height_unit == "cm":
                tree_height = tree_height / 100.0

            if self.__trunk_diam_col_index is not None and trunk_diam is not None:
                if self.__trunk_diam_unit == "cm":
                    trunk_diam = trunk_diam / 100.0
                if self.__trunk_is_circ:
                    trunk_diam = trunk_diam / math.pi

            if self.__crown_diam_col_index is not None and crown_diam is not None:
                if self.__crown_diam_unit == "cm":
                    crown_diam = crown_diam / 100.0
                if self.__crown_is_circ:
                    crown_diam = crown_diam / math.pi

            tree_model.set_height(tree_height)
            tree_model.set_trunkdiam(trunk_diam)
            tree_model.set_crowndiam(crown_diam)
            tree_model.set_crownheight(crown_height)

            for index, value in enumerate(row):
                if index in used_cols:
                    continue
                if value is None:
                    continue

                typ = self._col_datatypes[index]
                col_name = self._col_names[index]

                if typ == "GEOM":
                    continue
                elif typ == "INTEGER":
                    tree_model.add_generic("int", col_name, value)
                elif typ == "REAL":
                    tree_model.add_generic("float", col_name, value)
                elif typ == "TEXT":
                    tree_model.add_generic("string", col_name, value)

            validator = analysis.AnalyzeTreeGeoms(x_value, y_value, ref_height,
                                                  tree_height, trunk_diam, crown_diam, crown_height)
            lod1, lod2, lod3, lod4 = self.generate_geometries(tree_model, validator)

            if lod1 is False:
                invalid_lod1 += 1
            if lod2 is False:
                invalid_lod2 += 1
            if lod3 is False:
                invalid_lod3 += 1
            if lod4 is False:
                invalid_lod4 += 1

            self.add_tree_to_model(tree_model)

            # update couter for valid trees
            exported_trees += 1

            # update gauge in GUI
            progressbar.SetValue(progressbar.GetValue() + 1)

        self.bounded_by()
        if self._use_appearance:
            self.add_appearance(progressbar)
        self._con.close()

        # return number of exported valid trees and number of trees that were not exported
        return exported_trees, invalid_lod1, invalid_lod2, invalid_lod3, invalid_lod4

    # method is overwritten in subclasses
    def add_tree_to_model(self, tree_model):
        pass

    # method to generate geometric models for LOD1
    def generate_geometries(self, treemodel, validator):
        # validate tree parameters for LOD1 geometry
        lod1_valid = True

        # generate LOD1 geometry
        if self._use_lod1:
            lod1_valid = self.validate_geometry(validator, self._lod1_geomtype)
            if lod1_valid:
                lod1_geom_obj = self.get_geometry(treemodel, self._lod1_geomtype, self._lod1_segments, "lod1")
                treemodel.set_lod1model(lod1_geom_obj)

        return lod1_valid, True, True, True

    # method to validate geometric parameters before geometry creation
    def validate_geometry(self, validator, geomtype):
        valid = False

        if geomtype == 0:
            valid, _ = validator.analyze_height()
        elif geomtype == 1 or geomtype == 2:
            valid, _ = validator.analyze_height_crown()
        elif geomtype == 3 or geomtype == 4 or geomtype == 5:
            if self.__crown_height_code == 0:
                valid, _ = validator.analyze_height_crown_trunk_sphere()
            elif 0 < self.__crown_height_code < 5:
                valid, _ = validator.analyze_height_crown_trunk()
            elif self.__crown_height_code == 5:
                valid, _ = validator.analyze_height_crown_trunk_nosphere()
        elif geomtype == 6:
            valid, _ = validator.analyze_coordinates()

        return valid

    # Method to initiate creation of geometric tree models
    def get_geometry(self, treemodel, geomtype, segments, lod):
        geom_obj = None
        tree_class = treemodel.get_class()

        stem_ids = []
        crown_ids_coni = []
        crown_ids_deci = []

        if geomtype == 0:
            geom_obj = generate_line_geometry(treemodel, self._geom_type)
        elif geomtype == 1:
            geom_obj = generate_cylinder_geometry(treemodel, segments, self._geom_type)
        elif geomtype == 2:
            geom_obj = generate_billboard_rectangle_geometry(treemodel, segments, self._geom_type)
        elif geomtype == 3:
            if self.__class_col_index is not None and tree_class == 1060:
                geom_obj, stem_ids, crown_ids_coni = generate_billboard_polygon_coniferous(treemodel, segments, self._geom_type, lod)
            elif self.__class_col_index is not None and tree_class == 1070:
                geom_obj, stem_ids, crown_ids_deci = generate_billboard_polygon_deciduous(treemodel, segments, self._geom_type, lod)
            else:
                if self._default_export_type == 1060:
                    geom_obj, stem_ids, crown_ids_coni = generate_billboard_polygon_coniferous(treemodel, segments, self._geom_type, lod)
                elif self._default_export_type == 1070:
                    geom_obj, stem_ids, crown_ids_deci = generate_billboard_polygon_deciduous(treemodel, segments, self._geom_type, lod)
        elif geomtype == 4:
            if self.__class_col_index is not None and tree_class == 1060:
                geom_obj, stem_ids, crown_ids_coni = generate_cuboid_geometry_coniferous(treemodel, self._geom_type, lod)
            elif self.__class_col_index is not None and tree_class == 1070:
                geom_obj, stem_ids, crown_ids_deci = generate_cuboid_geometry_deciduous(treemodel, self._geom_type, lod)
            else:
                if self._default_export_type == 1060:
                    geom_obj, stem_ids, crown_ids_coni = generate_cuboid_geometry_coniferous(treemodel, self._geom_type, lod)
                elif self._default_export_type == 1070:
                    geom_obj, stem_ids, crown_ids_deci = generate_cuboid_geometry_deciduous(treemodel, self._geom_type, lod)
        elif geomtype == 5:
            if self.__class_col_index is not None and tree_class == 1060:
                geom_obj, stem_ids, crown_ids_coni = generate_geometry_coniferous(treemodel, segments, self._geom_type, lod)
            elif self.__class_col_index is not None and tree_class == 1070:
                geom_obj, stem_ids, crown_ids_deci = generate_geometry_deciduous(treemodel, segments, self._geom_type, lod)
            else:
                if self._default_export_type == 1060:
                    geom_obj, stem_ids, crown_ids_coni = generate_geometry_coniferous(treemodel, segments, self._geom_type, lod)
                elif self._default_export_type == 1070:
                    geom_obj, stem_ids, crown_ids_deci = generate_geometry_deciduous(treemodel, segments, self._geom_type, lod)
        elif geomtype == 6:
            geom_obj = generate_point_geometry(treemodel, self._geom_type)

        self._stem_ids.extend(stem_ids)
        self._crown_coniferous_ids.extend(crown_ids_coni)
        self._crown_deciduous_ids.extend(crown_ids_deci)
        return geom_obj

    def bounded_by(self):
        pass

    def add_appearance(self, progressbar):
        pass


class CityModelExport(Export):
    def __init__(self, savepath, dbfilepath):
        Export.__init__(self, savepath, dbfilepath)

        self._use_lod2 = False
        self._lod2_geomtype = None
        self._lod2_segments = None

        self._use_lod3 = False
        self._lod3_geomtype = None
        self._lod3_segments = None

    # method to set option if appearance should be used
    def set_use_appearance(self, val):
        supported_geoms = [3, 4, 5]
        if self._lod1_geomtype in supported_geoms or self._lod2_geomtype in supported_geoms or self._lod3_geomtype in supported_geoms:
            self._use_appearance = val

    # method to setup LOD2 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod2(self, value, geomtype, segments=None):
        self._use_lod2 = value
        self._lod2_geomtype = geomtype
        if segments is not None:
            self._lod2_segments = segments

    # method to setup LOD3 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod3(self, value, geomtype, segments=None):
        self._use_lod3 = value
        self._lod3_geomtype = geomtype
        if segments is not None:
            self._lod3_segments = segments

    # method to generate geometric tree models for LOD2 and LOD3
    def generate_geometries(self, treemodel, validator):
        lod1_valid, lod2_valid, lod3_valid, _ = super().generate_geometries(treemodel, validator)

        # generate LOD2 geometry
        if self._use_lod2:
            lod2_valid = self.validate_geometry(validator, self._lod2_geomtype)
            if lod2_valid:
                lod2_geom_obj = self.get_geometry(treemodel, self._lod2_geomtype, self._lod2_segments, "lod2")
                treemodel.set_lod2model(lod2_geom_obj)

        # generate LOD3 geometry
        if self._use_lod3:
            lod3_valid = self.validate_geometry(validator, self._lod3_geomtype)
            if lod3_valid:
                lod3_geom_obj = self.get_geometry(treemodel, self._lod3_geomtype, self._lod3_segments, "lod3")
                treemodel.set_lod3model(lod3_geom_obj)

        return lod1_valid, lod2_valid, lod3_valid, True


# Class containing CityGML-specific export methods and options
class CityGmlExport(CityModelExport):
    def __init__(self, savepath, dbfilepath):
        CityModelExport.__init__(self, savepath, dbfilepath)
        self.__root = ET.Element("CityModel")
        self.add_namespaces()

        self.__use_lod4 = False
        self.__lod4_geomtype = None
        self.__lod4_segments = None

        self.__current_tree_gmlid = ""  # variable to save gml:id of tree that is currently generated

    # method to save Element Tree to XML file
    def save_file(self):
        # reformat to prettyprint xml output
        if self._prettyprint:
            CityGmlExport.indent(self.__root)

        # write tree to output file
        tree = ET.ElementTree(self.__root)
        tree.write(self._filepath, encoding="UTF-8", xml_declaration=True, method="xml")

    # method to add a tree to CityGML-model
    # converts internal tree model into CityGML SolitaryVegetationObject tree model
    def add_tree_to_model(self, tree_model):

        # create CityObjectMember in XML Tree
        city_object_member = ET.SubElement(self.__root, "cityObjectMember")

        # Create SolitaryVegetationObject in XML Tree
        solitary_vegetation_object = ET.SubElement(city_object_member, "veg:SolitaryVegetationObject")
        solitary_vegetation_object.set("gml:id", tree_model.get_id())

        # add creationDate into the model: Today's date is always used for CreationDate
        creationdate = ET.SubElement(solitary_vegetation_object, "creationDate")
        creationdate.text = str(date.today())

        # add generic attributes
        if self._generate_generic_attributes:
            for attribute in tree_model.get_generics():
                typ = attribute[0]
                name = attribute[1]
                val = attribute[2]

                if typ == "int":
                    gen_int = ET.SubElement(solitary_vegetation_object, "gen:intAttribute")
                    gen_int.set("name", str(name))
                    value = ET.SubElement(gen_int, "gen:value")
                    value.text = str(val)
                if typ == "float":
                    gen_double = ET.SubElement(solitary_vegetation_object, "gen:doubleAttribute")
                    gen_double.set("name", str(name))
                    value = ET.SubElement(gen_double, "gen:value")
                    value.text = str(val)
                if typ == "string":
                    gen_string = ET.SubElement(solitary_vegetation_object, "gen:stringAttribute")
                    gen_string.set("name", str(name))
                    value = ET.SubElement(gen_string, "gen:value")
                    value.text = str(val)

        # Add class to parametrized tree model
        classe = tree_model.get_class()
        if classe is not None:
            classnode = ET.SubElement(solitary_vegetation_object, "veg:class")
            classnode.text = str(classe)

        # Add species to parametrized tree model
        species = tree_model.get_species()
        if species is not None:
            speciesnode = ET.SubElement(solitary_vegetation_object, "veg:species")
            speciesnode.text = str(species)

        # Add hight attribute to parameterized tree model
        height = tree_model.get_height()
        if height is not None:
            heightnode = ET.SubElement(solitary_vegetation_object, "veg:height")
            heightnode.text = str(height)
            heightnode.set("uom", "m")

        # Add trunk (stem) diameter attribute to parameterized tree model
        trunkdiam = tree_model.get_trunkdiam()
        if trunkdiam is not None:
            trunk = ET.SubElement(solitary_vegetation_object, "veg:trunkDiameter")
            trunk.text = str(trunkdiam)
            trunk.set("uom", "m")

        # Add crown diameter attribute to parameterized tree model
        crowndiam = tree_model.get_crowndiam()
        if crowndiam is not None:
            crown = ET.SubElement(solitary_vegetation_object, "veg:crownDiameter")
            crown.text = str(crowndiam)
            crown.set("uom", "m")

        # add explicit geometries
        if self._geom_type == "EXPLICIT":
            if self._use_lod1:
                geom = tree_model.get_lod1model()
                if geom is not None:
                    lod1_node = ET.SubElement(solitary_vegetation_object, "veg:lod1Geometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    lod1_node.append(geom_node)

            if self._use_lod2:
                geom = tree_model.get_lod2model()
                if geom is not None:
                    lod2_node = ET.SubElement(solitary_vegetation_object, "veg:lod2Geometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    lod2_node.append(geom_node)

            if self._use_lod3:
                geom = tree_model.get_lod3model()
                if geom is not None:
                    lod3_node = ET.SubElement(solitary_vegetation_object, "veg:lod3Geometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    lod3_node.append(geom_node)

            if self.__use_lod4:
                geom = tree_model.get_lod4model()
                if geom is not None:
                    lod4_node = ET.SubElement(solitary_vegetation_object, "veg:lod4Geometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    lod4_node.append(geom_node)

        # Add implicit geometries
        elif self._geom_type == "IMPLICIT":
            if self._use_lod1:
                geom = tree_model.get_lod1model()
                if geom is not None:
                    implicit_node = ET.SubElement(solitary_vegetation_object, "veg:lod1ImplicitRepresentation")
                    implicit_geom = ET.SubElement(implicit_node, "ImplicitGeometry")
                    matrix = ET.SubElement(implicit_geom, "transformationMatrix")
                    matrix.text = "1 0 0 0 " \
                                  "0 1 0 0 " \
                                  "0 0 1 0 " \
                                  "0 0 0 1"

                    relative_geom = ET.SubElement(implicit_geom, "relativeGMLGeometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    relative_geom.append(geom_node)
                    ref_point = ET.SubElement(implicit_geom, "referencePoint")
                    point = tree_model.get_position().get_citygml_geometric_representation()
                    ref_point.append(point)

            if self._use_lod2:
                geom = tree_model.get_lod2model()
                if geom is not None:
                    implicit_node = ET.SubElement(solitary_vegetation_object, "veg:lod2ImplicitRepresentation")
                    implicit_geom = ET.SubElement(implicit_node, "ImplicitGeometry")
                    matrix = ET.SubElement(implicit_geom, "transformationMatrix")
                    matrix.text = "1 0 0 0 " \
                                  "0 1 0 0 " \
                                  "0 0 1 0 " \
                                  "0 0 0 1"

                    relative_geom = ET.SubElement(implicit_geom, "relativeGMLGeometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    relative_geom.append(geom_node)
                    ref_point = ET.SubElement(implicit_geom, "referencePoint")
                    point = tree_model.get_position().get_citygml_geometric_representation()
                    ref_point.append(point)

            if self._use_lod3:
                geom = tree_model.get_lod3model()
                if geom is not None:
                    implicit_node = ET.SubElement(solitary_vegetation_object, "veg:lod3ImplicitRepresentation")
                    implicit_geom = ET.SubElement(implicit_node, "ImplicitGeometry")
                    matrix = ET.SubElement(implicit_geom, "transformationMatrix")
                    matrix.text = "1 0 0 0 " \
                                  "0 1 0 0 " \
                                  "0 0 1 0 " \
                                  "0 0 0 1"

                    relative_geom = ET.SubElement(implicit_geom, "relativeGMLGeometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    relative_geom.append(geom_node)
                    ref_point = ET.SubElement(implicit_geom, "referencePoint")
                    point = tree_model.get_position().get_citygml_geometric_representation()
                    ref_point.append(point)

            if self.__use_lod4:
                geom = tree_model.get_lod4model()
                if geom is not None:
                    implicit_node = ET.SubElement(solitary_vegetation_object, "veg:lod4ImplicitRepresentation")
                    implicit_geom = ET.SubElement(implicit_node, "ImplicitGeometry")
                    matrix = ET.SubElement(implicit_geom, "transformationMatrix")
                    matrix.text = "1 0 0 0 " \
                                  "0 1 0 0 " \
                                  "0 0 1 0 " \
                                  "0 0 0 1"

                    relative_geom = ET.SubElement(implicit_geom, "relativeGMLGeometry")
                    geom_node = geom.get_citygml_geometric_representation()
                    relative_geom.append(geom_node)
                    ref_point = ET.SubElement(implicit_geom, "referencePoint")
                    point = tree_model.get_position().get_citygml_geometric_representation()
                    ref_point.append(point)

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
        bbox = self._bbox.get_bbox()
        boundedby = ET.Element("gml:boundedBy")
        envelope = ET.SubElement(boundedby, "gml:Envelope")
        envelope.set("srsDimension", "2")
        envelope.set("srsName", "EPSG:%s" % self._EPSG)

        lower_corner = ET.SubElement(envelope, "gml:lowerCorner")
        upper_corner = ET.SubElement(envelope, "gml:upperCorner")

        lower_corner.text = "{0:.2f} {1:.2f}".format(bbox[0][0], bbox[0][1])
        upper_corner.text = "{0:.2f} {1:.2f}".format(bbox[1][0], bbox[1][1])

        # add bounded-by-element to the top root subelements
        self.__root.insert(0, boundedby)

    # method to add different materials to data model
    def add_appearance(self, progressbar):
        progressbar.SetValue(0)
        self.add_appearance_color("0.47", "0.24", "0", self._stem_ids, progressbar)
        progressbar.SetValue(0)
        self.add_appearance_color("0.26", "0.65", "0.15", self._crown_deciduous_ids, progressbar)
        progressbar.SetValue(0)
        self.add_appearance_color("0.08", "0.37", "0", self._crown_coniferous_ids, progressbar)

    # Method to add a material to appearance model
    def add_appearance_color(self, r, g, b, id_list, progressbar):
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

        progressbar.SetRange(len(id_list))
        for idx, identifyer in enumerate(id_list):
            target = ET.SubElement(x3dmaterial, "app:target")
            target.text = identifyer
            if idx % 100 == 0:
                progressbar.SetValue(progressbar.GetValue()+100)

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

    # method to set option if appearance should be used
    def set_use_appearance(self, val):
        supported_geoms = [3, 4, 5]
        if self._lod1_geomtype in supported_geoms or self._lod2_geomtype in supported_geoms or self._lod3_geomtype in supported_geoms or self.__lod4_geomtype in supported_geoms:
            self._use_appearance = val

    # method to setup LOD4 geometry creation: if it and which geomtype should be created and hw many segments to use
    def setup_lod4(self, value, geomtype, segments=None):
        self.__use_lod4 = value
        self.__lod4_geomtype = geomtype
        if segments is not None:
            self.__lod4_segments = segments

    # method to generate LOD4 geometric model
    def generate_geometries(self, treemodel, validator):
        lod1_valid, lod2_valid, lod3_valid, lod4_valid = super().generate_geometries(treemodel, validator)

        # generate LOD4 geometry
        if self.__use_lod4 and lod4_valid:
            lod4_valid = self.validate_geometry(validator, self.__lod4_geomtype)
            if lod1_valid:
                lod4_geom_obj = self.get_geometry(treemodel, self.__lod4_geomtype, self.__lod4_segments, "lod4")
                treemodel.set_lod4model(lod4_geom_obj)

        return lod1_valid, lod2_valid, lod3_valid, lod4_valid


# Class containing CityJSON-specific export methods and options
class CityJSONExport(CityModelExport):
    def __init__(self, savepath, dbfilepath):
        CityModelExport.__init__(self, savepath, dbfilepath)

        self.__metadata = {}
        self.__cityobjects = {}
        self.__vertices = []

        self.__implicit_templates = []
        self.__implicit_vertice_templates = []

        self.__root = {
            "type": "CityJSON",
            "version": "1.0",
            "metadata": self.__metadata,
            "CityObjects": self.__cityobjects,
            "vertices": self.__vertices
        }

    # convert city model to strings and write it to file
    def save_file(self):
        if self._prettyprint:
            export_string = json.dumps(self.__root, indent=4)
        else:
            export_string = json.dumps(self.__root)

        with open(self._filepath, mode="w", encoding="utf-8") as outfile:
            outfile.write(export_string)

    # method to add a tree to CityJSON-model
    # converts internal tree model into CityJSON SolitaryVegetationObject tree model
    def add_tree_to_model(self, tree_model):
        tree_id = tree_model.get_id()
        attributes = {"creationDate": str(date.today())}

        # Add class to parametrized tree model
        classe = tree_model.get_class()
        if classe is not None:
            attributes["class"] = str(classe)

        # Add species to parametrized tree model
        species = tree_model.get_species()
        if species is not None:
            attributes["species"] = str(species)

        # Add hight attribute to parameterized tree model
        height = tree_model.get_height()
        if height is not None:
            attributes["height"] = height

        # Add trunk (stem) diameter attribute to parameterized tree model
        trunkdiam = tree_model.get_trunkdiam()
        if trunkdiam is not None:
            attributes["trunkDiameter"] = trunkdiam

        # Add crown diameter attribute to parameterized tree model
        crowndiam = tree_model.get_crowndiam()
        if crowndiam is not None:
            attributes["crownDiameter"] = crowndiam

        if self._generate_generic_attributes:
            for gen_att in tree_model.get_generics():
                attributes[gen_att[1]] = gen_att[2]

        geom = []
        if self._geom_type == "EXPLICIT":
            if self._use_lod1:
                geom_model = tree_model.get_lod1model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    self.total_vertex_correction_explicit(boundaries)
                    geom_obj = {"lod": 1,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self.__vertices.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        geom_obj["material"] = material
                        if self._lod1_geomtype == 3:
                            for i in range(0, self._lod1_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod1_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod1_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod1_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod1_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

            if self._use_lod2:
                geom_model = tree_model.get_lod2model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    self.total_vertex_correction_explicit(boundaries)
                    geom_obj = {"lod": 2,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self.__vertices.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        geom_obj["material"] = material
                        if self._lod2_geomtype == 3:
                            for i in range(0, self._lod2_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod2_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod2_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod2_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod2_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

            if self._use_lod3:
                geom_model = tree_model.get_lod3model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    self.total_vertex_correction_explicit(boundaries)
                    geom_obj = {"lod": 3,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self.__vertices.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        geom_obj["material"] = material
                        if self._lod3_geomtype == 3:
                            for i in range(0, self._lod3_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod3_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod3_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod3_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod3_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

        elif self._geom_type == "IMPLICIT":
            if self._use_lod1:
                geom_model = tree_model.get_lod1model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    position = tree_model.get_position().get_coordinates()
                    self.total_vertex_correction_implicit(boundaries)
                    template = {"type": geom_type,
                                "lod": 1,
                                "boundaries": boundaries}
                    geom_obj = {"type": "GeometryInstance",
                                "template": len(self.__implicit_templates),
                                "boundaries": [len(self.__vertices)],
                                "transformationMatrix": [
                                    1, 0, 0, 0,
                                    0, 1, 0, 0,
                                    0, 0, 1, 0,
                                    0, 0, 0, 1]
                                }
                    self.__vertices.append(position)
                    self.__implicit_templates.append(template)
                    self.__implicit_vertice_templates.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        template["material"] = material
                        if self._lod1_geomtype == 3:
                            for i in range(0, self._lod1_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod1_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod1_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod1_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod1_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

            if self._use_lod2:
                geom_model = tree_model.get_lod2model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    position = tree_model.get_position().get_coordinates()
                    self.total_vertex_correction_implicit(boundaries)
                    template = {"type": geom_type,
                                "lod": 2,
                                "boundaries": boundaries}
                    geom_obj = {"type": "GeometryInstance",
                                "template": len(self.__implicit_templates),
                                "boundaries": [len(self.__vertices)],
                                "transformationMatrix": [
                                    1, 0, 0, 0,
                                    0, 1, 0, 0,
                                    0, 0, 1, 0,
                                    0, 0, 0, 1]
                                }
                    self.__vertices.append(position)
                    self.__implicit_templates.append(template)
                    self.__implicit_vertice_templates.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        template["material"] = material
                        if self._lod2_geomtype == 3:
                            for i in range(0, self._lod2_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod2_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod2_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod2_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod2_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

            if self._use_lod3:
                geom_model = tree_model.get_lod3model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    position = tree_model.get_position().get_coordinates()
                    self.total_vertex_correction_implicit(boundaries)
                    template = {"type": geom_type,
                                "lod": 3,
                                "boundaries": boundaries}
                    geom_obj = {"type": "GeometryInstance",
                                "template": len(self.__implicit_templates),
                                "boundaries": [len(self.__vertices)],
                                "transformationMatrix": [
                                    1, 0, 0, 0,
                                    0, 1, 0, 0,
                                    0, 0, 1, 0,
                                    0, 0, 0, 1]
                                }
                    self.__vertices.append(position)
                    self.__implicit_templates.append(template)
                    self.__implicit_vertice_templates.extend(vertex_list)

                    # add material codes
                    if self._use_appearance:
                        visual_values = []
                        material = {"visual": {"values": visual_values}}
                        template["material"] = material
                        if self._lod3_geomtype == 3:
                            for i in range(0, self._lod3_segments):
                                visual_values.append(0)
                                if classe == 1060:
                                    visual_values.append(1)
                                elif classe == 1070:
                                    visual_values.append(2)

                        elif self._lod3_geomtype == 4:
                            # stem
                            visual_values.append([[0, 0, 0, 0, 0, 0]])
                            if classe == 1060:
                                # crown coniferous
                                visual_values.append([[1, 1, 1, 1, 1]])
                            elif classe == 1070:
                                visual_values.append([[2, 2, 2, 2, 2, 2]])

                        elif self._lod3_geomtype == 5:
                            stem_visuals = []
                            for _ in range(0, self._lod3_segments):
                                stem_visuals.append(0)
                            stem_visuals.extend([0, 0])
                            visual_values.append([stem_visuals])

                            crown_visuals = []
                            if classe == 1060:
                                for _ in range(0, self._lod3_segments):
                                    crown_visuals.append(1)
                                crown_visuals.append(1)
                                visual_values.append([crown_visuals])
                            elif classe == 1070:
                                for _ in boundaries[1][0]:
                                    crown_visuals.append(2)
                                visual_values.append([crown_visuals])

                    geom.append(geom_obj)

        self.__cityobjects[tree_id] = {
            "type": "SolitaryVegetationObject",
            "attributes": attributes,
            "geometry": geom
        }

    # method to add appearance node with different materials to export file
    def add_appearance(self, progressbar):
        stem_material = {"name": "Stem",
                         "diffuseColor": [0.47, 0.24, 0]}
        crown_material_coniferous = {"name": "Crown coniferous",
                                     "diffuseColor": [0.08, 0.37, 0]}
        crown_material_deciduous = {"name": "Crown deciduous",
                                    "diffuseColor": [0.26, 0.65, 0.15]}
        materials = [stem_material, crown_material_coniferous, crown_material_deciduous]
        self.__root["appearance"] = {"materials": materials}

    # method to convert vertex values from local values (values in geom object starting from 0)
    # to global values to prevent dupliates
    def total_vertex_correction_explicit(self, boundary_list):
        for index, element in enumerate(boundary_list):
            if type(element) == list or type(element) == tuple:
                self.total_vertex_correction_explicit(element)
            else:
                boundary_list[index] += len(self.__vertices)

    # method to convert vertex values from local values (values in geom objects starting from 0)
    # to global values to prevent dupliates for implicit geometries
    def total_vertex_correction_implicit(self, boundary_list):
        for index, element in enumerate(boundary_list):
            if type(element) == list or type(element) == tuple:
                self.total_vertex_correction_implicit(element)
            else:
                boundary_list[index] += len(self.__implicit_vertice_templates)

    # method to calculate geometric model bounding box
    def bounded_by(self):
        bbox = analysis.BoundingBox()
        for point in self.__vertices:
            bbox.compare(point[0], point[1], point[2])
        bbox_coords = bbox.get_bbox()

        self.__metadata["referenceSystem"] = "urn:ogc:def:crs:EPSG::%s" % self._EPSG
        extent = [bbox_coords[0][0], bbox_coords[0][1], bbox_coords[0][2],
                  bbox_coords[1][0], bbox_coords[1][1], bbox_coords[1][2]]
        self.__metadata["geographicalExtent"] = extent

    def set_geomtype(self, geomtype):
        Export.set_geomtype(self, geomtype)
        if geomtype == "IMPLICIT":
            geom_templates = {"templates": self.__implicit_templates,
                              "vertices-templates": self.__implicit_vertice_templates}
            self.__root["geometry-templates"] = geom_templates


class GeoJSONExport(Export):
    def __init__(self, savepath, dbfilepath):
        Export.__init__(self, savepath, dbfilepath)

        self.__features = []
        self.__bbox = []
        self.__root = {"type": "FeatureCollection",
                       "bbox": self.__bbox,
                       "features": self.__features}

        self.__transformer = None

    def setup_transformer(self, from_epsg, to_epsg):
        self.__transformer = geometry.get_transformer(from_epsg, to_epsg)

    # convert city model to strings and write it to file
    def save_file(self):
        if self._prettyprint:
            export_string = json.dumps(self.__root, indent=4, ensure_ascii=False)
        else:
            export_string = json.dumps(self.__root, ensure_ascii=False)

        with open(self._filepath, mode="w", encoding="utf-8") as outfile:
            outfile.write(export_string)

    def add_tree_to_model(self, tree_model):
        geom_obj = tree_model.get_lod1model()

        # dont add anything to geojson if geometry does not exist
        if geom_obj is None:
            return

        properties = {"creationDate": str(date.today())}

        # Add class to parametrized tree model
        classe = tree_model.get_class()
        if classe is not None:
            properties["class"] = str(classe)

        # Add species to parametrized tree model
        species = tree_model.get_species()
        if species is not None:
            properties["species"] = str(species)

        # Add hight attribute to parameterized tree model
        height = tree_model.get_height()
        if height is not None:
            properties["height"] = height

        # Add trunk (stem) diameter attribute to parameterized tree model
        trunkdiam = tree_model.get_trunkdiam()
        if trunkdiam is not None:
            properties["trunkDiameter"] = trunkdiam

        # Add crown diameter attribute to parameterized tree model
        crowndiam = tree_model.get_crowndiam()
        if crowndiam is not None:
            properties["crownDiameter"] = crowndiam

        if self._generate_generic_attributes:
            for gen_att in tree_model.get_generics():
                properties[gen_att[1]] = gen_att[2]

        geom_type, geom_coords = geom_obj.transform(self.__transformer, 4326).get_geojson_geometric_representation()
        geom = {"type": geom_type,
                "coordinates": geom_coords}

        bbox_obj = analysis.BoundingBox()
        self.get_geometry_bbox(geom_coords, bbox_obj)
        bbox = bbox_obj.get_bbox()
        bbox_geojson = [bbox[0][0], bbox[0][1], bbox[0][2], bbox[1][0], bbox[1][1], bbox[1][2]]

        feature = {"type": "Feature",
                   "id": tree_model.get_id(),
                   "bbox": bbox_geojson,
                   "properties": properties,
                   "geometry": geom}

        self.__features.append(feature)

    # method to find the bbox of a single GeoJSON geometry
    def get_geometry_bbox(self, geom_list, bbox):
        if type(geom_list[0]) == list:
            for element in geom_list:
                self.get_geometry_bbox(element, bbox)
        else:
            x = geom_list[0]
            y = geom_list[1]
            z = geom_list[2]
            bbox.compare(x, y, z)

    def bounded_by(self):
        bbox = analysis.BoundingBox()
        for feature in self.__features:
            feature_bbox = feature["bbox"]
            bbox.compare(feature_bbox[0], feature_bbox[1], feature_bbox[2])
            bbox.compare(feature_bbox[3], feature_bbox[4], feature_bbox[5])

        global_bbox = bbox.get_bbox()

        for point in global_bbox:
            for coord in point:
                self.__bbox.append(coord)


class IfcExport(Export):

    def __init__(self, savepath, dbfilepath, ifc_version):
        Export.__init__(self, savepath, dbfilepath)
        self.__file_content = ""

        self.__IfcVersion = ifc_version

        self.__oid = IfcOid()
        self.__oid_organization = 0
        self.__oid_owner_history = 0
        self.__oid_site_placement = 0
        self.__oid_global_placement = 0
        self.__oid_element_placement = 0
        self.__oid_geometric_representation_context = 0
        self.__oid_project = 0
        self.__oid_site = 0

        self.__min_easting = 0
        self.__min_northing = 0
        self.__min_height = 0

        self.__l_tree_oids = []

    def add_line_to_file_content(self, line):
        self.__file_content += line + "\n"

    def add_lines_to_file_content(self, l_lines):
        for line in l_lines:
            self.add_line_to_file_content(line)

    def generate_header(self):
        self.add_line_to_file_content("ISO-10303-21;")
        self.add_line_to_file_content("HEADER;")
        self.add_line_to_file_content("FILE_DESCRIPTION((''),'2;1');")

        t_filename = self._filepath.split("\\")[-1]
        t_time = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
        t_name = config.get_program_name()
        t_version = config.get_program_version()
        t_name_version = t_name + " Version " + t_version

        t_file_name_row = "FILE_NAME('{0}','{1}',(''),('KIT/IAI'),'{2}',' ','KIT');".format(t_filename, t_time,
                                                                                            t_name_version)
        self.add_line_to_file_content(t_file_name_row)

        self.add_line_to_file_content("FILE_SCHEMA(('%s'));" % self.__IfcVersion)
        self.end_section()

    def start_data_section(self):
        self.add_line_to_file_content("DATA;")
        self.__oid_organization = self.create_ifc_organization()
        self.__oid_owner_history = self.create_ifc_owner_history()
        self.__oid_project = self.create_ifc_project()
        self.__oid_site = self.create_ifc_site()

        # Relation RelAggregates --> Projekt enthält eine Site
        self.create_ifc_rel_aggregates(self.__oid_project, [self.__oid_site])

    def create_ifc_organization(self):
        oid = self.__oid.get_new_oid()

        l_organization = ["#", str(oid), "=IFCORGANIZATION("
                                         "$, "  # Identification
                                         "'IAI/KIT', "  # Name
                                         "'Research University Karlsruhe', "  # Description
                                         "$, "  # Role
                                         "$"  # Adresses
                                         ");"]
        self.add_line_to_file_content("".join(l_organization))
        return oid

    def create_ifc_owner_history(self):
        oid = self.__oid.get_new_oid()

        t_change_action_state = "NOCHANGE"
        t_state = "READWRITE"

        l_owner_history = ["#", str(oid), "=IFCOWNERHISTORY(#",
                           str(self.create_ifc_person_and_organization()),  # OwningUser
                           ",#", str(self.create_ifc_application()), ",.",  # OwningApplication
                           t_state, ".,.",  # State
                           t_change_action_state, ".,",  # ChangeAction
                           "$,",  # LastModifiedDate
                           "$,",  # LastModifyingUser
                           "$,",  # LastModifiyingApplication
                           str(int(time())),  # CreationDate
                           ");"]
        self.add_line_to_file_content("".join(l_owner_history))
        return oid

    def create_ifc_person_and_organization(self):
        oid = self.__oid.get_new_oid()

        l_person_and_organization = ["#", str(oid), "=IFCPERSONANDORGANIZATION(#",
                                     str(self.create_ifc_person()),  # ThePerson
                                     ",#", str(self.__oid_organization),  # TheOrganization
                                     ", $",  # Roles
                                     ");"]
        self.add_line_to_file_content("".join(l_person_and_organization))
        return oid

    # Entität: IfcPerson, einzelner Mensch
    def create_ifc_person(self):
        oid = self.__oid.get_new_oid()

        l_persion = ["#", str(oid), "=IFCPERSON ("
                                    "$, "  # Identification
                                    "'IAI/KIT', "  # FamilyName
                                    "'IAI/KIT', "  # GivenName
                                    "$, "  # MiddleNames
                                    "$, "  # PrefixTitles
                                    "$, "  # SuffixTitles
                                    "$, "  # Roles
                                    "$"  # Addresses
                                    ");"]
        self.add_line_to_file_content("".join(l_persion))
        return oid

    def create_ifc_application(self):
        oid = self.__oid.get_new_oid()

        t_version = self.encode_step_string(config.get_program_version())
        t_application = self.encode_step_string(config.get_program_name())

        l_application = ["#", str(oid), "=IFCAPPLICATION(#",
                         str(self.__oid_organization),  # ApplicationDeveloper
                         ", 'Version {0}'".format(t_version),  # Version
                         ", '{0}'".format(t_application),  # ApplicationFullName
                         ", '{0}'".format(t_application),  # ApplicationIdentifer
                         ");"]
        self.add_line_to_file_content("".join(l_application))
        return oid

    def encode_step_string(self, t_string):
        l_express = []

        b_changed = False

        for char in t_string:
            if char != 0 and (ord(char) < 32 or ord(char) > 126):
                b_changed = True

                l_express.append("\\X2\\00")
                t_formated = "{:02x}".format(ord(char))
                t_upper = t_formated.upper()
                l_express.append(t_upper)
                l_express.append("\\X0\\")
                continue

            elif char == '\'':
                b_changed = True
                l_express.append("''")
                continue

            elif char == '\\':
                b_changed = True
                l_express.append("\\")
                continue

            else:
                l_express.append(char)
                continue

        if b_changed == True:
            t_express_string = "".join(l_express)
            return t_express_string
        else:
            return t_string

    def create_ifc_project(self):
        oid = self.__oid.get_new_oid()

        self.__oid_geometric_representation_context = self.create_ifc_geometric_representation_context()

        l_project = ["#", str(oid), "=IFCPROJECT("]

        l_root_attributes = self.create_ifc_root_attributes(t_name="Tree cadastre")
        l_project.extend(l_root_attributes)

        l_project.extend([
            ",$",  # ObjectType
            ",$",  # LongName
            ",$",  # Phase
            ",(#{0})".format(self.__oid_geometric_representation_context),  # RepresentationContexts
            ",#{0}".format(self.create_ifc_unit_assignment()),  # UnitsOnContext
            ");"])

        self.add_line_to_file_content("".join(l_project))
        return oid

    def create_ifc_root_attributes(self, t_name="", t_description=""):

        if not t_name:
            t_name = "$"

        if not t_description:
            t_description = "$"

        if t_name != "$":
            t_name = "'{0}'".format(self.encode_step_string(t_name))

        if t_description != "$":
            t_description = "'{0}'".format(self.encode_step_string(t_description))

        t_hex_guid = self.get_guid(hex=True)
        t_ifc_guid = self.compress_guid(t_hex_guid)

        l_root_attr = ["'{0}'".format(t_ifc_guid),  # GlobalId
                       ",#{0}".format(self.__oid_owner_history),  # OwnerHistory
                       ",{0}".format(t_name),  # Name
                       ",{0}".format(t_description)]  # Description
        return l_root_attr

    def create_ifc_geometric_representation_context(self):
        oid = self.__oid.get_new_oid()

        self.__oid_global_placement = self.create_ifc_axis_2_placement_3d()

        l_geom_representation = ["#", str(oid), "=IFCGEOMETRICREPRESENTATIONCONTEXT(",
                                 "$,",  # ContextIdentifer
                                 "'Model',",  # ContextType
                                 '3,',  # CoordinateSpaceDimension
                                 '1.E-005,',  # Precision
                                 "#", str(self.__oid_global_placement),  # WorldCoordinateSystem
                                 ",$",  # TrueNorth
                                 ");"]
        self.add_line_to_file_content("".join(l_geom_representation))

        self.create_ifc_map_conversion(oid)
        return oid

    def create_ifc_axis_2_placement_3d(self, o_point=None, o_direction_z=None, o_direction_x=None):
        oid = self.__oid.get_new_oid()

        if not o_point:
            o_point = geometry.Point(self._EPSG, 3, 0, 0, 0)
        if not o_direction_z:
            o_direction_z = geometry.Direction([0, 0, 1])
        if not o_direction_x:
            o_direction_x = geometry.Direction([1, 0, 0])

        l_axix_2_placement_3d = ["#", str(oid), "=IFCAXIS2PLACEMENT3D(",
                                 "#", str(self.create_ifc_cartesian_point(o_point)),  # Location
                                 ",#", str(self.create_ifc_direction(o_direction_z)),  # Axis (local z-Axis)
                                 ",#", str(self.create_ifc_direction(o_direction_x)),
                                 # RefDirection (local x-Axis)
                                 ");"]
        self.add_line_to_file_content("".join(l_axix_2_placement_3d))
        return oid

    def create_ifc_direction(self, o_direction):
        oid = self.__oid.get_new_oid()

        l_direction = ["#", str(oid), "=IFCDIRECTION((",
                       self.double_ifc_syntax(o_direction.get_dir_x()), ",",
                       self.double_ifc_syntax(o_direction.get_dir_y()), ",",
                       self.double_ifc_syntax(o_direction.get_dir_z()), "));"]

        self.add_line_to_file_content("".join(l_direction))
        return oid

    def create_ifc_map_conversion(self, geom_context):
        oid_ref_system = self.__oid.get_new_oid()

        t_from_epsg = "EPSG:" + str(self._EPSG)

        l_projected_crs = ["#", str(oid_ref_system), "=IFCPROJECTEDCRS(",
                           "'{0}',".format(t_from_epsg),  # Name
                           "$,",  # Description
                           "$,",  # GeodeticDatum
                           "$,",  # VerticalDatum
                           "$,",  # MapProjection
                           "$,",  # MapZone
                           "$",  # MapUnit
                           ");"]
        self.add_line_to_file_content("".join(l_projected_crs))

        statement = 'SELECT min("%s"), min("%s"), min("%s") from %s' % (self._col_names[self._x_value_col_index],
                                                                        self._col_names[self._y_value_col_index],
                                                                        self._col_names[self._ref_height_col_index],
                                                                        self._TreeTableName)
        self._DataCursor.execute(statement)
        self.__min_easting, self.__min_northing, self.__min_height = self._DataCursor.fetchone()

        oid_map_conversion = self.__oid.get_new_oid()

        l_map_conversion = ["#", str(oid_map_conversion), "=IFCMAPCONVERSION(",
                            "#{0},".format(geom_context),
                            "#{0},".format(oid_ref_system),
                            self.double_ifc_syntax(self.__min_easting), ",",
                            self.double_ifc_syntax(self.__min_northing), ",",
                            self.double_ifc_syntax(self.__min_height), ",",
                            self.double_ifc_syntax(1.0), ",",
                            self.double_ifc_syntax(0.0), ",",
                            "$",
                            ");"]
        self.add_line_to_file_content("".join(l_map_conversion))

        return oid_map_conversion

    def create_ifc_cartesian_point(self, o_point):
        oid = self.__oid.get_new_oid()

        l_coords = o_point.get_coordinates()

        if o_point.get_dimension() == 3:
            t_endstring = ",{0}));".format(str(self.double_ifc_syntax(l_coords[2])))
        else:
            t_endstring = "));"

        l_cartesion_point = ["#", str(oid), "=IFCCARTESIANPOINT((",
                             str(self.double_ifc_syntax(l_coords[0])),
                             ",", str(self.double_ifc_syntax(l_coords[1])),
                             t_endstring]

        self.add_line_to_file_content("".join(l_cartesion_point))
        return oid

    def double_ifc_syntax(self, d_value):
        int_part = math.ceil(d_value)

        if math.fabs(d_value - int_part) < 0.000001:
            d_formatted_value = "%d." % int_part
            return d_formatted_value

        d_formatted_value = "%f" % d_value
        return d_formatted_value

    def create_ifc_siunit(self, t_unit_type="", t_prefix="", t_name=""):
        oid = self.__oid.get_new_oid()

        if len(t_unit_type) > 0:
            t_type = ".{0}.,".format(t_unit_type)
        else:
            t_type = "$,"

        if len(t_prefix) > 0:
            t_pre = ".{0}.,".format(
                t_prefix.upper())
        else:
            t_pre = "$,"

        if len(t_name) > 0:
            t_nam = ".{0}.".format(t_name.upper())
        else:
            t_nam = "$"

        l_siunit = ["#", str(oid), "=IFCSIUNIT(*,",
                    t_type,
                    t_pre,
                    t_nam,
                    ");"]
        self.add_line_to_file_content("".join(l_siunit))
        return oid

    def create_ifc_unit_assignment(self):
        oid = self.__oid.get_new_oid()

        example_unit = self.create_ifc_siunit(t_unit_type="LENGTHUNIT", t_name="Metre")

        l_unit_assignment = ["#",
                             str(oid),
                             "=IFCUNITASSIGNMENT((",
                             "#", str(example_unit),
                             "));"]
        self.add_line_to_file_content("".join(l_unit_assignment))
        return oid

    def create_ifc_site(self):
        oid = self.__oid.get_new_oid()

        # Calculate average point and set it as Reference Point for IfcSIte
        # TODO: Calculate average point and translate it into degree, minute, seconds
        t_y_lat = "$"
        t_x_lon = "$"

        self.__oid_site_placement = self.create_ifc_local_placement(0, self.__oid_global_placement)

        l_root_attributes = self.create_ifc_root_attributes(t_name="Site")

        l_ifc_site = ["#", str(oid), "=IFCSITE("]  # GlobalId
        l_ifc_site.extend(l_root_attributes)  # OwnerHistory, Name, Description

        # TODO: createIfcObject_Attributes
        l_ifc_site.extend(",$")  # ObjectType

        l_ifc_site.extend([",#", str(self.__oid_site_placement)])  # ObjectPlacement

        l_ifc_site.extend([",$",  # Representation
                           ",$",  # LongName
                           ",.ELEMENT."])  # CompositionType

        # Koordinaten y (Grad, Minuten, Sekunden, Teilsekunden), x (Grad, Minuten, Sekunden, Teilsekunden)
        l_ifc_site.extend([",", t_y_lat,  # RefLatitude
                           ",", t_x_lon])  # RefLongditude

        l_ifc_site.extend([",$",  # RefElevation
                           ",$",  # LandTitleNumber
                           ",$",  # SiteAddress
                           ");"])
        self.add_line_to_file_content("".join(l_ifc_site))
        return oid

    def create_ifc_local_placement(self, localPlacement, axisPlacement):
        oid = self.__oid.get_new_oid()

        if localPlacement == 0:
            t_local_placement = "$"
        else:
            t_local_placement = "#{0}".format(localPlacement)

        if axisPlacement == 0:
            t_axis_placement = "$"
        else:
            t_axis_placement = ",#{0}".format(axisPlacement)

        l_ifc_local_placement = ["#", str(oid), "=IFCLOCALPLACEMENT(",
                                 t_local_placement,  # IfcObjectPlacement
                                 t_axis_placement,  # IfcAxis2Placement
                                 ");"]
        self.add_line_to_file_content("".join(l_ifc_local_placement))
        return oid

    def create_ifc_rel_aggregates(self, relating_obj, l_reladed_obj):
        oid = self.__oid.get_new_oid()

        l_rel_aggregates = ["#", str(oid), "=IFCRELAGGREGATES("]

        l_root_attributes = self.create_ifc_root_attributes(t_name="$", t_description="$")
        l_rel_aggregates.extend(l_root_attributes)

        l_rel_aggregates.extend([
            ",#", str(relating_obj),
            ", ("])

        object_count = 0
        for object in l_reladed_obj:
            object_count += 1

            if object_count > 1:
                l_rel_aggregates.append(",")

            l_rel_aggregates.extend(["#", str(object)])

        l_rel_aggregates.append("));")

        self.add_line_to_file_content("".join(l_rel_aggregates))
        return oid

    def get_guid(self, hex=False):
        if not hex:
            guid = uuid.uuid4()
        else:
            guid = uuid.uuid4().hex
        return guid

    # Gibt eine verkürzte IFC konvorme (22 Zeichen lange) GUID zurück
    def compress_guid(self, t_hex_guid):
        chars = string.digits + string.ascii_uppercase + string.ascii_lowercase + '_$'

        bs = [int(t_hex_guid[i:i + 2], 16) for i in range(0, len(t_hex_guid), 2)]

        def b64(v, l=4):
            return ''.join([chars[(v // (64 ** i)) % 64] for i in range(l)][::-1])

        return ''.join(
            [b64(bs[0], 2)] + [b64((bs[i] << 16) + (bs[i + 1] << 8) + bs[i + 2]) for i in range(1, 16, 3)])

    # method to end a section. Called to end header or data section
    def end_section(self):
        self.add_line_to_file_content("ENDSEC;")

    def end_file(self):
        self.add_line_to_file_content("END-ISO-10303-21;")

    def save_file(self):
        self.create_ifc_rel_aggregates(self.__oid_site, self.__l_tree_oids)  # create relation: tree_objs to site
        self.end_section()
        self.end_file()
        with open(self._filepath, "w") as outfile:
            outfile.write(self.__file_content)

    def add_tree_to_model(self, tree_model):
        oid = self.__oid.get_new_oid()

        tree_global_position = tree_model.get_position()
        tree_gloabl_x, tree_global_y, tree_global_z = tree_global_position.get_coordinates()
        tree_local_position = geometry.Point(0, 3,
                                             tree_gloabl_x - self.__min_easting,
                                             tree_global_y - self.__min_northing,
                                             tree_global_z - self.__min_height)

        axis_placement = self.create_ifc_axis_2_placement_3d(o_point=tree_local_position)
        self.__oid_element_placement = self.create_ifc_local_placement(self.__oid_site_placement, axis_placement)

        lod1model = tree_model.get_lod1model()
        l_geom_oids, l_geometry, representation_identifier, representation_type = lod1model.get_ifc_geometric_representation(self.__oid)
        self.add_lines_to_file_content(l_geometry)

        oid_ifc_shape_representation = self.create_ifc_shape_representation(representation_identifier, representation_type, l_geom_oids)
        oid_ifc_product_definition_shape = self.create_ifc_product_definition_shape(["#"+str(oid_ifc_shape_representation)])

        # Code to create IfcProxy for each tree
        if self.__IfcVersion == "IFC4x1":
            l_ifc_proxy = ["#", str(oid), "=IFCPROXY("]
            l_ifc_proxy.extend(self.create_ifc_root_attributes(t_name=tree_model.get_id()))
            l_ifc_proxy.extend([",$"])  # IfcLabel
            l_ifc_proxy.extend([",#", str(self.__oid_element_placement),  # ObjectPlacement
                                ",#", str(oid_ifc_product_definition_shape)])  # Representation
            l_ifc_proxy.extend([",.PRODUCT.",  # ProxyType
                                ",$",  #
                                ");"])
            self.add_line_to_file_content("".join(l_ifc_proxy))

        # Code to create IfcPlant for each tree
        elif self.__IfcVersion == "IFC4x3_RC1":
            l_ifc_plant = ["#", str(oid), "=IFCPLANT("]
            l_ifc_plant.extend(self.create_ifc_root_attributes(t_name=tree_model.get_id()))
            l_ifc_plant.extend([",'tree'"])  # ObjectType
            l_ifc_plant.extend([",#", str(self.__oid_element_placement),  # ObjectPlacement
                                ",#", str(oid_ifc_product_definition_shape)])  # Representation
            l_ifc_plant.extend([",'tree'"])  # Tag
            l_ifc_plant.extend([",.USERDEFINED."])  # PredefinedType
            l_ifc_plant.extend([");"])
            self.add_line_to_file_content("".join(l_ifc_plant))

        l_property_oids = []

        # Add class to parametrized tree model
        classe = tree_model.get_class()
        if classe is not None:
            classe_oid = self.create_ifc_property_single_value("classe", classe)
            l_property_oids.append(classe_oid)

        # Add species to parametrized tree model
        species = tree_model.get_species()
        if species is not None:
            species_oid = self.create_ifc_property_single_value("species", species)
            l_property_oids.append(species_oid)

        # Add hight attribute to parameterized tree model
        height = tree_model.get_height()
        if height is not None:
            height_oid = self.create_ifc_property_single_value("height (m)", height)
            l_property_oids.append(height_oid)

        # Add trunk (stem) diameter attribute to parameterized tree model
        trunkdiam = tree_model.get_trunkdiam()
        if trunkdiam is not None:
            trunk_oid = self.create_ifc_property_single_value("trunkDiameter (m)", trunkdiam)
            l_property_oids.append(trunk_oid)

        # Add crown diameter attribute to parameterized tree model
        crowndiam = tree_model.get_crowndiam()
        if crowndiam is not None:
            crown_oid = self.create_ifc_property_single_value("crownDiameter (m)", crowndiam)
            l_property_oids.append(crown_oid)

        if self._generate_generic_attributes:
            for _, key, value in tree_model.get_generics():
                oid_propertyset = self.create_ifc_property_single_value(key, str(value))
                l_property_oids.append(oid_propertyset)

        if len(l_property_oids) > 0:
            oid_propertyset = self.create_ifc_property_set(l_property_oids)
            self.create_ifc_rel_defined_by_properties([oid], oid_propertyset)

        self.__l_tree_oids.append(oid)

    def create_ifc_shape_representation(self, representation_identifier, representation_type, l_oid_representation_items):
        oid = self.__oid.get_new_oid()

        t_geometric_representation_context = "#{0}".format(self.__oid_geometric_representation_context)
        t_representation_items = ",".join(["#" + str(oid) for oid in l_oid_representation_items])

        l_shape_representation = ["#", str(oid), "=IFCSHAPEREPRESENTATION(",
                                  t_geometric_representation_context,  # RepresentationContext
                                  ",'", str(representation_identifier), "','",  # RepresentationIdentifer
                                  representation_type,  # RepresentationType
                                  "',(", t_representation_items,  # RepresentationItems
                                  "));"]

        self.add_line_to_file_content("".join(l_shape_representation))
        return oid

    def create_ifc_product_definition_shape(self, l_representation_oids):
        oid = self.__oid.get_new_oid()

        l_product_definition_shape = ["#", str(oid), "=IFCPRODUCTDEFINITIONSHAPE(",
                                      "$,",  # Name
                                      "$,",  # Description
                                      "(" + ",".join(l_representation_oids) + ")",  # representation
                                      ");"
                                      ]

        self.add_line_to_file_content("".join(l_product_definition_shape))
        return oid

    def create_ifc_property_single_value(self, t_key, t_value):
        oid = self.__oid.get_new_oid()

        t_name = self.encode_step_string(str(t_key))
        t_value = self.encode_step_string(str(t_value))

        l_property_single_value = ["#", str(oid), "=IFCPROPERTYSINGLEVALUE(",
                                   "'", t_name, "'",  # Name
                                   ",$",  # Description
                                   ", IFCLABEL('", t_value,  # NominalValue
                                   "'),", "$",  # TODO: Unit in SIUNIT hinzufügen?
                                   ");"]
        self.add_line_to_file_content("".join(l_property_single_value))
        return oid

    def create_ifc_rel_defined_by_properties(self, l_oid_related_entity, oid_propertyset):
        oid = self.__oid.get_new_oid()

        l_rel_defined_by_properties = ["#", str(oid), "=IFCRELDEFINESBYPROPERTIES("]

        l_root_attributes = self.create_ifc_root_attributes(t_name="$", t_description="$")
        l_rel_defined_by_properties.extend(l_root_attributes)

        l_rel_defined_by_properties.append(",(")

        i_entity_count = 0
        for element in l_oid_related_entity:
            i_entity_count += 1
            l_rel_defined_by_properties.extend(["#", str(element)])

            if i_entity_count < len(l_oid_related_entity):
                l_rel_defined_by_properties.append(",")

        l_rel_defined_by_properties.extend(["),#", str(oid_propertyset)])

        l_rel_defined_by_properties.append(");")
        self.add_line_to_file_content("".join(l_rel_defined_by_properties))
        return oid

    def create_ifc_property_set(self, l_property_single_value_oids):
        oid = self.__oid.get_new_oid()

        l_property_set = ["#", str(oid), "=IFCPROPERTYSET("]

        l_root_attributes = self.create_ifc_root_attributes(t_name="tree_properties", t_description="$")
        l_property_set.extend(l_root_attributes)

        l_property_set.append(",(")

        i_property_count = 0
        for property_id in l_property_single_value_oids:
            i_property_count += 1

            if i_property_count > 1:
                l_property_set.append(",")

            l_property_set.extend(["#", str(property_id)])
        l_property_set.append("));")
        self.add_line_to_file_content("".join(l_property_set))
        return oid


# Class to create internal tree models
# Tree models will later be converted into whatever export format is needed
class TreeModel:
    def __init__(self):
        self.__id = None  # tree ID, for example for gml:id
        self.__class = None  # tree class (CityGML Species Code)
        self.__species = None  # tree species (CityGML Species Code)
        self.__height = None  # Tree height (in meters)
        self.__trunkdiam = None  # trunk diameter (in meters)
        self.__crowndiam = None  # crown diameter (in meters)
        self.__crownheight = None  # crown height (in meters)
        self.__generics = []  # list of generic attributes
        self.__position = None  # position of trees, geometry.Point() object

        self.__lod1model = None  # geometric tree representation for LOD1 (object from geometry module)
        self.__lod2model = None  # geometric tree representation for LOD2 (object from geometry module)
        self.__lod3model = None  # geometric tree representation for LOD3 (object from geometry module)
        self.__lod4model = None  # geometric tree representation for LOD4 (object from geometry module)

    def set_id(self, val):
        self.__id = val

    def get_id(self):
        return self.__id

    def set_class(self, val):
        self.__class = val

    def get_class(self):
        return self.__class

    def set_species(self, val):
        self.__species = val

    def get_species(self):
        return self.__species

    def set_height(self, val):
        self.__height = val

    def get_height(self):
        return self.__height

    def set_trunkdiam(self, val):
        self.__trunkdiam = val

    def get_trunkdiam(self):
        return self.__trunkdiam

    def set_crowndiam(self, val):
        self.__crowndiam = val

    def get_crowndiam(self):
        return self.__crowndiam

    def set_crownheight(self, val):
        self.__crownheight = val

    def get_crownheight(self):
        return self.__crownheight

    def add_generic(self, typ, name, val):
        self.__generics.append([typ, name, val])

    def get_generics(self):
        return self.__generics

    # method to set tree position: will creage geometry.Point() object
    def set_position(self, epsg, x, y, z):
        self.__position = geometry.Point(epsg, 3, x, y, z)

    # returns tree position as geometry.Point() object
    def get_position(self):
        return self.__position

    def set_lod1model(self, geom):
        self.__lod1model = geom

    def get_lod1model(self):
        return self.__lod1model

    def set_lod2model(self, geom):
        self.__lod2model = geom

    def get_lod2model(self):
        return self.__lod2model

    def set_lod3model(self, geom):
        self.__lod3model = geom

    def get_lod3model(self):
        return self.__lod3model

    def set_lod4model(self, geom):
        self.__lod4model = geom

    def get_lod4model(self):
        return self.__lod4model


class IfcOid:
    def __init__(self):
        self.__oid = 1

    def get_new_oid(self):
        oid = self.__oid
        self.__oid += 1
        return oid


# jölkj
def generate_point_geometry(treemodel, geomtype):
    epsg_code = treemodel.get_position().get_epsg()
    if geomtype == "EXPLICIT":
        coords = treemodel.get_position().get_coordinates()
    else:
        coords = (0,0,0)

    point = geometry.Point(epsg_code, 3, coords[0], coords[1], coords[2])
    return point


# method to generate a vertiecal line geometry
def generate_line_geometry(treemodel, geomtype):
    epsg_code = treemodel.get_position().get_epsg()
    if geomtype == "EXPLICIT":
        coords = treemodel.get_position().get_coordinates()
    else:
        coords = (0, 0, 0)

    p1 = geometry.Point(epsg_code, 3, coords[0], coords[1], coords[2])
    p2 = geometry.Point(epsg_code, 3, coords[0], coords[1], coords[2]+treemodel.get_height())

    line = geometry.LineString(epsg_code, 3, p1, p2)
    return line


# method to generate cylinder geometry
def generate_cylinder_geometry(treemodel, segments, geomtype):
    epsg = treemodel.get_position().get_epsg()

    if geomtype == "EXPLICIT":
        coords = treemodel.get_position().get_coordinates()
    else:
        coords = (0, 0, 0)

    ref_h = coords[2]
    tree_h = treemodel.get_height() + ref_h
    crown_dm = treemodel.get_crowndiam()

    solid = geometry.Solid(epsg, 3)
    comp_poly = geometry.CompositePolygon(epsg, 3)

    angle = 0
    rotate = 2*math.pi / segments

    coordinates = []
    for _ in range(0, segments):
        pnt = [coords[0] + (crown_dm/2) * math.cos(angle), coords[1] + (crown_dm/2) * math.sin(angle)]
        coordinates.append(pnt)
        angle += rotate

    # generate walls of cylinder
    for index in range(0, len(coordinates)):
        poly = geometry.Polygon(epsg, 3)
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index-1][0], coordinates[index-1][1], tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index-1][0], coordinates[index-1][1], ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], ref_h))

        comp_poly.add_polygon(poly)

    # generate top of cylinder
    poly = geometry.Polygon(epsg, 3)
    for point in coordinates:
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], tree_h))
    comp_poly.add_polygon(poly)

    # generate bottom of cylinder
    poly = geometry.Polygon(epsg, 3)
    for point in reversed(coordinates):
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], ref_h))
    comp_poly.add_polygon(poly)

    solid.set_exterior_comp_polygon(comp_poly)
    return solid


# method to generate rectangle billboard geometries
def generate_billboard_rectangle_geometry(treemodel, segments, geomtype):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0
    tree_h = treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()

    comp_poly = geometry.CompositePolygon(epsg, 3)

    angle = 0
    rotate = 360./segments
    for _ in range(0, segments):
        poly = geometry.Polygon(epsg, 3)
        x = math.cos(math.radians(angle)) * (crown_dm/2.0)
        y = math.sin(math.radians(angle)) * (crown_dm/2.0)

        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h + tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + x, tree_y + y, ref_h + tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + x, tree_y + y, ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))

        comp_poly.add_polygon(poly)
        angle += rotate

    return comp_poly


# generate billboard from polygon outlines for deciduous trees
def generate_billboard_polygon_deciduous(treemodel, segments, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()

    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    stem_ids = []
    crown_ids = []

    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    stem_dm = treemodel.get_trunkdiam()
    crown_height = treemodel.get_crownheight()
    laubansatz = tree_h - crown_height

    comp_poly = geometry.CompositePolygon(epsg, 3)

    angle = 0.
    rotate = (2*math.pi) / segments

    alpha = math.asin((stem_dm/2.0)/(crown_dm/2.0))
    delta = (tree_h-laubansatz)/2.0 - (crown_height/2.0)*math.cos(alpha)

    for segment in range(0, segments):
        sinx = math.sin(angle)
        cosx = math.cos(angle)

        # creating stem polygon
        poly_id = "%s_%s_stempolygon%s" % (tree_id, lod, str(segment))
        stem_ids.append(poly_id)
        poly1 = geometry.Polygon(epsg, 3, geom_id=poly_id)
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), ref_h))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz+delta))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz+delta))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))
        comp_poly.add_polygon(poly1)

        # create crown polygon
        poly_id = "%s_%s_crownpolygon%s" % (tree_id, lod, str(segment))
        crown_ids.append(poly_id)
        poly2 = geometry.Polygon(epsg, 3, geom_id=poly_id)
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz+delta))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz + delta))

        # generate circle points for crown
        for v_angle in range(0, 180, 10):
            if math.radians(v_angle) < alpha:
                continue
            x = tree_x + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * cosx
            y = tree_y + (crown_dm/2.0) * math.sin(math.radians(180-v_angle)) * sinx
            z = laubansatz + crown_height/2.0 + (crown_height/2.0) * math.cos(math.radians(180-v_angle))
            poly2.exterior_add_point(geometry.Point(epsg, 3, x, y, z))

        # finish crown geometry
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz+delta))

        comp_poly.add_polygon(poly2)

        angle += rotate

    return comp_poly, stem_ids, crown_ids


# generate billboard from polygon outlines for coniferous trees
def generate_billboard_polygon_coniferous(treemodel, segments, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()

    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    stem_ids = []
    crown_ids = []

    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    stem_dm = treemodel.get_trunkdiam()
    crown_height = treemodel.get_crownheight()
    laubansatz = tree_h - crown_height

    comp_poly = geometry.CompositePolygon(epsg, 3)

    angle = 0.
    rotate = (2*math.pi) / segments
    for segment in range(0, segments):
        sinx = math.sin(angle)
        cosx = math.cos(angle)

        # creating stem polygon
        poly_id = "%s_%s_stempolygon%s" % (tree_id, lod, str(segment))
        stem_ids.append(poly_id)
        poly1 = geometry.Polygon(epsg, 3, geom_id=poly_id)
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), ref_h))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz))
        poly1.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, ref_h))
        comp_poly.add_polygon(poly1)

        # creatin crown polygon
        poly_id = "%s_%s_crownpolygon%s" % (tree_id, lod, str(segment))
        crown_ids.append(poly_id)
        poly2 = geometry.Polygon(epsg, 3, geom_id=poly_id)
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (stem_dm / 2.0), tree_y + sinx * (stem_dm / 2.0), laubansatz))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x + cosx * (crown_dm / 2.0), tree_y + sinx * (crown_dm / 2.0), laubansatz))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
        poly2.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, laubansatz))
        comp_poly.add_polygon(poly2)

        angle += rotate
    return comp_poly, stem_ids, crown_ids


# method to generate the stem for cuboid geometries
def generate_cuboid_geometry_stem(treemodel, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()

    stem_ids = []

    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    stem_dm = treemodel.get_trunkdiam()
    laubansatz = ref_h + treemodel.get_height() - treemodel.get_crownheight()

    solid = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_stem" % (tree_id, lod)
    stem_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

    # generate bottom polygon of stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    comp_poly.add_polygon(poly)

    # gemerate left side polygon for stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    comp_poly.add_polygon(poly)

    # gemerate back side polygon for stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    comp_poly.add_polygon(poly)

    # gemerate right side polygon for stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, ref_h))
    comp_poly.add_polygon(poly)

    # gemerate front side polygon for stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, ref_h))
    comp_poly.add_polygon(poly)

    # generate top polygon of stem
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y + stem_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - stem_dm / 2, tree_y - stem_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    solid.set_exterior_comp_polygon(comp_poly)
    return solid, stem_ids


# method to generate a cuboid geometry for deciduous trees
def generate_cuboid_geometry_deciduous(treemodel, geomtype, lod):

    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()
    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    crown_ids = []

    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    laubansatz = tree_h - treemodel.get_crownheight()

    comp_solid = geometry.CompositeSolid(epsg, 3)

    # --- generate stem geometry ---
    solid1, stem_ids = generate_cuboid_geometry_stem(treemodel, geomtype, lod)
    comp_solid.add_solid(solid1)

    # --- generate crown geometry ---
    solid2 = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_crown" % (tree_id, lod)
    crown_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

    # generate bottom polygon of crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate left side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate back side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate right side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate front side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # generate top polygon of crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, tree_h))
    comp_poly.add_polygon(poly)

    solid2.set_exterior_comp_polygon(comp_poly)

    comp_solid.add_solid(solid2)
    return comp_solid, stem_ids, crown_ids


# method to generate a cuboid geometry for deciduous trees
def generate_cuboid_geometry_coniferous(treemodel, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()
    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    crown_ids = []

    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    laubansatz = tree_h - treemodel.get_crownheight()

    comp_solid = geometry.CompositeSolid(epsg, 3)

    # --- generate stem geometry ---
    solid1, stem_ids = generate_cuboid_geometry_stem(treemodel, geomtype, lod)
    comp_solid.add_solid(solid1)

    # --- generate crown geometry ---
    solid2 = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_crown" % (tree_id, lod)
    crown_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

    # generate bottom polygon of crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate left side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate back side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate right side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y + crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    # gemerate front side polygon for crown
    poly = geometry.Polygon(epsg, 3)
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x - crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, tree_x + crown_dm / 2, tree_y - crown_dm / 2, laubansatz))
    comp_poly.add_polygon(poly)

    solid2.set_exterior_comp_polygon(comp_poly)
    comp_solid.add_solid(solid2)
    return comp_solid, stem_ids, crown_ids


# generate stem for geometries: cylinder
def generate_geometry_stem(epsg, tree_id, tree_x, tree_y, ref_h, stem_dm, laubansatz, segments, lod):
    stem_ids = []

    solid = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_stem" % (tree_id, lod)
    stem_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

    angle = 0
    rotate = 2 * math.pi / segments

    coordinates = []
    for _ in range(0, segments):
        pnt = [tree_x + (stem_dm / 2) * math.cos(angle), tree_y + (stem_dm / 2) * math.sin(angle)]
        coordinates.append(pnt)
        angle += rotate

    # generate walls of cylinder
    for index in range(0, len(coordinates)):
        poly = geometry.Polygon(epsg, 3)
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], laubansatz))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index - 1][0], coordinates[index - 1][1], laubansatz))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index - 1][0], coordinates[index - 1][1], ref_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], ref_h))
        comp_poly.add_polygon(poly)

    # generate top of cylinder
    poly = geometry.Polygon(epsg, 3)
    for point in coordinates:
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[0][0], coordinates[0][1], laubansatz))
    comp_poly.add_polygon(poly)

    # generate bottom of cylinder
    poly = geometry.Polygon(epsg, 3)
    for point in reversed(coordinates):
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], ref_h))
    poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[-1][0], coordinates[-1][1], ref_h))
    comp_poly.add_polygon(poly)

    solid.set_exterior_comp_polygon(comp_poly)

    return solid, stem_ids


# generate most detailed geometry for coniferous trees
# cylinder for stem, cone for crown
def generate_geometry_coniferous(treemodel, segments, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()

    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0

    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    stem_dm = treemodel.get_trunkdiam()
    crown_height = treemodel.get_crownheight()
    laubansatz = tree_h - crown_height

    crown_ids = []

    comp_solid = geometry.CompositeSolid(epsg, 3)

    # generate stem geometry
    solid1, stem_ids = generate_geometry_stem(epsg, tree_id, tree_x, tree_y, ref_h, stem_dm, laubansatz, segments, lod)
    comp_solid.add_solid(solid1)

    # generate crown geometry (cone)
    solid2 = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_crown" % (tree_id, lod)
    crown_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

    # generate walls of cone
    angle = 0
    rotate = 2 * math.pi / segments

    coordinates = []
    for _ in range(0, segments):
        pnt = [tree_x + (crown_dm / 2) * math.cos(angle), tree_y + (crown_dm / 2) * math.sin(angle)]
        coordinates.append(pnt)
        angle += rotate

    for index in range(0, len(coordinates)):
        poly = geometry.Polygon(epsg, 3)
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], laubansatz))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index-1][0], coordinates[index-1][1], laubansatz))
        poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[index][0], coordinates[index][1], laubansatz))
        comp_poly.add_polygon(poly)

    # generate bottom of cone
    poly = geometry.Polygon(epsg, 3)
    for point in reversed(coordinates):
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], laubansatz))
    poly.exterior_add_point(geometry.Point(epsg, 3, coordinates[-1][0], coordinates[-1][1], laubansatz))
    comp_poly.add_polygon(poly)

    solid2.set_exterior_comp_polygon(comp_poly)
    comp_solid.add_solid(solid2)

    return comp_solid, stem_ids, crown_ids


# generate most detailed geometry for deciduous trees:
# cylinder for stem, ellipsoid for crown
def generate_geometry_deciduous(treemodel, segments, geomtype, lod):
    pos = treemodel.get_position()
    epsg = pos.get_epsg()
    tree_id = treemodel.get_id()

    if geomtype == "EXPLICIT":
        tree_x = pos.get_x()
        tree_y = pos.get_y()
        ref_h = pos.get_z()
    else:
        tree_x = 0.0
        tree_y = 0.0
        ref_h = 0.0
    tree_h = ref_h + treemodel.get_height()
    crown_dm = treemodel.get_crowndiam()
    stem_dm = treemodel.get_trunkdiam()
    crown_height = treemodel.get_crownheight()
    laubansatz = tree_h - crown_height

    crown_ids = []

    comp_solid = geometry.CompositeSolid(epsg, 3)

    alpha = math.asin((stem_dm / 2.0) / (crown_dm / 2.0))
    delta = (tree_h - laubansatz) / 2.0 - (crown_height / 2.0) * math.cos(alpha)

    # generate stem geometry
    solid1, stem_ids = generate_geometry_stem(epsg, tree_id, tree_x, tree_y, ref_h, stem_dm, laubansatz+delta, segments, lod)
    comp_solid.add_solid(solid1)

    # generate crown geometry (ellipsoid)
    solid2 = geometry.Solid(epsg, 3)

    geom_id = "%s_%s_crown" % (tree_id, lod)
    crown_ids.append(geom_id)
    comp_poly = geometry.CompositePolygon(epsg, 3, geom_id=geom_id)

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
            poly = geometry.Polygon(epsg, 3)

            pnt1 = geometry.Point(epsg, 3,
                                  coordinates[row_index][pnt_index][0],
                                  coordinates[row_index][pnt_index][1],
                                  coordinates[row_index][pnt_index][2])
            pnt2 = geometry.Point(epsg, 3,
                                  coordinates[row_index][pnt_index-1][0],
                                  coordinates[row_index][pnt_index-1][1],
                                  coordinates[row_index][pnt_index-1][2])
            pnt3 = geometry.Point(epsg, 3,
                                  coordinates[row_index-1][pnt_index - 1][0],
                                  coordinates[row_index-1][pnt_index - 1][1],
                                  coordinates[row_index-1][pnt_index - 1][2])
            pnt4 = geometry.Point(epsg, 3,
                                  coordinates[row_index - 1][pnt_index][0],
                                  coordinates[row_index - 1][pnt_index][1],
                                  coordinates[row_index - 1][pnt_index][2])

            poly.exterior_add_point(pnt1)
            poly.exterior_add_point(pnt2)
            poly.exterior_add_point(pnt3)
            poly.exterior_add_point(pnt4)
            poly.exterior_add_point(pnt1)
            comp_poly.add_polygon(poly)

    # generate top triangle segments
    top_row = coordinates[-1]
    for index in range(0, len(top_row)):
        poly = geometry.Polygon(epsg, 3)
        poly.exterior_add_point(geometry.Point(epsg, 3, top_row[index][0], top_row[index][1], top_row[index][2]))
        poly.exterior_add_point(geometry.Point(epsg, 3, tree_x, tree_y, tree_h))
        poly.exterior_add_point(geometry.Point(epsg, 3, top_row[index-1][0], top_row[index-1][1], top_row[index-1][2]))
        poly.exterior_add_point(geometry.Point(epsg, 3, top_row[index][0], top_row[index][1], top_row[index][2]))
        comp_poly.add_polygon(poly)

    # generate bottom polygon
    poly = geometry.Polygon(epsg, 3)
    bottom_row = coordinates[0]
    for point in reversed(bottom_row):
        poly.exterior_add_point(geometry.Point(epsg, 3, point[0], point[1], point[2]))
    comp_poly.add_polygon(poly)

    solid2.set_exterior_comp_polygon(comp_poly)
    comp_solid.add_solid(solid2)

    return comp_solid, stem_ids, crown_ids
