import csv
import sqlite3
import threading

import wx

import default_gui


# GUI class to import DEM into database
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
            msg = wx.MessageDialog(self, "This file seems to have been imported into the database already.\n"
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
            msg = wx.MessageDialog(self, message, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return

        # create and start new thread to do the import
        thread = threading.Thread(target=self.start_import)
        thread.start()

    # method to start the import (executed in new thread
    def start_import(self):
        self.buttonBrowse.Enable(False)
        self.importbutton.Enable(False)
        self.next.Enable(False)

        colstoimport = [self.xvalue.GetSelection(), self.yvalue.GetSelection(), self.heightvalue.GetSelection()]
        importer = DemImporter(self.__filepath, self.__encoding, self.__seperator, colstoimport, self.epsg.GetValue(),
                               self.__EmptyLinesBeforeDataStart, self.__DbFilePath)

        # create table in database for elevation data (if not exists already)
        importer.create_table()

        # start the import of file
        imp = importer.import_file(self.__PointsImported, self.text_rowcount)  # start file import
        if not imp[0]:
            importer.rollback()
            msg = wx.MessageDialog(self, imp[1], style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            self.text_rowcount.SetLabel("%s elevation points imported" % self.__PointsImported)
            return

        importer.commit()

        # update variable for number of points imported
        self.__PointsImported = importer.get_rowcount()

        # Update Text in GUI to show number of points imported
        self.text_rowcount.SetLabel("%s elevation points imported" % self.__PointsImported)  # Update label in GUI
        self.__ImportedFiles.append(self.__filepath)

        importer.close_connection()

        # activate buttons to import further DEM files
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

        self.DoLayoutAdaptation()
        self.Layout()

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


# Real basic database connection with basic functionality
# All other database connections inherit from this class
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

    def rollback(self):
        self._con.rollback()

    # closes database connection
    def close_connection(self):
        self._con.close()

    # returns number of imported points
    def get_rowcount(self):
        self._cursor.execute("SELECT COUNT(*) FROM elevation")
        return self._cursor.fetchone()[0]

    # updates a value in a database column
    # cannot update with string values yet!!!
    def update_value(self, tablename, insert_col, insert_val, where_col=None, where_val=None, where_lowercase=False):
        statement = 'UPDATE %s SET "%s" = %s' % (tablename, insert_col, insert_val)
        if where_col is not None and where_val is not None:
            if not where_lowercase:
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


# Class with basic functionality for DEM importing
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


# Class to import DEM into database
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

    # class to create elevation table
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

    # class to DEM file into database
    def import_file(self, imported_points, text_count):
        success = True
        message = ""
        imported_row_count = imported_points
        with open(self.__filepath, newline='', encoding=self.__encoding) as file:

            # skip empty lines at beginning of file
            counter = 0
            while counter < self.__NumberOfEmptyLines:
                file.readline()
                counter += 1

            csvreader = csv.reader(file, delimiter=self.__seperator)
            for index, line in enumerate(csvreader):
                # skip empty lines
                if not line:
                    continue

                try:
                    x = line[self.__XColIndex]
                    y = line[self.__YColIndex]
                    h = line[self.__HColIndex]
                except IndexError:
                    success = False
                    message = "Error in line %s" % str(index + self.__NumberOfEmptyLines + 1)
                    break

                # Create Text to insert point into database
                pointtext = "GeomFromText('POINT(%s %s)', 5677)" % (x, y)

                # insert point into database
                try:
                    self._cursor.execute('INSERT INTO elevation VALUES (%s, %s);' % (h, pointtext))
                except sqlite3.OperationalError:
                    success = False
                    message = "Error in line %s" % str(index + self.__NumberOfEmptyLines + 1)
                    break

                imported_row_count += 1

                # Update label in GUI every 10.000 imported lines
                if imported_row_count % 10000 == 0:
                    text_count.SetLabel("%s elevation points imported" % imported_row_count)

        return success, message


# Derived GUI class to hight values
class GrabHeight(default_gui.GrabHeight):
    def __init__(self, parent, dbpath):
        default_gui.GrabHeight.__init__(self, parent)
        self.__DbFilePath = dbpath
        self.__running = False
        self.populate_dropdown()
        self.DoLayoutAdaptation()
        self.Layout()

    # method to populate dropdowns
    def populate_dropdown(self):
        col_names = self.GetParent().db.get_column_names()
        geom_names = self.GetParent().db.get_column_names_geom()
        self.id.SetItems(col_names)
        self.geom.SetItems(geom_names)

    # method called when checkbox is hit:
    # activates TextBox to enter Search radius
    def on_checkbox_hit(self, event):
        self.radius.Enabled = not self.radius.Enabled

    # method called when dropdown changes
    # if all dropdowns have been chosen, Button to Assign hight activates (if program is not running)
    def validate(self, event):
        valid = True
        if not self.__running:
            if self.id.GetSelection() == wx.NOT_FOUND:
                valid = False
            if self.geom.GetSelection() == wx.NOT_FOUND:
                valid = False
        else:
            valid = False
        if valid:
            self.assign.Enable(True)

    # method to be called when Assign Height button is pushed:
    # Starts height assigning process
    def on_assign(self, event):
        valid, message = self.validate_input()
        if not valid:
            msg = wx.MessageDialog(self, message, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return
        self.assign.Enable(False)
        self.__running = True
        self.GetParent().db.add_col("Height_DEM", "REAL")  # Adds Hight_DEM column to Tree data table

        # Create and start new thread
        thread = threading.Thread(target=self.start_assign)
        thread.start()

    # method to validate user input (search radius)
    def validate_input(self):
        valid = True
        message = ""
        if self.use_radius.GetValue():
            try:
                int(self.radius.GetValue())
            except ValueError:
                valid = False
                message = "Radius must be an integer"

        return valid, message

    # method to administer the assigning (called in new thread)
    def start_assign(self):
        try:
            radius = int(self.radius.GetValue())
        except ValueError:
            radius = 0
        assigner = AssignHeight(self.__DbFilePath, self.GetParent().db, self.id.GetStringSelection(),
                                self.geom.GetStringSelection(), self.GetParent().db.get_tree_table_name(),
                                self.gauge, self.use_radius.GetValue(), radius)
        assigner.assign()
        assigner.commit()
        self.EndModal(1)


# class that adds hight to the trees
class AssignHeight(BasicConnection):
    def __init__(self, dbpath, db, idcol, geomcol, treetable, gauge, use_searchradius, searchradius):
        BasicConnection.__init__(self, dbpath)
        self.__db = db
        self.__IdCol = idcol
        self.__GeomCol = geomcol
        self.__TreeTableName = treetable
        self.__gauge = gauge
        self.__use_searchradius = use_searchradius
        self.__searchradius = searchradius

    # method to do the actual assigning of hights
    def assign(self):
        innercursor = self._con.cursor()

        # SELECT part of the statemnet
        statement = 'SELECT %s."%s", X(%s."%s"), Y(%s."%s") FROM %s, convexhull'\
                    % (self.__TreeTableName, self.__IdCol,
                       self.__TreeTableName, self.__GeomCol,
                       self.__TreeTableName, self.__GeomCol,
                       self.__TreeTableName)
        countstatement = 'SELECT count(%s.ROWID) FROM %s, convexhull' % (self.__TreeTableName, self.__TreeTableName)

        # WHERE part of the statement
        statement += ' WHERE Intersects(%s."%s", convexhull."geom")==1;' % (self.__TreeTableName, self.__GeomCol)
        countstatement += ' WHERE Intersects(%s."%s", convexhull."geom")==1;' % (self.__TreeTableName, self.__GeomCol)
        self._cursor.execute(countstatement)
        self.__gauge.SetRange(self._cursor.fetchone()[0])
        self._cursor.execute(statement)

        for idx, row in enumerate(self._cursor):
            # SELECT part of the inner statement
            statement = 'SELECT elevation.height, Distance(%s."%s", elevation."geom") FROM elevation, %s' \
                        % (self.__TreeTableName, self.__GeomCol, self.__TreeTableName)

            # WHERE part of the inner statement
            if type(row[0]) == str:
                statement += ' WHERE %s."%s" = "%s"' % (self.__TreeTableName, self.__IdCol, row[0])
            else:
                statement += ' WHERE %s."%s" = %s' % (self.__TreeTableName, self.__IdCol, row[0])

            # Add index constraints to statements (MUCH faster querying!)
            if self.__use_searchradius:
                x = row[1]  # X koordinate of tree
                y = row[2]  # Y koordinate of tree
                statement += ''' AND elevation.ROWID IN'''
                statement += ''' (SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'elevation' '''
                statement += '''AND search_frame = BuildCircleMBR(%s, %s, %s))''' % (x, y, self.__searchradius)

            # ORDER BY part of inner statement to find 4 closest points
            statement += ' ORDER BY Distance(%s."%s", elevation."geom") LIMIT 4;'\
                         % (self.__TreeTableName, self.__GeomCol)

            innercursor.execute(statement)

            # IDW Interpolation (quadratic weights)
            zaehler = 0
            nenner = 0
            for innerrow in innercursor:
                weight = 1. / (innerrow[1]) ** 2
                zaehler += (weight * innerrow[0])
                nenner += weight
            hoehe = zaehler / nenner

            self.update_value(self.__TreeTableName, "Height_DEM", hoehe, self.__IdCol, row[0])
            self.__gauge.SetValue(self.__gauge.GetValue() + 1)


# Class to add Geom objects into the database
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

    # Method to call when button to create geometries is pressed
    def on_add(self, event):
        if not self.validate_input()[0]:
            msg = wx.MessageDialog(self, self.validate_input()[1], style=wx.ICON_WARNING | wx.CENTRE)
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
                dlg = wx.MessageDialog(self, msg, style=wx.ICON_WARNING | wx.CENTRE)
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


# class to add CityGML's vegetation species code to the dataset
class AddCityGmlVegetationCodeGUI(default_gui.add_vegetation_code):
    def __init__(self, parent, dbpath, tablename):
        default_gui.add_vegetation_code.__init__(self, parent)
        self.__DbPath = dbpath
        self.__DbTreeTableName = tablename
        self.__CodeList = []

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
            with open("citygml_vegetation_codes.code", encoding="utf-8") as file:
                csvfile = csv.reader(file, delimiter=":")
                for idx, line in enumerate(csvfile):

                    # ignore empty lines
                    if not line:
                        continue

                    # ignore comments
                    if line[0][0] == "#":
                        continue

                    # Error if there are more than two Doppelpunkt in a line
                    if len(line) < 3:
                        text = "Cannot import Species vegetation codes\n" \
                              "Error in file citygml_vegetation_species_codes.dict in line %s:\n" \
                               "Less than 3 colons in line detected." % str(idx+1)
                        self.__CodeList.clear()
                        success = False
                        break

                    # Error if there are more than two Doppelpunkt in a line
                    if len(line) > 3:
                        text = "Cannot import Species vegetation codes\n" \
                               "Error in file citygml_vegetation_species_codes.dict in line %s:\n" \
                               "More than 3 colons in line detected." % str(idx + 1)
                        self.__CodeList.clear()
                        success = False
                        break

                    # species code must be cast to an integer
                    try:
                        self.__CodeList.append([line[0], int(line[1]), int(line[2])])
                    except ValueError:
                        text = "Cannot import Species vegetation codes\n" \
                               "Error in file citygml_vegetation_species_codes.dict in line %s:\n" \
                               "Code not an integer." % str(idx + 1)
                        self.__CodeList.clear()
                        success = False
                        break
        except FileNotFoundError:
            success = False
            text = "Cannot import Species Vegetation codes.\n" \
                   "Could not find file citygml_vegetation_species_codes.dict in curent directory."
        return success, text

    # method is called when choice is changed
    def on_choice(self, event):
        self.add_code.Enable(True)

    # Method to be called when button Add Code is pushed
    def on_add_code(self, event):
        success, text = self.fill_dict()
        if not success:
            msg = wx.MessageDialog(self, text, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            self.EndModal(1234)
            return

        veg_column = self.choice_vegetation_col.GetStringSelection()  # get column with botanical name
        self.GetParent().db.add_col("CityGML Species Code", "INT")  # add species code column to database table
        self.GetParent().db.add_col("CityGML Class Code", "INT")  # add species code column to database table
        self.GetParent().db.commit()
        con = BasicConnection(self.__DbPath)
        for entry in self.__CodeList:
            con.update_value(self.__DbTreeTableName, "CityGML Species Code", entry[1], veg_column, entry[0], True)
            con.update_value(self.__DbTreeTableName, "CityGML Class Code", entry[2], veg_column, entry[0], True)
        con.commit()
        self.EndModal(12347)
