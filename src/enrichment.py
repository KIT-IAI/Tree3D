import csv
import sqlite3
import threading

import wx

import default_gui


class ImportHeight(default_gui.import_dem):
    def __init__(self, parent, dbpath):
        default_gui.import_dem.__init__(self, parent)

        self.__filepath = ""  # variable for DEM filepath
        self.__ImportedFiles = []  # list of already imported files
        self.__encoding = ""  # variable for file encoding (through GUI)
        self.__seperator = ""  # variable for file data seperator
        self.__filecontainscolumnnames = False  # variable to store if file contains column names
        self.__FileColumns = []  # list for columns in file
        self.__EmptyLinesBeforeDataStart = -1  # variable for number of lines before data starts
        self.__PointsImported = 0  # number of points imported to database
        self.__DbFilePath = dbpath  # path of database

        self.DoLayoutAdaptation()
        self.Layout()

    # method to innitialize settings before preview is generated and before import
    def initialize(self):
        self.__encoding = self.encoding.GetValue()

        sep = ""
        if self.delim.GetSelection() == 0:
            sep = " "
        elif self.delim.GetSelection() == 1:
            sep = ","
        elif self.delim.GetSelection() == 2:
            sep = "\t"
        elif self.delim.GetSelection() == 3:
            sep = ";"

        self.__seperator = sep
        self.__filecontainscolumnnames = self.contains_columns.GetValue()

    # method to be called when "Browse" button is pushed in UI
    def on_browse(self, event):
        self.initialize()
        dialog = wx.FileDialog(self, "Open DEM file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        if dialog.GetPath() in self.__ImportedFiles:
            msg = wx.MessageDialog(None, "This file seems to have been imported into the database already.\n"
                                         "Do you like to import it anyway?",
                                   "Import warning?", style=wx.YES_NO | wx.ICON_WARNING)
            if msg.ShowModal() == wx.ID_YES:
                pass
            else:
                self.on_browse(None)
                return

        self.__filepath = dialog.GetPath()
        self.filepat_textbox.SetValue(self.__filepath)

        self.importbutton.Enable(True)
        self.text_rowcount.Enable(True)
        self.generate_preview()

    # method to be called when button "Import DEM" is pressed
    def on_import_dem(self, event):
        valid = self.validate_input()[0]
        message = self.validate_input()[1]
        if not valid:
            msg = wx.MessageDialog(None, message, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return

        thread = threading.Thread(target=self.start_import)
        thread.start()

    def start_import(self):
        self.buttonBrowse.Enable(False)
        self.importbutton.Enable(False)
        self.next.Enable(False)

        colstoimport = [self.xvalue.GetSelection(), self.yvalue.GetSelection(), self.heightvalue.GetSelection()]
        importer = DemImporter(self.__filepath, self.__encoding, self.__seperator, colstoimport, self.epsg.GetValue(),
                               self.__EmptyLinesBeforeDataStart, self.__DbFilePath)
        importer.create_table()  # create table in database for elevation data (if not exists already)
        imp = importer.import_file(self.__PointsImported, self.text_rowcount)  # start file import
        if not imp[0]:
            msg = wx.MessageDialog(None, imp[1], style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            self.text_rowcount.SetLabel("%s elevation points imported" % self.__PointsImported)
            return

        importer.commit()
        self.__PointsImported = importer.get_rowcount()  # update variable for number of points imported

        self.text_rowcount.SetLabel("%s elevation points imported" % self.__PointsImported)  # Update label in GUI
        self.__ImportedFiles.append(self.__filepath)

        importer.close_connection()

        self.buttonBrowse.Enable(True)
        self.importbutton.Enable(True)
        self.next.Enable(True)

    # method to be called when file settings change
    # method triggers refresh of grid preview
    def refresh_preview(self, event):
        self.generate_preview()

    # method to be called when "Next" button is pushed
    def on_next(self, event):
        self.buttonBrowse.Enable(False)
        self.importbutton.Enable(False)
        self.next.Enable(False)
        threat = threading.Thread(target=self.end_next_step)
        threat.start()

    # method to be called when all files are imported. Finish up import, initialize next step
    def end_next_step(self):
        connection = BasicDemConnection(self.__DbFilePath, self.epsg.GetValue())
        self.text_rowcount.SetLabel("Please Wait: Generating Spatial Index...")
        connection.generate_spatial_index()
        self.text_rowcount.SetLabel("Please Wait: Generating Convexhull...")
        connection.generate_convexhull()
        connection.commit()
        connection.close_connection()
        self.EndModal(1234)

    # method to generate grid preview and gather information about file
    def generate_preview(self):
        self.initialize()
        with open(self.__filepath, encoding=self.encoding.GetValue()) as file:

            if self.previewgrid.GetNumberRows() > 0:
                self.previewgrid.DeleteRows(0, self.previewgrid.GetNumberRows())
            if self.previewgrid.GetNumberCols() > 0:
                self.previewgrid.DeleteCols(0, self.previewgrid.GetNumberCols())

            filereader = csv.reader(file, delimiter=self.__seperator)

            headers_found = False
            headers = []
            start_data = 0
            data_started = False
            max_rows = 5 - 1
            subtractor = 0

            for RowIndex, line in enumerate(filereader):
                if RowIndex > max_rows:
                    break

                # what to do if line has no data
                if not line:
                    max_rows += 1
                    if not data_started:
                        start_data += 1
                    if data_started:
                        subtractor += 1
                    continue

                # get column names from file
                if self.__filecontainscolumnnames and not headers_found:
                    headers = line
                    headers_found = True
                    max_rows += 1
                    continue

                data_started = True

                # Add new column to previewgrid if it does not have enough
                if len(line) > self.previewgrid.GetNumberCols():
                    self.previewgrid.AppendCols(len(line) - self.previewgrid.GetNumberCols())

                # Add row to grid and fill it with data
                self.previewgrid.AppendRows()
                if self.__filecontainscolumnnames:
                    for ColIndex, value in enumerate(line):
                        self.previewgrid.SetCellValue(RowIndex - start_data - subtractor - 1, ColIndex, value)
                else:
                    for ColIndex, value in enumerate(line):
                        self.previewgrid.SetCellValue(RowIndex - start_data - subtractor, ColIndex, value)

        # generate column names in case file has none
        if not self.__filecontainscolumnnames:
            for element in range(0, self.previewgrid.GetNumberCols()):
                headers.append("col_" + str(element + 1))

        # set column headers
        for idx, header in enumerate(headers):
            self.previewgrid.SetColLabelValue(idx, header)
        self.__FileColumns = headers

        self.previewgrid.AutoSizeColumns()
        self.previewgrid.AutoSizeRows()
        self.Layout()
        self.SetSize(-1, -1, -1, self.GetSize().GetHeight() + 10)

        self.populate_dropdown()
        if self.__filecontainscolumnnames:
            self.__EmptyLinesBeforeDataStart = start_data + 1
        else:
            self.__EmptyLinesBeforeDataStart = start_data

    def validate_input(self):
        valid = True
        message = ""

        if self.yvalue.GetSelection() == self.heightvalue.GetSelection():
            valid = False
            message = "Y Value and Height Value must not be the same column"

        if self.xvalue.GetSelection() == self.heightvalue.GetSelection():
            valid = False
            message = "X Value and Height Value must not be the same column"

        if self.xvalue.GetSelection() == self.yvalue.GetSelection():
            valid = False
            message = "X Value an Y Value must not be the same column"

        try:
            int(self.epsg.GetValue())
        except ValueError:
            valid = False
            message = "Please enter a valid EPSG Code\n" \
                      "EPSG Input must be an integer number"

        if self.epsg.GetValue() == "":
            valid = False
            message = "EPSG Code not specified"

        if self.heightvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
            message = "No height value column specified"

        if self.yvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
            message = "No Y Value column specified"

        if self.xvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
            message = "No X Value column specified"
        return valid, message

    # method to populate dropdowns with columns from file
    def populate_dropdown(self):
        self.xvalue.SetItems(self.__FileColumns)
        self.yvalue.SetItems(self.__FileColumns)
        self.heightvalue.SetItems(self.__FileColumns)


class BasicConnection:
    def __init__(self, databasepath):
        self._DbFilePath = databasepath
        self._con = sqlite3.connect(self._DbFilePath)
        self._cursor = self._con.cursor()
        self._updatecursor = self._con.cursor()
        self._con.enable_load_extension(True)
        self._con.execute('SELECT load_extension("mod_spatialite");')

        # next method call to initialize spatial metadata: causes error when called multiple times, but its harmless
        self._con.execute('SELECT InitSpatialMetaData(1);')
        self._con.commit()

    # performs a commit
    def commit(self):
        self._con.commit()

    # closes database connection
    def close_connection(self):
        self._con.close()

    # returns number of imported points
    def get_rowcount(self):
        self._cursor.execute("SELECT COUNT(*) FROM elevation")
        return self._cursor.fetchone()[0]

    # updates a value in a database column
    # cannot update with string values yet!!!
    def update_value(self, tablename, insert_col, insert_val, where_col=None, where_val=None, where_lower=False):
        statement = 'UPDATE %s SET "%s" = %s' % (tablename, insert_col, insert_val)
        if where_col is not None and where_val is not None:
            if not where_lower:
                if type(where_val) == str:
                    statement += ' WHERE "%s" = "%s"' % (where_col, where_val)
                else:
                    statement += ' WHERE "%s" = %s' % (where_col, where_val)
            else:
                if type(where_val) == str:
                    statement += ' WHERE lower("%s") = "%s"' % (where_col, where_val)
                else:
                    statement += ' WHERE lower("%s") = %s' % (where_col, where_val)
        statement += ';'
        self._updatecursor.execute(statement)


class BasicDemConnection(BasicConnection):
    def __init__(self, dbpath, ref):
        BasicConnection.__init__(self, dbpath)
        self._ReferenceSystemCode = ref

    # ceate a new table and store a convexhull-polygon in it
    def generate_convexhull(self):
        self._cursor.execute("DROP TABLE IF EXISTS convexhull;")
        self._cursor.execute("CREATE TABLE convexhull (typ TEXT)")
        self._cursor.execute(
            'SELECT AddGeometryColumn("convexhull", "geom" , %s, "POLYGON", "XY");' % self._ReferenceSystemCode)
        self._cursor.execute('INSERT INTO convexhull SELECT "convex", ConvexHull(Collect(geom)) FROM elevation;')

    # create a spatial over geometries
    def generate_spatial_index(self):
        self._cursor.execute("SELECT CreateSpatialIndex('elevation', 'geom');")


class DemImporter(BasicDemConnection):
    def __init__(self, filepath, encoding, sep, colstoimport, ref, emptylines, dbpath):
        self.__filepath = filepath
        self.__encoding = encoding
        self.__seperator = sep
        self.__XColIndex = colstoimport[0]
        self.__YColIndex = colstoimport[1]
        self.__HColIndex = colstoimport[2]
        self.__NumberOfEmptyLines = emptylines

        BasicDemConnection.__init__(self, dbpath, ref)

    def create_table(self):
        self._cursor.execute('CREATE TABLE IF NOT EXISTS elevation (height REAL);')

        self._cursor.execute("pragma table_info(elevation);")

        colnames = []
        for row in self._cursor:
            colnames.append(row[1])

        if 'geom' not in colnames:
            self._cursor.execute('SELECT AddGeometryColumn("elevation", "geom" , %s, "POINT", "XY");'
                                 % self._ReferenceSystemCode)
        self._con.commit()

    def import_file(self, imported_points, text_count):
        success = True
        message = ""
        imported_row_count = imported_points
        with open(self.__filepath, newline='', encoding=self.__encoding) as file:

            counter = 0
            while counter < self.__NumberOfEmptyLines:
                file.readline()
                counter += 1

            csvreader = csv.reader(file, delimiter=self.__seperator)
            for index, line in enumerate(csvreader):
                if not line:
                    continue

                try:
                    x = line[self.__XColIndex]
                    y = line[self.__YColIndex]
                    h = line[self.__HColIndex]
                except IndexError:
                    self._con.rollback()
                    success = False
                    message = "Error in line %s" % str(index + self.__NumberOfEmptyLines + 1)
                    break

                pointtext = "GeomFromText('POINT(%s %s)', 5677)" % (x, y)

                try:
                    self._cursor.execute('INSERT INTO elevation VALUES (%s, %s);' % (h, pointtext))
                except sqlite3.OperationalError:
                    self._con.rollback()
                    success = False
                    message = "Error in line %s" % str(index + self.__NumberOfEmptyLines + 1)
                    break
                imported_row_count += 1
                if imported_row_count % 10000 == 0:
                    text_count.SetLabel("%s elevation points imported" % imported_row_count)

        return success, message


class GrabHeight(default_gui.GrabHeight):
    def __init__(self, parent, dbpath):
        default_gui.GrabHeight.__init__(self, parent)
        self.__DbFilePath = dbpath
        self.populate_dropdown()
        self.DoLayoutAdaptation()
        self.Layout()

    def populate_dropdown(self):
        col_names = self.GetParent().db.get_column_names()
        geom_names = self.GetParent().db.get_column_names_geom()
        self.id.SetItems(col_names)
        self.geom.SetItems(geom_names)

    def validate(self, event):
        valid = True
        if self.id.GetSelection() == wx.NOT_FOUND:
            valid = False
        if self.geom.GetSelection() == wx.NOT_FOUND:
            valid = False
        if valid:
            self.assign.Enable(True)

    def on_assign(self, event):
        self.assign.Enable(False)
        self.GetParent().db.add_col("height", "REAL")
        thread = threading.Thread(target=self.start_assign)
        thread.start()

    def start_assign(self):
        assigner = AssignHeight(self.__DbFilePath, self.GetParent().db, self.id.GetStringSelection(),
                                self.geom.GetStringSelection(), self.GetParent().db.get_tree_table_name(),
                                self.gauge)
        assigner.assign()
        assigner.commit()
        self.EndModal(1)


class AssignHeight(BasicConnection):
    def __init__(self, dbpath, db, idcol, geomcol, treetable, gauge):
        BasicConnection.__init__(self, dbpath)
        self.__db = db
        self.__IdCol = idcol
        self.__GeomCol = geomcol
        self.__TreeTableName = treetable
        self.__gauge = gauge

    def assign(self):
        innercursor = self._con.cursor()
        statement = 'SELECT %s.%s FROM %s, convexhull' % (self.__TreeTableName, self.__IdCol, self.__TreeTableName)
        countstatement = 'SELECT count(%s.ROWID) FROM %s, convexhull' % (self.__TreeTableName, self.__TreeTableName)
        statement += ' WHERE Intersects(%s."%s", convexhull.geom)==1' % (self.__TreeTableName, self.__GeomCol)
        countstatement += ' WHERE Intersects(%s."%s", convexhull.geom)==1' % (self.__TreeTableName, self.__GeomCol)
        self._cursor.execute(countstatement)
        self.__gauge.SetRange(self._cursor.fetchone()[0])
        self._cursor.execute(statement)
        for idx, row in enumerate(self._cursor):
            print(idx)
            statement = "SELECT elevation.height, Distance(%s.%s, elevation.geom) FROM elevation, %s" \
                        % (self.__TreeTableName, self.__GeomCol, self.__TreeTableName)
            if type(row[0]) == str:
                statement += ' WHERE %s."%s" = "%s"' % (self.__TreeTableName, self.__IdCol, row[0])
            else:
                statement += ' WHERE %s."%s" = %s' % (self.__TreeTableName, self.__IdCol, row[0])
            statement += ' ORDER BY Distance(%s.%s, elevation.geom) LIMIT 4;' % (self.__TreeTableName, self.__GeomCol)
            innercursor.execute(statement)

            # IDW Interpolation (quadratic weights)
            zaehler = 0
            nenner = 0
            for innerrow in innercursor:
                weight = 1. / (innerrow[1]) ** 2
                zaehler += (weight * innerrow[0])
                nenner += weight
            hoehe = zaehler / nenner

            self.update_value(self.__TreeTableName, "height", hoehe, self.__IdCol, row[0])
            self.__gauge.SetValue(self.__gauge.GetValue() + 1)

        print("fertig")


# Class for GUI to assign Height to Trees
class AddGeometry(default_gui.geom_props):
    def __init__(self, parent):
        default_gui.geom_props.__init__(self, parent)
        self.populate_dropdown()
        self.DoLayoutAdaptation()
        self.Layout()

    # method to populate dropdowns
    def populate_dropdown(self):
        col_list = self.GetParent().db.get_column_names()
        num_col_list = self.GetParent().db.get_column_names_numeric()
        self.xvalue.SetItems(num_col_list)
        self.yvalue.SetItems(num_col_list)
        self.id.SetItems(col_list)
        self.Layout()

    # activate button if all dropdowns are used
    def validate(self, event):
        valid = True

        if self.xvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
        if self.yvalue.GetSelection() == wx.NOT_FOUND:
            valid = False
        if self.id.GetSelection() == wx.NOT_FOUND:
            valid = False
        if self.epsg.GetValue() == "":
            valid = False

        if valid:
            self.add.Enable(True)
        else:
            self.add.Enable(False)

    # Method to call when button "Get Height" is pressed
    def on_add(self, event):
        if not self.validate_input()[0]:
            msg = wx.MessageDialog(None, self.validate_input()[1], style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return

        self.GetParent().db.add_geom_col(self.epsg.GetValue())

        collist = [self.id.GetStringSelection(), self.xvalue.GetStringSelection(), self.yvalue.GetStringSelection()]
        cursor = self.GetParent().db.get_data_by_collist(collist)
        for row in cursor:
            try:
                self.GetParent().db.update_value("geom", "GeomFromText('POINT(%s %s)',%s)" % (row[1], row[2],
                                                                                              self.epsg.GetValue()),
                                                 self.id.GetStringSelection(), row[0])
            except sqlite3.OperationalError:
                self.GetParent().db.rollback()
                self.GetParent().db.remove_col_from_collist("geom")
                msg = "Something went wrong while creating geometries."
                dlg = wx.MessageDialog(None, msg, style=wx.ICON_WARNING | wx.CENTRE)
                dlg.ShowModal()
                break
        else:
            self.GetParent().db.add_spatial_index("geom")
            self.GetParent().db.commit()
        self.EndModal(1)

    # method to validate user input
    def validate_input(self):
        valid = True
        message = ""

        try:
            int(self.epsg.GetValue())
        except ValueError:
            valid = False
            message = "Please enter a valid EPSG Code\n" \
                      "EPSG Input must be an integer number"

        if self.xvalue.GetSelection() == self.yvalue.GetSelection():
            valid = False
            message = "X Value and Y Value must not be the same column"

        return valid, message


# Method to add CityGML's vegetation species code to the dataset
class AddCityGmlVegetationCodeGUI(default_gui.add_vegetation_code):
    def __init__(self, parent, dbpath, tablename):
        default_gui.add_vegetation_code.__init__(self, parent)
        self.__DbPath = dbpath
        self.__DbTreeTableName = tablename
        self.__CodeDict = {}

        self.populate_dropdowns()
        self.DoLayoutAdaptation()
        self.Layout()

    def populate_dropdowns(self):
        collist = self.GetParent().db.get_column_names()
        self.choice_vegetation_col.SetItems(collist)

    # method to fill the dictionary which is used to look up values
    def fill_dict(self):
        success = True
        text = ""
        try:
            with open("citygml_vegetation_species_codes.dict", encoding="utf-8") as file:
                csvfile = csv.reader(file, delimiter=":")
                for idx, line in enumerate(csvfile):
                    if not line:  # ignore empty lines
                        continue

                    if line[0][0] == "#":  # ignore comments
                        continue

                    if len(line) != 2:  # Error if there are more than two Doppelpunkt in a line
                        text = "Cannot import Species vegetation codes\n" \
                              "Error in file citygml_vegetation_species_codes.dict in line %s:\n" \
                               "More than one colon detected." % str(idx+1)
                        self.__CodeDict.clear()
                        success = False
                        break

                    try:  # Code must be cast to an integer
                        self.__CodeDict[line[0]] = int(line[1])
                    except ValueError:
                        text = "Cannot import Species vegetation codes\n" \
                               "Error in file citygml_vegetation_species_codes.dict in line %s:\n" \
                               "Code not an integer." % str(idx + 1)
                        self.__CodeDict.clear()
                        success = False
                        break
        except FileNotFoundError:
            success = False
            text = "Cannot import Species Vegetation codes.\n" \
                   "Could not find file citygml_vegetation_species_codes.dict in curent directory."
        return success, text

    # Method to be called when button Add Code is pushed
    def on_add_code(self, event):
        success, text = self.fill_dict()
        if not success:
            msg = wx.MessageDialog(self, text, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            self.EndModal(1234)
            return

        veg_column = self.choice_vegetation_col.GetStringSelection()
        self.GetParent().db.add_col("code", "INT")
        self.GetParent().db.commit()
        con = BasicConnection(self.__DbPath)
        for v in self.__CodeDict:
            con.update_value(self.__DbTreeTableName, "code", self.__CodeDict[v], veg_column, v, True)
        con.commit()
        self.EndModal(12347)

