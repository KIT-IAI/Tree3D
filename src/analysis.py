import uuid
import math

import default_gui

import wx


# DialogBox to check for duplicate elements in data by ID
class CheckDuplicateId(default_gui.OnCheckDuplicateIdDialog):
    def __init__(self, parent):
        default_gui.OnCheckDuplicateIdDialog.__init__(self, parent)
        self.__col_settings = self.GetParent().get_column_config()
        self.populate_dropdown()

    # populate dropdown with grid columns in dialogbox
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.IdColumns.SetItems(colitemlist)

        # pre-select ID column
        idcol = self.__col_settings.get_id()
        if idcol is not None:
            self.IdColumns.SetStringSelection(idcol)

    # method to be executed when hitting Analyze Button in DialogBox
    # Checks if data contains duplicate IDs, validates UUIDs
    # overrides method in parent class
    def on_analyze(self, event):
        # exit method if no selection has been made in dropdown
        if self.IdColumns.GetSelection() == wx.NOT_FOUND:
            warningtext = "Please select ID column to analyze for duplicates"
            msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()
            return

        # update ID pre-selection setting
        self.__col_settings.set_id(self.IdColumns.GetStringSelection())

        # hide result text and result grid
        self.InfoTextUUID.Hide()
        self.UUIDGrid.Hide()
        self.InfoTextDuplicate.Hide()
        self.DuplicateGrid.Hide()

        # Delete rows from grid to reset to 0
        try:
            self.DuplicateGrid.DeleteRows(pos=0, numRows=self.DuplicateGrid.GetNumberRows())
        except:
            pass
        try:
            self.UUIDGrid.DeleteRows(pos=0, numRows=self.UUIDGrid.GetNumberRows())
        except:
            pass

        itemindex = self.IdColumns.GetSelection()  # index of selected column
        itemcolname = self.IdColumns.GetString(itemindex)  # name of selected column

        # displays selected column name in column labels of grids
        self.DuplicateGrid.SetColLabelValue(0, itemcolname)
        self.DuplicateGrid.SetColLabelValue(1, "#")
        self.UUIDGrid.SetColLabelValue(0, itemcolname)

        # performs a selection for every value to be checkt with WHERE clause
        # check_value: all distinct values of one column
        duplicate_counter = 0
        uuid_counter = 0
        all_data = self.GetParent().db.count_unique_values_in_col(itemcolname)
        for row in all_data:
            # if query returns >1 rows (e.g. two entries with one ID), add values to grid
            if row[1] > 1:
                self.DuplicateGrid.AppendRows(1)
                self.DuplicateGrid.SetCellValue(duplicate_counter, 0, str(row[0]))
                self.DuplicateGrid.SetCellValue(duplicate_counter, 1, str(row[1]))
                duplicate_counter += 1
            # perform uuid validation if uuid-checkbox was activated
            if self.UUIDCheck.GetValue():
                try:
                    uuid.UUID('{%s}' % row[0])
                except ValueError:
                    # add UUID to grid if invalid
                    self.UUIDGrid.AppendRows(1)
                    self.UUIDGrid.SetCellValue(uuid_counter, 0, str(row[0]))
                    uuid_counter += 1

        # change info message if no duplicates have been found
        # otherwise: show grid with duplicates
        if duplicate_counter == 0:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed.\nNo duplicates have been found")
        else:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed.\n"
                                            "%s duplicates have been found" % duplicate_counter)
            self.DuplicateGrid.Show(True)
        self.InfoTextDuplicate.Show(True)

        # change info message if no invalid uuid was found
        # otherwise: show grid with invalid uuids
        if self.UUIDCheck.GetValue():
            if uuid_counter == 0:
                self.InfoTextUUID.SetLabel("UUID-Validation completed.\nNo invalid UUIDs found")
            else:
                self.UUIDGrid.Show(True)
                self.InfoTextUUID.SetLabel("UUID-Validation completed.\n"
                                           "%s invalid UUIDs found" % uuid_counter)
            self.InfoTextUUID.Show(True)

        self.Layout()


# DialogBox to check for duplicate elements in data by ID
class CheckDuplicateGeom(default_gui.OnCheckDuplicateGeomDialog):
    def __init__(self, parent):
        default_gui.OnCheckDuplicateGeomDialog.__init__(self, parent)
        self.__col_settings = self.GetParent().get_column_config()
        self.populate_dropdown()

    # populate dropdown with grid columns in dialogbox
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.IdColumns.SetItems(colitemlist)
        self.xvalue.SetItems(colitemlist)
        self.yvalue.SetItems(colitemlist)

        # make column pre-selection
        idcol = self.__col_settings.get_id()
        if idcol is not None:
            self.IdColumns.SetStringSelection(idcol)

        coords = self.__col_settings.get_coordinates()
        if coords != (None, None):
            self.xvalue.SetStringSelection(coords[0])
            self.yvalue.SetStringSelection(coords[1])

    # method to be executed when hitting Analyze Button in DialogBox
    # Checks if data contains duplicate geometries
    # objects are considered duplicates when their (2D)-Distance is smaller than a threshold
    def on_analyze(self, event):
        if not self.validate_entries():
            return

        # update column pre-selection
        self.__col_settings.set_id(self.IdColumns.GetStringSelection())
        self.__col_settings.set_coordinates(self.xvalue.GetStringSelection(), self.yvalue.GetStringSelection())

        # reset gui in case operation is performed twice
        self.InfoTextDuplicate.Hide()
        self.DuplicateGrid.Hide()
        if self.DuplicateGrid.GetNumberRows() > 0:
            self.DuplicateGrid.DeleteRows(numRows=self.DuplicateGrid.GetNumberRows())

        # set max value of progressbar in gui
        num_tablerecords = self.GetParent().db.get_number_of_tablerecords()
        summands = num_tablerecords
        summe = 0
        while summands > 0:
            summe += summands
            summands -= 1
        summe -= num_tablerecords
        self.gauge.SetRange(summe)
        self.gauge.SetValue(0)

        # list with result of analysis
        result_list = []

        # list of database columns to be queried
        # collist[0] = ID, collist[1] = xvalue, collist[2] = yvalue
        collist = []
        idx = self.IdColumns.GetSelection()
        collist.append(self.IdColumns.GetString(idx))
        idx = self.xvalue.GetSelection()
        collist.append(self.xvalue.GetString(idx))
        idx = self.yvalue.GetSelection()
        collist.append(self.yvalue.GetString(idx))

        # fetch data from database
        data_cursor = self.GetParent().db.get_data_for_duplicatecheck_geom(collist)
        for row in data_cursor:
            self.gauge.SetValue(self.gauge.GetValue() + 1)
            # coordinates for calculation
            x1 = row[1]
            y1 = row[2]
            x2 = row[4]
            y2 = row[5]

            # calculate squared distance between both trees
            try:
                dist_sq = (x1 - x2) ** 2 + (y1 - y2) ** 2
            except TypeError:
                warningtext = "Cannot perform calculations with values in X or Y column.\n" \
                              "Value in specified X or Y grid column is most likely not numeric.\n" \
                              "Was the correct grid column chosen for X and Y value?"
                msg = wx.MessageDialog(self, warningtext, caption="Error",
                                       style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
                msg.ShowModal()
                return

            if dist_sq < float(self.threshold.GetLineText(0).replace(",", ".")) ** 2:
                result_list.append([row[0], row[3], math.sqrt(dist_sq)])
        self.gauge.SetValue(0)

        # show result in gui
        if len(result_list) > 0:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed:\n"
                                            "%s duplicates have been found" % len(result_list))
            self.DuplicateGrid.AppendRows(len(result_list))
            for index, row in enumerate(result_list):
                self.DuplicateGrid.SetCellValue(index, 0, str(row[0]))
                self.DuplicateGrid.SetCellValue(index, 1, str(row[1]))
                self.DuplicateGrid.SetCellValue(index, 2, str(round(row[2], 3)))
            self.InfoTextDuplicate.Show(True)
            self.DuplicateGrid.Show(True)
        else:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed:\nNo duplicates have been found")
            self.InfoTextDuplicate.Show(True)

        self.Layout()

    # validate entries to GUI
    def validate_entries(self):
        valid = True
        warningtext = ""

        try:
            float(self.threshold.GetLineText(0).replace(",", "."))
        except ValueError:
            valid = False
            warningtext = "Threshold must be a decimal"

        if self.threshold.GetLineText(0) == "":
            warningtext = "Threshold value must not be empty"
            valid = False

        if self.xvalue.GetSelection() == self.yvalue.GetSelection():
            warningtext = "X-Value and Y-Value must not be the same column"
            valid = False

        if self.yvalue.GetSelection() == wx.NOT_FOUND or self.xvalue.GetSelection() == wx.NOT_FOUND:
            warningtext = "Please select X and Y values to perform geometric duplicate analysis"
            valid = False

        if self.IdColumns.GetSelection() == wx.NOT_FOUND:
            warningtext = "Please select ID column to perform geometric duplicate analysis"
            valid = False

        if not valid:
            msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()

        return valid


class AnalyzeGeometryDialog(default_gui.OnCheckGeometryDialog):
    def __init__(self, parent):
        default_gui.OnCheckGeometryDialog.__init__(self, parent)
        self.__col_settings = self.GetParent().get_column_config()

        self.populate_columns()
        self.DoLayoutAdaptation()

    # adds column names to dropdown windows
    def populate_columns(self):
        collist = self.GetParent().db.get_column_names()

        self.choiceID.SetItems(collist)
        self.choiceX.SetItems(collist)
        self.choiceY.SetItems(collist)
        self.choiceRefheight.SetItems(collist)
        self.choiceHeight.SetItems(collist)
        self.choiceTrunk.SetItems(collist)
        self.choiceCrown.SetItems(collist)
        self.crown_height_col.SetItems(collist)

        # make column pre-selection
        self.load_column_preselection()

    # method to pre-select dropdown menus
    def load_column_preselection(self):
        idcol = self.__col_settings.get_id()
        if idcol is not None:
            self.choiceID.SetStringSelection(idcol)

        xcol, ycol = self.__col_settings.get_coordinates()
        if xcol is not None:
            self.choiceX.SetStringSelection(xcol)
        if ycol is not None:
            self.choiceY.SetStringSelection(ycol)

        refheight = self.__col_settings.get_ref_height()
        if refheight is not None:
            self.choiceRefheight.SetStringSelection(refheight)

        height = self.__col_settings.get_tree_height()
        if height != (None, None):
            self.choiceHeight.SetStringSelection(height[0])
            self.choiceHeightUnit.SetStringSelection(height[1])

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

        crownheight = self.__col_settings.get_crown_height()
        if crownheight is not None:
            self.crown_height_col.SetStringSelection(crownheight)

    def validate_coordinates(self, identify, x, y, refheight):
        valid = True
        message = ""

        if identify == x and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as Easting column"

        if identify == y and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as Northing column"

        if identify == refheight and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as Reference Height column"

        if x == y and x != wx.NOT_FOUND:
            valid = False
            message = "Easting column must not be the same as Northing column"

        if x == refheight and x != wx.NOT_FOUND:
            valid = False
            message = "Easting column must not be the same as Reference Height column"

        if y == refheight and y != wx.NOT_FOUND:
            valid = False
            message = "NOrthing column must not be the same as Reference Height column"

        if refheight == wx.NOT_FOUND:
            valid = False
            message = "Reference Height Column must not be empty"

        if y == wx.NOT_FOUND:
            valid = False
            message = "Northing Column must not be empty"

        if x == wx.NOT_FOUND:
            valid = False
            message = "Easting Column must not be empty"

        if identify == wx.NOT_FOUND:
            valid = False
            message = "ID Column must not be empty."

        return valid, message

    # checks columns for validity: ID and height
    def validate_height(self, identify, x, y, refheight, height):
        valid, message = self.validate_coordinates(identify, x, y, refheight)

        if identify == height and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as height column"

        if x == height and x != wx.NOT_FOUND:
            valid = False
            message = "Easting column must not be the same as height column"

        if y == height and y != wx.NOT_FOUND:
            valid = False
            message = "Northing column must not be the same as height column"

        if refheight == height and refheight != wx.NOT_FOUND:
            valid = False
            message = "Reference Height column must not be the same as height column"

        if height == wx.NOT_FOUND:
            valid = False
            message = "Height column must not be empty"

        return valid, message

    # checks columns for validity: ID, height and crown
    def validate_height_crown(self, identify, x, y, refheight, height, crown):
        valid, message = self.validate_height(identify, x, y, refheight, height)

        if height == crown and height != wx.NOT_FOUND:
            valid = False
            message = "Height column must not be the same as crown column"

        if identify == crown and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as crown column"

        if x == crown and x != wx.NOT_FOUND:
            valid = False
            message = "Easting column must not be the same as crown column"

        if y == crown and y != wx.NOT_FOUND:
            valid = False
            message = "Northing column must not be the same as crown column"

        if refheight == crown and refheight != wx.NOT_FOUND:
            valid = False
            message = "Reference Height column must not be the same as crown column"

        if crown == wx.NOT_FOUND:
            valid = False
            message = "Crown diameter column must not be empty."

        return valid, message

    # checks columns for validity: ID height, crown and trunk
    def validate_height_crown_trunk(self, identify, x, y, refheight, height, crown, trunk):
        valid, message = self.validate_height_crown(identify, x, y, refheight, height, crown)

        if trunk == crown and trunk != wx.NOT_FOUND:
            valid = False
            message = "Trunk column must not be the same as crown column"

        if height == trunk and height != wx.NOT_FOUND:
            valid = False
            message = "Height column must not be the same as trunk column"

        if x == trunk and x != wx.NOT_FOUND:
            valid = False
            message = "Easting column must not be the same as trunk column"

        if y == trunk and y != wx.NOT_FOUND:
            valid = False
            message = "Northing column must not be the same as trunk column"

        if refheight == trunk and refheight != wx.NOT_FOUND:
            valid = False
            message = "Reference Height column must not be the same as trunk column"

        if identify == trunk and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as trunk column"

        if trunk == wx.NOT_FOUND:
            valid = False
            message = "Trunk diameter column must not be empty"

        return valid, message

    # checks columns for validity: ID, height, crown, trunk and crown height
    def validate_height_crown_trunk_crownheight(self, identify, x, y, refheight, height, crown, trunk, crownheight):
        valid, message = self.validate_height_crown_trunk(identify, x, y, refheight, height, crown, trunk)

        if crownheight == identify and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as ID column"

        if crownheight == x and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as Easting column"

        if crownheight == y and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as Northing column"

        if crownheight == refheight and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as Reference Height column"

        if crownheight == height and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as height column"

        if crownheight == crown and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as crown column"

        if crownheight == trunk and crownheight != wx.NOT_FOUND:
            valid = False
            message = "Crown height column must not be the same as trunk column"

        if crownheight == wx.NOT_FOUND:
            valid = False
            message = "Cronw height column must not be empty"

        return valid, message

    # validates user input to GUI
    def validate(self):
        valid = True
        message = ""

        geom_type = self.geom_type.GetStringSelection()

        identify = self.choiceID.GetSelection()
        x = self.choiceX.GetSelection()
        y = self.choiceY.GetSelection()
        refheight = self.choiceRefheight.GetSelection()
        height = self.choiceHeight.GetSelection()
        trunk = self.choiceTrunk.GetSelection()
        crown = self.choiceCrown.GetSelection()
        crown_height = self.crown_height_col.GetSelection()

        # choose method for input validation, depening on input of geometry type
        if geom_type == "Point":
            valid, message = self.validate_coordinates(identify, x, y, refheight)
        if geom_type == "Line":
            valid, message = self.validate_height(identify, x, y, refheight, height)
        if geom_type == "Cylinder":
            valid, message = self.validate_height_crown(identify, x, y, refheight, height, crown)
        if geom_type == "Rectangles":
            valid, message = self.validate_height_crown(identify, x, y, refheight, height, crown)
        if geom_type in ["Outline polygons", "Cuboid", "Detailled"]:
            if self.crown_height.GetSelection() != 2:
                valid, message = self.validate_height_crown_trunk(identify, x, y, refheight, height, crown, trunk)
            else:
                valid, message = self.validate_height_crown_trunk_crownheight(identify, x, y, refheight,
                                                                              height, crown, trunk, crown_height)

        # show error message if input is not valid
        if not valid:
            msg = wx.MessageDialog(self, message, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()

        return valid

    # method is executed if value in tree_geom dropdown changes
    # Enables/disables certaín GUI elements
    def on_tree_geom(self, event):
        if self.geom_type.GetSelection() in [0, 1, 2, 3]:
            self.crown_height_text.Enable(False)
            self.crown_height.Enable(False)
            self.crown_height_col_text.Enable(False)
            self.crown_height_col.Enable(False)
            self.crown_height.SetSelection(0)
            self.crown_height_col.SetSelection(n=wx.NOT_FOUND)
        else:
            self.crown_height_text.Enable(True)
            self.crown_height.Enable(True)
            self.on_crown_height(None)

    # method is executed if value in crown height calcuoation dropdown chagnes
    # Enables/disables certain GUI elemnts
    def on_crown_height(self, event):
        if self.crown_height.GetSelection() != 2:
            self.crown_height_col_text.Enable(False)
            self.crown_height_col.Enable(False)
            self.crown_height_col.SetSelection(n=wx.NOT_FOUND)
        else:
            self.crown_height_col_text.Enable(True)
            self.crown_height_col.Enable(True)

    # method is executed if "Analyze" button is pushed
    def on_analyze(self, event):
        if not self.validate():
            return

        self.save_column_preselection()

        geom_type = self.geom_type.GetStringSelection()

        # disable GUI elements
        self.analysis_invalid.Show(False)
        self.analysis_valid.Show(False)
        self.result_grid.Show(False)

        collist = [self.choiceX.GetStringSelection(),
                   self.choiceY.GetStringSelection(),
                   self.choiceRefheight.GetStringSelection(),
                   self.choiceID.GetStringSelection(),
                   self.choiceHeight.GetStringSelection(),
                   self.choiceTrunk.GetStringSelection(),
                   self.choiceCrown.GetStringSelection()]

        # add crown height column to collist, if it is used
        if self.crown_height.GetSelection() == 2:
            collist.append(self.crown_height_col.GetStringSelection())

        invalid_trees = []

        # loop over all trees in data base table
        for cursor in self.GetParent().db.get_data_by_collist(collist):
            x = cursor[0]
            y = cursor[1]
            refheight = cursor[2]
            identifier = cursor[3]
            height = cursor[4]
            trunk = cursor[5]
            crown = cursor[6]
            try:
                crown_height = cursor[7]
            except IndexError:
                crown_height = None

            # convert everything into meters
            if self.choiceHeightUnit.GetSelection() == 1:
                try:
                    height = height / 100
                except TypeError:
                    pass
            if self.choiceTrunkUnit.GetSelection() == 1:
                try:
                    trunk = trunk / 100
                except TypeError:
                    pass
            if self.choiceCrownUnit.GetSelection() == 1:
                try:
                    crown = crown / 100
                except:
                    pass

            # convert circumference into diameter
            if self.trunk_circ.GetSelection() == 1:
                try:
                    trunk = trunk / math.pi
                except TypeError:
                    pass
            if self.crown_circ.GetSelection() == 1:
                try:
                    crown = crown / math.pi
                except:
                    pass

            analyzer = AnalyzeTreeGeoms(x, y, refheight, height, trunk, crown, crown_height)
            valid = True
            message = ""

            # choose, what geometry check should be performed, depending on user input for geometry type
            if geom_type == "Point":
                valid, message = analyzer.analyze_coordinates()
            if geom_type == "Line":
                valid, message = analyzer.analyze_height()
            if geom_type == "Cylinder":
                valid, message = analyzer.analyze_height_crown()
            if geom_type == "Rectangles":
                valid, message = analyzer.analyze_height_crown()
            if geom_type in ["Outline polygons", "Cuboid", "Detailled"]:
                # geometry check depends on what kind of tree height calculation should be used
                if self.crown_height.GetSelection() == 0:
                    valid, message = analyzer.analyze_height_crown_trunk_sphere()
                if self.crown_height.GetSelection() == 1:
                    valid, message = analyzer.analyze_height_crown_trunk()
                if self.crown_height.GetSelection() == 2:
                    valid, message = analyzer.analyze_height_crown_trunk_nosphere()

            if not valid:
                invalid_trees.append((identifier, message))

        # show results
        self.m_staticline13.Show(True)

        # show text if no invalid geoms were found
        if len(invalid_trees) == 0:
            self.analysis_valid.Show(True)
        # show different text if otherwise, show fill grid with info
        else:
            label = "Analysis completed.\n" \
                    "%s Trees with invalid geometry parameters have been found.\n" % len(invalid_trees)
            self.analysis_invalid.SetLabel(label)
            self.analysis_invalid.Show(True)

            if self.result_grid.GetNumberRows() > 0:
                self.result_grid.DeleteRows(pos=0, numRows=self.result_grid.GetNumberRows())
            self.result_grid.AppendRows(len(invalid_trees))
            for row_index, row in enumerate(invalid_trees):
                for col_index, value in enumerate(row):
                    self.result_grid.SetCellValue(row_index, col_index, str(value))
            self.result_grid.SetColSize(0, 110)
            self.result_grid.SetColSize(1, 300)
            self.result_grid.Show(True)
        self.DoLayoutAdaptation()
        self.Layout()

    # method to save column selections
    def save_column_preselection(self):
        if self.choiceID.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_id(self.choiceID.GetStringSelection())

        if self.choiceX.GetSelection() != wx.NOT_FOUND and self.choiceY.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_coordinates(self.choiceX.GetStringSelection(), self.choiceY.GetStringSelection())

        if self.choiceRefheight.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_ref_height(self.choiceRefheight.GetStringSelection())

        if self.choiceHeight != wx.NOT_FOUND:
            height = self.choiceHeight.GetStringSelection()
            unit = self.choiceHeightUnit.GetStringSelection()
            self.__col_settings.set_tree_height(height, unit)

        if self.choiceTrunk.GetSelection() != wx.NOT_FOUND:
            trunk = self.choiceTrunk.GetStringSelection()
            mode = self.trunk_circ.GetStringSelection()
            unit = self.choiceTrunkUnit.GetStringSelection()
            self.__col_settings.set_trunk_diam(trunk, mode, unit)

        if self.choiceCrown.GetSelection() != wx.NOT_FOUND:
            crown = self.choiceCrown.GetStringSelection()
            mode = self.crown_circ.GetStringSelection()
            unit = self.choiceCrownUnit.GetStringSelection()
            self.__col_settings.set_crown_diam(crown, mode, unit)

        if self.crown_height_col.GetSelection() != wx.NOT_FOUND:
            self.__col_settings.set_crown_height(self.crown_height_col.GetStringSelection())


class AnalyzeTreeGeoms:
    # all parameters must be the same unit
    # trunk and crown must BOTH be diam
    def __init__(self, x, y, ref, height, trunk_diam, crown_diam, crown_height=None):
        self.__Height = height
        self.__TrunkDiam = trunk_diam
        self.__CrownDiam = crown_diam
        self.__CrownHeight = crown_height

        self.__x = x
        self.__y = y
        self.__ref_height = ref

    def analyze_coordinates(self):
        valid = True
        msg = ""

        if self.__x is None:
            valid = False
            msg = "No easting value specified"

        if self.__y is None:
            valid = False
            msg = "No northing value specified"

        if self.__ref_height is None:
            valid = False
            msg = "No reference height value specified"

        return valid, msg

    # analyze values: height
    def analyze_height(self):
        valid, msg = self.analyze_coordinates()

        if self.__Height == 0:
            valid = False
            msg = "Height is 0"
        elif self.__Height is None:
            valid = False
            msg = "No height value specified"
        elif self.__Height < 0:
            valid = False
            msg = "Hight is smaller that 0"

        return valid, msg

    # analyze values: height, crown
    def analyze_height_crown(self):
        valid, msg = self.analyze_height()

        if self.__CrownDiam == 0:
            valid = False
            msg = "Crown diameter is 0"
        elif self.__CrownDiam is None:
            valid = False
            msg = "No crown diameter specified"
        elif self.__CrownDiam < 0:
            valid = False
            msg = "Crown diameter is smaller than 0"

        return valid, msg

    # analyze values: height, crown, trunk, crown shape ellipsoid height depends on tree height
    def analyze_height_crown_trunk(self):
        valid, msg = self.analyze_height_crown()

        if self.__TrunkDiam == 0:
            valid = False
            msg = "Trunk diameter is 0"
        elif self.__TrunkDiam is None:
            valid = False
            msg = "No trunk diameter specified"
        elif self.__TrunkDiam < 0:
            valid = False
            msg = "Trunk diameter is smaller than 0"

        if self.__Height is not None and self.__TrunkDiam is not None and self.__CrownDiam is not None:
            if self.__TrunkDiam > self.__CrownDiam:
                valid = False
                msg = "Trunk diameter is greater than crown diameter"
            if self.__TrunkDiam > self.__Height:
                valid = False
                msg = "Trunk diameter is greater than tree height"

        return valid, msg

    # analyze values: height, crown, trunk for spheric crown shape
    def analyze_height_crown_trunk_sphere(self):
        valid, msg = self.analyze_height_crown_trunk()

        if self.__Height is not None and self.__CrownDiam is not None and self.__CrownDiam > self.__Height:
            valid = False
            msg = "Crown diameter is greater than tree height"

        return valid, msg

    # analyze values: height, crown, trunk for crown from crown height value
    def analyze_height_crown_trunk_nosphere(self):
        valid, msg = self.analyze_height_crown_trunk()

        if self.__CrownHeight == 0:
            valid = False
            msg = "Crown height is 0"
        elif self.__CrownHeight is None:
            valid = False
            msg = "No crown height specified"
        elif self.__CrownHeight < 0:
            valid = False
            msg = "Crown height is smaller than 0"

        if self.__Height is not None and self.__CrownHeight is not None and self.__CrownHeight > self.__Height:
            valid = False
            msg = "Crown height is greater than tree height."

        return valid, msg

    # method to analyze parameters, Deprecated and not used in Program
    def analyze_old(self):
        valid = True
        msg = ""

        if self.__Height == 0:
            valid = False
            msg = "Height is 0"
        elif self.__Height is None:
            valid = False
            msg = "No height value specified"
        elif self.__Height < 0:
            valid = False
            msg = "Hight is smaller that 0"

        if self.__TrunkDiam == 0:
            valid = False
            msg = "Trunk diameter is 0"
        elif self.__TrunkDiam is None:
            valid = False
            msg = "No trunk diameter specified"
        elif self.__TrunkDiam < 0:
            valid = False
            msg = "Trunk diameter is smaller than 0"

        if self.__CrownDiam == 0:
            valid = False
            msg = "Crown diameter is 0"
        elif self.__CrownDiam is None:
            valid = False
            msg = "No crown diameter specified"
        elif self.__CrownDiam < 0:
            valid = False
            msg = "Crown diameter is smaller than 0"

        if self.__Height is not None and self.__TrunkDiam is not None and self.__CrownDiam is not None:
            if self.__TrunkDiam > self.__CrownDiam:
                valid = False
                msg = "Trunk diameter is greater than crown diameter"
            if self.__CrownDiam > self.__Height:
                valid = False
                msg = "Crown diameter is greater than tree height"
            if self.__TrunkDiam > self.__Height:
                valid = False
                msg = "Trunk diameter is greater than tree height"

        return valid, msg


class BoundingBox:
    def __init__(self):
        self.__xMin = float("inf")
        self.__xMax = 0
        self.__yMin = float("inf")
        self.__yMax = 0
        self.__zMin = float("inf")
        self.__zMax = 0

    def set_xmin(self, val):
        self.__xMin = val

    def set_ymin(self, val):
        self.__yMin = val

    def set_zmin(self, val):
        self.__zMin = val

    def set_xmax(self, val):
        self.__xMax = val

    def set_ymax(self, val):
        self.__yMax = val

    def set_zmax(self, val):
        self.__zMax = val

    # compares coordinates to bbox, extends bbox if necessary
    def compare(self, x_val, y_val, z_val=1):
        if x_val < self.__xMin:
            self.set_xmin(x_val)

        if x_val > self.__xMax:
            self.set_xmax(x_val)

        if y_val < self.__yMin:
            self.set_ymin(y_val)

        if y_val > self.__yMax:
            self.set_ymax(y_val)

        if z_val < self.__zMin:
            self.set_zmin(z_val)

        if z_val > self.__zMax:
            self.set_zmax(z_val)

    # returns bounding box coordinates
    def get_bbox(self):
        min_vals = [self.__xMin, self.__yMin, self.__zMin]
        max_vals = [self.__xMax, self.__yMax, self.__zMax]
        return [min_vals, max_vals]
