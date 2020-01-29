import csv
import sqlite3

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
    def on_browse( self, event ):
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

        msg = wx.MessageDialog(None, "Do you like to import another file to the database?",
                               "Import other file?", style=wx.YES_NO)
        importer.close_connection()
        if msg.ShowModal() == wx.ID_YES:
            self.next.Enable()
            self.on_browse(None)
        else:
            self.end_next_step()
            print("weiter gehts")

    # method to be called when file settings change
    # method triggers refresh of grid preview
    def refresh_preview(self, event):
        self.generate_preview()

    def on_next( self, event ):
        self.end_next_step()

    def end_next_step(self):
        connection = BasicConnection(self.__DbFilePath, self.epsg.GetValue())
        connection.generate_spatial_index()
        connection.generate_convexhull()
        connection.commit()
        connection.close_connection()
        self.EndModal(1234)

    # method to generate grid preview and gather information about file
    def generate_preview(self):
        with open(self.__filepath, encoding=self.encoding.GetValue()) as file:

            self.initialize()

            if self.previewgrid.GetNumberRows() > 0:
                self.previewgrid.DeleteRows(0, self.previewgrid.GetNumberRows())
            if self.previewgrid.GetNumberCols() > 0:
                self.previewgrid.DeleteCols(0, self.previewgrid.GetNumberCols())

            filereader = csv.reader(file, delimiter=self.__seperator)

            headersFound = False
            headers = []
            start_data = 0
            data_started = False
            max_rows = 5-1
            subtractor = 0

            for RowIndex, line in enumerate(filereader):
                if RowIndex > max_rows:
                    break

                if not line:
                    max_rows += 1
                    if not data_started:
                        start_data += 1
                    if data_started:
                        subtractor += 1
                    continue

                if self.__filecontainscolumnnames and not headersFound:
                    headers = line
                    headersFound = True
                    max_rows += 1
                    continue

                data_started = True

                if len(line) > self.previewgrid.GetNumberCols():
                    self.previewgrid.AppendCols(len(line)-self.previewgrid.GetNumberCols())

                self.previewgrid.AppendRows()
                if self.__filecontainscolumnnames:
                    for ColIndex, value in enumerate(line):
                        self.previewgrid.SetCellValue(RowIndex-start_data-subtractor-1, ColIndex, value)
                else:
                    for ColIndex, value in enumerate(line):
                        self.previewgrid.SetCellValue(RowIndex-start_data-subtractor, ColIndex, value)

        if not self.__filecontainscolumnnames:
            for element in range(0, self.previewgrid.GetNumberCols()):
                headers.append("col_"+str(element+1))

        for idx, header in enumerate(headers):
            self.previewgrid.SetColLabelValue(idx, header)
        self.__FileColumns = headers

        self.previewgrid.AutoSizeColumns()
        self.previewgrid.AutoSizeRows()
        self.Layout()
        self.SetSize(-1, -1, -1, self.GetSize().GetHeight()+10)

        self.populate_dropdown()
        if self.__filecontainscolumnnames:
            self.__EmptyLinesBeforeDataStart = start_data+1
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

    # Override ShowModal Class of parent to manipulate return value
    # def EndModal(self, retCode):
    #    super().EndModal(1234566)


class BasicConnection:
    def __init__(self, databasepath, ref):
        self._ReferenceSystemCode = ref
        self._DbFilePath = databasepath
        self._con = sqlite3.connect(self._DbFilePath)
        self._cursor = self._con.cursor()
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

    # create a spatial over geometries
    def generate_spatial_index(self):
        self._cursor.execute("SELECT CreateSpatialIndex('elevation', 'geom');")

    # returns number of imported points
    def get_rowcount(self):
        self._cursor.execute("SELECT COUNT(*) FROM elevation")
        return self._cursor.fetchone()[0]

    # ceate a new table and store a convexhull-polygon in it
    def generate_convexhull(self):
        self._cursor.execute("DROP TABLE IF EXISTS convexhull;")
        self._cursor.execute("CREATE TABLE convexhull (typ TEXT)")
        self._cursor.execute(
            'SELECT AddGeometryColumn("convexhull", "geom" , %s, "POLYGON", "XY");' % self._ReferenceSystemCode)
        self._cursor.execute('INSERT INTO convexhull SELECT "convex", ConvexHull(Collect(geom)) FROM elevation;')

class DemImporter(BasicConnection):
    def __init__(self, filepath, encoding, sep, colstoimport, ref, emptylines, dbpath):
        self.__filepath = filepath
        self.__encoding = encoding
        self.__seperator = sep
        self.__XColIndex = colstoimport[0]
        self.__YColIndex = colstoimport[1]
        self.__HColIndex = colstoimport[2]
        self.__NumberOfEmptyLines = emptylines

        BasicConnection.__init__(self, dbpath, ref)

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
                    message = "Error in line %s" % str(index+self.__NumberOfEmptyLines+1)
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


class GrabHeight(default_gui.derive_height):
    def __init__(self, parent):
        default_gui.derive_height.__init__(self, parent)
