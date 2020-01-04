import uuid
import math

import default_gui

import wx


# DialogBox to check for duplicate elements in data by ID
class CheckDuplicateId(default_gui.OnCheckDuplicateIdDialog):
    def __init__(self, parent):
        default_gui.OnCheckDuplicateIdDialog.__init__(self, parent)
        self.populate_dropdown()

    # populate dropdown with grid columns in dialogbox
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.IdColumns.SetItems(colitemlist)

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
        collist = [itemcolname]  # name of column but in a list

        # displays selected column name in column labels of grids
        self.DuplicateGrid.SetColLabelValue(0, itemcolname)
        self.DuplicateGrid.SetColLabelValue(1, "#")
        self.UUIDGrid.SetColLabelValue(0, itemcolname)

        # performs a selection for every value to be checkt with WHERE clause
        # check_value: all distinct values of one column
        duplicate_counter = 0
        uuid_counter = 0
        all_data = self.GetParent().db.get_data_by_collist_distinct(collist).fetchall()
        for check_value in all_data:
            data_cursor = self.GetParent().db.get_data_with_condition('WHERE "%s" = "%s"'
                                                                      % (itemcolname, check_value[0]))
            dat = data_cursor.fetchall()

            # if query returns >1 rows (e.g. two entries with one ID), add values to grid
            if len(dat) > 1:
                self.DuplicateGrid.AppendRows(1)
                self.DuplicateGrid.SetCellValue(duplicate_counter, 0, str(check_value[0]))
                self.DuplicateGrid.SetCellValue(duplicate_counter, 1, str(len(dat)))
                duplicate_counter += 1
            # perform uuid validation if uuid-checkbox was activated
            if self.UUIDCheck.GetValue():
                try:
                    uuid.UUID('{%s}' % check_value[0])
                except ValueError:
                    # add UUID to grid if invalid
                    self.UUIDGrid.AppendRows(1)
                    self.UUIDGrid.SetCellValue(uuid_counter, 0, str(check_value[0]))
                    uuid_counter += 1

        # change info message if no duplicates have been found
        # otherwise: show grid with duplicates
        if duplicate_counter == 0:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed.\nNo duplicates have been found")
        else:
            self.DuplicateGrid.Show(True)
        self.InfoTextDuplicate.Show(True)

        # change info message if no invalid uuid was found
        # otherwise: show grid with invalid uuids
        if self.UUIDCheck.GetValue():
            if uuid_counter == 0:
                self.InfoTextUUID.SetLabel("UUID-Validation completed.\nNo invalid UUIDs found")
            else:
                self.UUIDGrid.Show(True)
            self.InfoTextUUID.Show(True)

        self.Layout()


# DialogBox to check for duplicate elements in data by ID
class CheckDuplicateGeom(default_gui.OnCheckDuplicateGeomDialog):
    def __init__(self, parent):
        default_gui.OnCheckDuplicateGeomDialog.__init__(self, parent)
        self.populate_dropdown()

    # populate dropdown with grid columns in dialogbox
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.IdColumns.Set(colitemlist)
        self.xvalue.SetItems(colitemlist)
        self.yvalue.SetItems(colitemlist)

    # method to be executed when hitting Analyze Button in DialogBox
    # Checks if data contains duplicate geometries
    # objects are considered duplicates when their (2D)-Distance is smaller than a threshold
    def on_analyze(self, event):
        if not self.validate_entries():
            return

        # set max value of progressbar in gui
        self.gauge.SetRange(self.GetParent().db.get_number_of_tablerecords())

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
        data_cursor = self.GetParent().db.get_data_by_collist(collist)
        data = data_cursor.fetchall()

        # compare every tree with every other tree in the dataset
        for idx_low in range(0, len(data)):
            # move progress bar
            self.gauge.SetValue(idx_low+1)

            # coordinates of first tree to be considered
            x1 = data[idx_low][1]
            y1 = data[idx_low][2]

            for idx_high in range(idx_low+1, len(data)):

                # coordinates of second tree to be considered
                x2 = data[idx_high][1]
                y2 = data[idx_high][2]

                # calculate squared distance between both trees
                try:
                    dist_sq = (x1-x2)**2 + (y1-y2)**2
                except TypeError:
                    warningtext = "Cannot perform calculations with values in X or Y column.\n" \
                                  "Value in specified X or Y grid column is most likely not numeric.\n" \
                                  "Was the correct grid column chosen for X and Y value?"
                    msg = wx.MessageDialog(self, warningtext, caption="Error",
                                           style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
                    msg.ShowModal()
                    return

                if dist_sq < float(self.threshold.GetLineText(0).replace(",", "."))**2:
                    result_list.append([data[idx_low][0], data[idx_high][0], math.sqrt(dist_sq)])
        self.gauge.SetValue(0)
        print("fertig")
        for row in result_list:
            print(row)

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

        self.populate_columns()

    def populate_columns(self):
        collist = self.GetParent().db.get_column_names()

        self.choiceID.SetItems(collist)
        self.choiceHeight.SetItems(collist)
        self.choiceTrunk.SetItems(collist)
        self.choiceCrown.SetItems(collist)

    def validate(self):
        valid = True
        message = ""

        identify = self.choiceID.GetSelection()
        height = self.choiceHeight.GetSelection()
        trunk = self.choiceTrunk.GetSelection()
        crown = self.choiceCrown.GetSelection()

        if trunk == crown and trunk != wx.NOT_FOUND:
            valid = False
            message = "Trunk column must not be the same as crown column"

        if height == crown and height != wx.NOT_FOUND:
            valid = False
            message = "Height column must not be the same as crown column"

        if height == trunk and height != wx.NOT_FOUND:
            valid = False
            message = "Height column must not be the same as trunk column"

        if identify == crown and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as crown column"

        if identify == trunk and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as trunk column"

        if identify == height and identify != wx.NOT_FOUND:
            valid = False
            message = "ID column must not be the same as height column"

        if crown == wx.NOT_FOUND:
            valid = False
            message = "Crown diameter column must not be empty."

        if trunk == wx.NOT_FOUND:
            valid = False
            message = "Trunk diameter column must not be empty"

        if height == wx.NOT_FOUND:
            valid = False
            message = "Height column must not be empty"

        if identify == wx.NOT_FOUND:
            valid = False
            message = "ID Column must not be empty."

        if not valid:
            msg = wx.MessageDialog(self, message, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()

        return valid

    def on_analyze(self, event):
        if not self.validate():
            return

        self.analysis_invalid.Show(False)
        self.analysis_valid.Show(False)
        self.result_grid.Show(False)

        collist = [self.choiceID.GetStringSelection(),
                   self.choiceHeight.GetStringSelection(),
                   self.choiceTrunk.GetStringSelection(),
                   self.choiceCrown.GetStringSelection()]

        invalid_trees = []

        for cursor in self.GetParent().db.get_data_by_collist(collist):
            identifier = cursor[0]
            height = cursor[1]
            trunk = cursor[2]
            crown = cursor[3]

            # convert everything into meters
            if self.choiceHeightUnit.GetSelection() == 1:
                try:
                    height = height/100
                except TypeError:
                    pass
            if self.choiceTrunkUnit.GetSelection() == 1:
                try:
                    trunk = trunk/100
                except TypeError:
                    pass
            if self.choiceCrownUnit.GetSelection() == 1:
                try:
                    crown = crown/100
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

            geom = AnalyzeTreeGeoms(height, trunk, crown)
            valid, message = geom.analyze()

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
                    "Trees with invalid geometry parameters have been found.\n" \
                    "%s invalid geometries found." % len(invalid_trees)
            self.analysis_invalid.SetLabel(label)
            self.analysis_invalid.Show(True)

            self.result_grid.HideRowLabels()
            if self.result_grid.GetNumberRows() > 0:
                self.result_grid.DeleteRows(pos=0, numRows=self.result_grid.GetNumberRows())
            self.result_grid.AppendRows(len(invalid_trees))
            for row_index, row in enumerate(invalid_trees):
                for col_index, value in enumerate(row):
                    self.result_grid.SetCellValue(row_index, col_index, value)
            self.result_grid.AutoSizeColumns(False)
            self.result_grid.Show(True)
        self.DoLayoutAdaptation()
        self.Layout()


class AnalyzeTreeGeoms:
    # all parameters must be the same unit
    # trunk and crown must BOTH be diam
    def __init__(self, height, trunk_diam, crown_diam):
        self.__Height = height
        self.__TrunDiam = trunk_diam
        self.__CrownDiam = crown_diam

    # method to analyze parameters
    def analyze(self):
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

        if self.__TrunDiam == 0:
            valid = False
            msg = "Trunk diameter is 0"
        elif self.__TrunDiam is None:
            valid = False
            msg = "No trunk diameter specified"
        elif self.__TrunDiam < 0:
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

        if self.__TrunDiam is not None and self.__CrownDiam is not None:
            if self.__TrunDiam > self.__CrownDiam:
                valid = False
                msg = "Trunk diameter is greater than crown diameter"

        return valid, msg


class BoundingBox:
    def __init__(self):
        self.__xMin = float("inf")
        self.__xMax = 0
        self.__yMin = float("inf")
        self.__yMax = 0

    def set_xmin(self, val):
        self.__xMin = val

    def set_ymin(self, val):
        self.__yMin = val

    def set_xmax(self, val):
        self.__xMax = val

    def set_ymax(self, val):
        self.__yMax = val

    # compares coordinates to bbox, extends bbox if necessary
    def compare(self, x_val, y_val):
        if x_val < self.__xMin:
            self.set_xmin(x_val)

        if x_val > self.__xMax:
            self.set_xmax(x_val)

        if y_val < self.__yMin:
            self.set_ymin(y_val)

        if y_val > self.__xMax:
            self.set_ymax(y_val)

    # returns bounding box coordinates
    def get_bbox(self):
        min_vals = [self.__xMin, self.__yMin]
        max_vals = [self.__xMax, self.__yMax]
        return [min_vals, max_vals]
