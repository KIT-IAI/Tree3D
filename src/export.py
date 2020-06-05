import xml.etree.ElementTree as ET
import math
from datetime import date
import threading
import sqlite3
import os
import json

import default_gui
import analysis
import geometry

import wx


# parent GUI class for export dialog
# provides export functionality, needed by all export formats
# derived classes then make format-specific alterations to class
class ExportDialog(default_gui.CityGmlExport):
    def __init__(self, parent):
        default_gui.CityGmlExport.__init__(self, parent)
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
        if not self.validate_input():
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
        else:
            exporter = None

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
                                "simplified tree": 5}

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
        height = self.choiceHeight.GetSelection()
        stem = self.choiceTrunk.GetSelection()
        crown = self.choiceCrown.GetSelection()

        geom_types = []

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

        if not valid:
            msg = wx.MessageDialog(self, warningmessage, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()

        return valid

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


# Class to perform the export itself
class Export:
    def __init__(self, savepath, dbfilepath):
        self._con = sqlite3.connect(dbfilepath)
        self._DataCursor = self._con.cursor()  # Data cursor table from database (list of lists)
        self._TreeTableName = ""

        self._filepath = savepath  # output file path (where citygml will be saved)

        self._bbox = analysis.BoundingBox()  # Bounding box object

        self._col_datatypes = None  # list of data types of columns
        self._col_names = None  # list of names all columns

        self.__x_value_col_index = None  # index of column in which x value is stored
        self.__y_value_col_index = None  # index of column in which y value is stored
        self.__ref_height_col_index = None  # index of column in which reference height is stored
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

    def set_tree_table_name(self, name):
        self._TreeTableName = name

    def set_col_names(self, names):
        self._col_names = names

    def set_col_datatypes(self, types):
        self._col_datatypes = types

    def set_x_col_idx(self, idx):
        self.__x_value_col_index = idx

    def set_y_col_idx(self, idx):
        self.__y_value_col_index = idx

    def set_ref_height_col_idx(self, idx):
        self.__ref_height_col_index = idx

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
        used_cols = [self.__x_value_col_index,
                     self.__y_value_col_index,
                     self.__ref_height_col_index,
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
            x_value = row[self.__x_value_col_index]
            y_value = row[self.__y_value_col_index]
            ref_height = row[self.__ref_height_col_index]
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

            validator = analysis.AnalyzeTreeGeoms(tree_height, trunk_diam, crown_diam, crown_height)
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

        self._generate_generic_attributes = None  # variable to generate generic attributes (Trud/False)
        self._prettyprint = None  # boolean variable to determine if xml output should be formatted

        self._use_lod2 = False
        self._lod2_geomtype = None
        self._lod2_segments = None

        self._use_lod3 = False
        self._lod3_geomtype = None
        self._lod3_segments = None

    # method to set option if pretty print should be used
    def set_prettyprint(self, value):
        self._prettyprint = value

    # method to set option if generic attributes should be used
    def set_generate_generic_attributes(self, val):
        self._generate_generic_attributes = val

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
        self._vertices = []

        self.__root = {
            "type": "CityJSON",
            "version": "1.0",
            "metadata": self.__metadata,
            "CityObjects": self.__cityobjects,
            "vertices": self._vertices
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
                    self.total_vertex_correction(boundaries)
                    geom_obj = {"lod": 1,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self._vertices.extend(vertex_list)
                    geom.append(geom_obj)
            if self._use_lod2:
                geom_model = tree_model.get_lod2model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    self.total_vertex_correction(boundaries)
                    geom_obj = {"lod": 2,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self._vertices.extend(vertex_list)
                    geom.append(geom_obj)
            if self._use_lod3:
                geom_model = tree_model.get_lod3model()
                if geom_model is not None:
                    geom_type, vertex_list, boundaries = geom_model.get_cityjson_geometric_representation()
                    self.total_vertex_correction(boundaries)
                    geom_obj = {"lod": 3,
                                "type": geom_type,
                                "boundaries": boundaries}
                    self._vertices.extend(vertex_list)
                    geom.append(geom_obj)

        elif self._geom_type == "IMPLICIT":
            print("not supported yet")

        self.__cityobjects[tree_id] = {
            "type": "SolitaryVegetationObject",
            "attributes": attributes,
            "geometry": geom
        }

    # method to convert vertex values from local values (values in geom object starting from 0)
    # to global values to prevent dupliates
    def total_vertex_correction(self, boundary_list):
        for index, element in enumerate(boundary_list):
            if type(element) == list or type(element) == tuple:
                self.total_vertex_correction(element)
            else:
                boundary_list[index] += len(self._vertices)

    # method to calculate geometric model bounding box
    def bounded_by(self):
        bbox = analysis.BoundingBox()
        for point in self._vertices:
            bbox.compare(point[0], point[1], point[2])
        bbox_coords = bbox.get_bbox()

        self.__metadata["referenceSystem"] = "urn:ogc:def:crs:EPSG::%s" % self._EPSG
        extent = [bbox_coords[0][0], bbox_coords[0][1], bbox_coords[0][2],
                  bbox_coords[1][0], bbox_coords[1][1], bbox_coords[1][2]]
        self.__metadata["geographicalExtent"] = extent


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
