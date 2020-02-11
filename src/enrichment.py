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


class AddCityGmlVegetationCodeGUI(default_gui.add_vegetation_code):
    def __init__(self, parent, dbpath, tablename):
        default_gui.add_vegetation_code.__init__(self, parent)
        self.__DbPath = dbpath
        self.__DbTreeTableName = tablename

        self.populate_dropdowns()
        self.DoLayoutAdaptation()
        self.Layout()

    def populate_dropdowns(self):
        collist = self.GetParent().db.get_column_names()
        self.choice_vegetation_col.SetItems(collist)

    def on_add_code(self, event):
        codes = {"picea": 1000, "pinus": 1010, "larix": 1020, "quercus": 1030, "fagus": 1040, "betula": 1050,
                 "alnus": 1060, "populus": 1070, "salix": 1080, "acer": 1090, "fraxinus": 1100, "arabis": 1110,
                 "galeobdolon luteum": 1120, "campanula poscharskyana": 1130, "galium odoratum": 1140,
                 "allium ursinum": 1150, "helleborus": 1160, "alchemilla": 1170, "iris": 1180, "begonia": 1190,
                 "ranunculus asiaticus": 1200, "geranium macrorrhizum ingwersen": 1210, "pelargonie burc double": 1220,
                 "euphorbia": 1230, "aqulilegia": 1240, "symphytum officinale": 1250,
                 "sedum spectabile und sedum telphium": 1260, "centaurea": 1270, "centaurea cysanus": 1280,
                 "lychnis coronaria": 1290, "physalis": 1300, "coreopsis verticillata": 1310, "calendula": 1320,
                 "phlox paniculata": 1330, "dianthus barbatus": 1340, "hemerocallis": 1350, "hemerocallis flava": 1360,
                 "lythrum": 1370, "lysmachia": 1380, "aster novae": 1390, "cardiocrinum giganteum": 1400,
                 "delphinium": 1410, "pteridium": 1420, "gymnocarpium dryopteris": 1430,
                 "matteuccia struthiopteris": 1440, "magnolia elisabeth": 1450, "hibiskus": 1460, "hydrangea": 1470,
                 "cotinus coggygria": 1480, "euonymus europea": 1490, "rhododendron": 1500, "pontederia": 1510,
                 "clematis": 1520, "tropaeolum": 1530, "vicia, lathyrus": 1540, "plumbago": 1550, "zantedeschia": 1560,
                 "fuchsia": 1570, "gerbera": 1580, "nopalxochia": 1590, "cassia": 1610, "cistus": 1620,
                 "abienus festuschristus": 1630, "abies alba": 1640, "abies cephalonica": 1650, "abies concolor": 1660,
                 "abies grandis": 1670, "abies homolepsis": 1680, "abies koreana": 1690, "abies lasiocarpa": 1700,
                 "abies nordmanniana": 1710, "abies pinsapo": 1720, "abies procera": 1730,
                 "abies procera 'glauca'": 1740, "abies veitchii": 1750, "acer campéstre": 1760, "acer campestre": 1760,
                 "acer capillipes": 1770, "acer cappadocicum": 1780, "acer circinatum": 1790, "acer davidii": 1800,
                 "acer ginnala maxim": 1810, "acer grosserii": 1820, "acer monspessulanum": 1830, "acer negundo": 1840,
                 "acer palmatum": 1850, "acer platanoides": 1860, "acer platanoides 'crimson king'": 1870,
                 "acer pseudoplatanus": 1880, "acer rubrum": 1890, "acer saccharinum": 1900,
                 "acer saccharum marsch": 1910, "acer tartaricum": 1920, "aesculus hippocástanum": 1930,
                 "aesculus hippocastanum": 1930, "aesculus x carnea": 1940, "afzelia africana": 1950,
                 "ailanthus altissima": 1960, "alnus cordata": 1970, "alnus glutinosa": 1980, "alnus incána": 1990,
                 "alnus incana": 1990, "alnus viridis": 2000, "amelánchier ovális": 2010, "amelanchier ovalis": 2010,
                 "anacardium occidentale": 2020, "aralia elata": 2030, "araucaria araucana": 2040,
                 "aucuba japonica": 2050, "berberis julianae": 2060, "berberis thunbergii": 2070,
                 "betula alnoides": 2080, "betula costata": 2090, "betula davurica": 2100, "betula ermanii": 2110,
                 "betula papyrifera": 2120, "bétula péndula": 2130, "betula pendula": 2130, "betula pubescens": 2140,
                 "broussonetia papyrifera": 2150, "buddleja davidii": 2160, "butyrospermum parkii": 2170,
                 "buxus sempervirens": 2180, "calocedrus decurrens": 2190,
                 "calocedrus decurrens 'aureovariegata'": 2200, "calycanthus floridus": 2210, "campsis radicans": 2220,
                 "caragana arborescens": 2230, "carpínus bétulus": 2240, "carpinus betulus": 2240,
                 "cassia siberiana": 2250, "castanéa satíva": 2260, "castanea sativa": 2260,
                 "catalpa bignonioides": 2270, "cedrela sinensis": 2280, "cedrus atlantica": 2290,
                 "cedrus atlantica 'glauca'": 2300, "cedrus deodara": 2310, "cedrus deodara var paktia": 2320,
                 "cedrus libani": 2330, "celtis occidentalis": 2340, "cercis siliquastrum": 2350,
                 "chaenomeles japonica": 2360, "chamaecyparis lawsonia": 2370, "chamaecyparis nootkatensis": 2380,
                 "chionanthus virginicus": 2390, "cladrastis lutea": 2400, "clematis montana": 2410,
                 "clematis vitalba": 2420, "colutea arborescens": 2430, "cornus alba": 2440, "cornus florida": 2450,
                 "cornus mas": 2460, "cornus sanguinea": 2470, "córylus avellána": 2480, "corylus avellana": 2480,
                 "corylus avellana 'contorta'": 2490, "córylus colúrna": 2500, "corylus colurna": 2500,
                 "corylus maxima": 2510, "cotoneaster frigidus": 2530, "crataegus laevigata": 2540,
                 "crataegus laevigata 'paul's scarlet'": 2550, "crataegus lavallei 'carrierei'": 2560,
                 "crataegus monogyna": 2570, "cryptomeria japonica": 2580, "cupressus arizonica": 2590,
                 "cupressus sempervirens": 2600, "davidia involucrata": 2610, "delonix regia": 2620,
                 "deutzia scabra": 2630, "dracaena draco": 2640, "elaeagnus angustifolia": 2650,
                 "elaeagnus umbellata": 2660, "euonymus alatus": 2670, "euonymus europaeus": 2680,
                 "euonymus planipes": 2690, "fagus orientalis": 2700, "fagus sylvatica": 2710,
                 "fagus sylvatica 'pendula'": 2720, "fágus sylvática purpuréa": 2730, "fagus sylvatica purpurea": 2730,
                 "ficus carica": 2740, "forsythia x intermedia": 2750, "frangula alnus": 2760,
                 "fraxínus excélsior": 2770, "fraxinus excelsior": 2770, "fraxinus latifolia": 2780,
                 "fraxinus ornus": 2790, "fraxinus paxiana": 2800, "ginkgo biloba l": 2810,
                 "gleditsia triacanthos": 2820, "halesia carolina": 2830, "hamamelis virginiana": 2840,
                 "hamamelis x intermedia": 2850, "hedera helix": 2860, "hibiscus syriacus": 2870,
                 "hippophae rhamnoides": 2880, "ilex aquifolium": 2890, "jasminum nudiflorum": 2900,
                 "juglans nigra": 2910, "juglans regia": 2920, "juniperus communis": 2930, "juniperus sabina": 2940,
                 "kerria japonica 'pleniflora'": 2950, "khaya senegalensis": 2960, "koelreuteria paniculata": 2970,
                 "kolkwitzia amabilis": 2980, "laburnum alpinum": 2990, "laburnum anagyroides": 3000,
                 "larix decidua": 3010, "larix kaempferi": 3020, "ligustrum vulgare": 3030,
                 "liquidambar orientalis": 3040, "liquidambar styraciflua": 3050, "liriodendron tulipifera": 3060,
                 "lonicera maackii": 3070, "lonicera tartarica": 3080, "lonicera x heckrottii": 3090,
                 "lonicera xylosteum": 3100, "magnolia x soulangiana": 3110, "mahonia aquifolium": 3120,
                 "malus floribunda": 3130, "málus sylvéstris": 3140, "malus sylvestris": 3140,
                 "malus toringoides": 3150, "mespilus germanica": 3160, "metasequoia glyptostroboides": 3170,
                 "ostrya carpinifolia": 3180, "parrotia persica": 3190, "parthenocissus quinquefolia": 3200,
                 "parthenocissus tricuspidata": 3210, "paulownia tomentosa": 3220, "philadelphus coronarius": 3230,
                 "picea abies": 3240, "picea abies 'inversa'": 3250, "picea asperata": 3260, "picea engelmanii": 3270,
                 "picea glauca": 3280, "picea glauca 'conica'": 3290, "picea omorika": 3300, "picea orientalis": 3310,
                 "picea polita": 3320, "picea pungens 'glauca'": 3330, "picea sitchensis": 3340, "pinus aristata": 3350,
                 "pinus armandii": 3360, "pinus cembra": 3370, "pinus contorta": 3380, "pinus heldreichii": 3390,
                 "pinus jeffreyi": 3400, "pinus koraiensis": 3410, "pinus leucodermis": 3420, "pinus mugo": 3430,
                 "pinus nigra": 3440, "pinus nigra var": 3450, "pinus parviflora": 3470, "pinus peuce": 3480,
                 "pinus ponderosa": 3490, "pinus strobus": 3500, "pinus sylvestris": 3510, "pinus thunbergii": 3520,
                 "pinus wallichiana": 3530, "platanus acerifolia": 3540, "platanus orientalis": 3550,
                 "platycladus orientalis": 3560, "populus alba": 3570, "populus nigra": 3580, "populus simonii": 3590,
                 "populus tremula": 3600, "populus x canadensis": 3610, "populus x canescens": 3620,
                 "prunus avium": 3630, "prunus cerasifera 'nigra'": 3640, "prunus domestica": 3650,
                 "prunus domestica ssp": 3660, "prunus dulcis": 3670, "prunus laurocerasus": 3680, "prúnus pádus": 3690,
                 "prunus padus": 3690, "prunus sargentii": 3700, "prunus serotina": 3710, "prunus serrulata": 3720,
                 "prunus spinosa": 3730, "prunus subhirtella": 3740, "pseudotsuga menziesii": 3750,
                 "ptelea trifoliata": 3760, "pterocarya fraxinifolia": 3770, "pterocarya stenoptera": 3780,
                 "pyracantha coccinea": 3790, "pýrus pyráster": 3800, "pyrus pyraster": 3800,
                 "quercus acutissima": 3810, "quercus cerris": 3820, "quercus coccinea": 3830,
                 "quercus frainetto": 3840, "quercus ilex": 3850, "quercus libani": 3860, "quercus palustris": 3870,
                 "quercus petraea": 3880, "quercus prinus": 3890, "quercus pubescens": 3900, "quercus robur": 3910,
                 "quercus rubra": 3920, "quercus suber": 3930, "quercus x hispanica 'lucombeana'": 3940,
                 "quercus x turneri": 3950, "rhamnus cathartica": 3960, "rhamnus imeretinus": 3970,
                 "rhodotypos scandens": 3980, "rhus hirta": 3990, "ribes aureum": 4000, "ribes sanguineum": 4010,
                 "robinia pseudoacacia": 4020, "rosa canina": 4030, "rosa spinosissima": 4040, "rubus fruticosus": 4050,
                 "salix alba": 4060, "salix alba 'tristis'": 4070, "salix aurita": 4080, "salix babylonica": 4090,
                 "salix caprea": 4100, "salix caprea 'kilmarnock'": 4110, "salix cinerea": 4120, "salix fragilis": 4130,
                 "salix matsudana 'tortuosa'": 4140, "salix viminalis": 4150, "sambucus nigra": 4160,
                 "sambucus racemosa": 4170, "sciadopitys verticillata": 4180, "sequoia sempervirens": 4190,
                 "sequoiadendron giganteum": 4200, "shepherdia argentea": 4210, "sophora japonica": 4220,
                 "sorbus aria": 4230, "sórbus aucupária": 4240, "sorbus aucuparia": 4240, "sorbus domestica": 4250,
                 "sorbus intermedia": 4260, "sorbus torminalis": 4270, "spiraea x billardii": 4280,
                 "spiraea x vanhouttei": 4290, "staphylea pinnata": 4300, "stranvaesia davidiana": 4310,
                 "symphoricarpos albus": 4320, "syringa reflexa": 4330, "syringa vulgaris": 4340,
                 "tamarix parviflora": 4350, "taxodium distichum": 4360, "taxus baccata": 4370,
                 "thuja occidentalis": 4380, "thuja plicata": 4390, "thujopsis dolabrata": 4400, "tília cordáta": 4410,
                 "tilia cordata": 4410, "tilia platyphyllos": 4420, "tilia tomentosa": 4430, "tsuga canadensis": 4440,
                 "ulex europaeus": 4450, "úlmus glábra": 4460, "ulmus glabra": 4460, "ulmus laevis": 4470,
                 "úlmus mínor": 4480, "ulmus minor": 4480, "ulmus pumila": 4490, "viburnum farreri": 4500,
                 "viburnum lantana": 4510, "viburnum lentago": 4520, "viburnum opulus": 4530,
                 "viburnum rhytidophyllum": 4540, "viburnum tinus": 4550, "viburnum x bodnantense": 4560,
                 "viscum album": 4570, "vitis coignetiae": 4580, "weigela florida": 4590, "wisteria sinensis": 4600,
                 "zelkova serrata": 4610, "actinidia lind": 4630, "aeschynanthus jack": 4640, "ageratum": 4650,
                 "agrostemma githago": 4660, "agrostis": 4670, "allium cepa": 4680, "allium fistulosum": 4690,
                 "allium porrum": 4700, "allium schoenoprasum": 4710, "aloe": 4720,
                 "alonsoa meridionalis ( f.) o. kuntze": 4730, "alopecurus pratensis": 4740, "alstroemeria": 4750,
                 "amaranthus blitoides s. watson": 4760, "amaranthus cruentus": 4770, "anigozanthos labil": 4780,
                 "anthriscus cerefolium ( ) hoffm.": 4790, "anthurium schott": 4800, "antirrhinum": 4810,
                 "apium graveolens": 4820, "arctium": 4830, "argyranthemum frutescens ( ) schultz bip.": 4840,
                 "arnica montana": 4850, "aronia medik.": 4860,
                 "arrhenatherum elatius ( ) p.beauv. ex j.s. et k.b. presl": 4870, "asparagus officinalis": 4880,
                 "aster": 4890, "aubrieta adans.": 4900, "avena sativa": 4910, "begonia x hiemalis fotsch": 4930,
                 "begonia x tuberhybrida voss": 4940, "begonia-semperflorens-hybriden": 4950,
                 "beta vulgaris   var. altissima döll": 4960, "beta vulgaris   var. altissima doll": 4960,
                 "beta vulgaris   var. conditiva alef.": 4970, "beta vulgaris   var. crassa mansf.": 4980,
                 "beta vulgaris   var. vulgaris": 4990, "bidens ferulifolia (jacq.) dc.": 5000,
                 "brachyscome cass.": 5010, "brassica juncea ( ) czernj. et cosson": 5020,
                 "brassica napus   (partim)": 5030, "brassica napus   var. napobrassica ( ) rchb.": 5050,
                 "brassica oleracea   convar. acephala (dc.) alef. var. gongylodes": 5060,
                 "brassica oleracea   convar. acephala (dc.) alef. var. medullosa thel  und var. viridis": 5070,
                 "brassica oleracea   convar. acephala (dc.) alef. var. sabellica": 5080,
                 "brassica oleracea   convar. botrytis ( ) alef. var. botrytis": 5090,
                 "brassica oleracea   convar. botrytis ( ) alef. var. cymosa duch.": 5100,
                 "brassica oleracea   convar. capitata ( ) alef. var. alba dc.": 5110,
                 "brassica oleracea   convar. capitata ( ) alef. var. rubra dc.": 5120,
                 "brassica oleracea   convar. capitata ( ) alef. var. sabauda": 5130,
                 "brassica oleracea   convar. oleracea var. gemmifera dc.": 5140, "brassica rapa   var. rapa": 5150,
                 "brassica rapa   var. silvestris (lam.) briggs": 5170, "bromus": 5190,
                 "brunnera macrophylla (adams) johnst.": 5200, "calceolaria": 5210, "calluna vulgaris ( ) hull": 5220,
                 "camelina sativa ( ) crantz": 5230, "cannabis sativa": 5240, "capsicum annuum": 5250, "carex": 5260,
                 "carthamus tinctorius": 5270, "celosia": 5280, "chamomilla recutita ( ) rauschert": 5290,
                 "cichorium endivia": 5300, "convallaria majalis": 5320, "coronilla varia": 5330, "corylus": 5340,
                 "crassula schmidtii regel": 5350, "cucumis sativus": 5360, "cucurbita": 5370, "cucurbita pepo": 5380,
                 "cuphea p. br.": 5390, "cydonia oblonga mil": 5400, "cynara cardunculus": 5410,
                 "cynara scolymus": 5420, "daboecia cantabrica (huds.) k. koch": 5430, "dactylis": 5440,
                 "dahlia cav.": 5450, "daucus carota": 5460, "dendranthema x grandiflorum (ramat.) kitam.": 5480,
                 "deschampsia cespitosa ( ) p. beauv.": 5490, "dianthus": 5500, "digitalis": 5510,
                 "dracocephalum moldavica": 5520, "echinodorus   c. rich. ex engelm.": 5530, "erica": 5540,
                 "euonymus fortunei (turcz.) hand.-mazz.": 5550, "euphorbia fulgens karw. ex klotzsch": 5560,
                 "euphorbia milii des mou  var. milii": 5570, "euphorbia pulcherrima willd. ex klotzsch": 5580,
                 "fagopyrum mil": 5590, "festuca arundinacea schreber": 5600, "festuca ovina   sensu lato": 5610,
                 "festuca pratensis hudson": 5620, "festuca rubra   sensu lato": 5630, "ficus benjamina": 5640,
                 "foeniculum vulgare mil": 5660, "forsythia vahl": 5680, "fragaria": 5690, "gazania-hybriden": 5710,
                 "gentiana": 5720, "ginkgo biloba": 5740, "glycine max ( ) merr.": 5750, "hebe comm. ex juss.": 5760,
                 "helianthus annuus": 5770, "helianthus tuberosus": 5780, "helichrysum italicum (roth) gussone": 5790,
                 "heliotropium arborescens": 5800, "hippophae": 5820, "hordeum vulgare   sensu lato": 5830,
                 "humulus lupulus": 5850, "hypericum androsaemum": 5870, "hypericum perforatum": 5880,
                 "hyssopus officinalis": 5890, "ilex": 5900, "impatiens": 5910, "impatiens walleriana hybriden": 5920,
                 "juglans-hybriden": 5930, "kalanchoe adans.": 5940, "lactuca sativa": 5950,
                 "leontopodium alpinum cass.": 5970, "leucanthemum x superbum (j.w.ingram) bergmans ex kent": 5980,
                 "lilium": 5990, "limonium mil": 6000, "linum usitatissimum": 6010, "lobelia": 6030,
                 "lolium   (partim)": 6040, "lolium multiflorum lam.": 6050, "lolium perenne": 6060,
                 "lolium x boucheanum kunth": 6070, "lonicera nitida wils.": 6080, "lotus corniculatus": 6090,
                 "lupinus luteus": 6100, "lupinus albus": 6110, "lupinus angustifolius": 6120,
                 "lupinus mutabilis": 6130, "lupinus nanus douglas": 6140,
                 "lycopersicon lycopersicum ( ) karsten ex farw.": 6150, "malus mil": 6160, "malva verticillata": 6190,
                 "medicago lupulina": 6200, "medicago sativa": 6210, "melissa officinalis": 6220, "nicotiana": 6230,
                 "ocimum basilicum": 6240, "onobrychis viciifolia scop.": 6250, "orchidaceae": 6260,
                 "origanum majorana": 6270, "origanum vulgare": 6280, "pelargonium l'hérit. ex ait.": 6290,
                 "pelargonium l'herit. ex ait.": 6290, "pelargonium-grandiflorum-hybriden": 6300,
                 "petroselinum crispum (miller) nyman ex a.w. hill": 6310, "petunia juss.": 6330,
                 "phacelia juss.": 6340, "phalaris arundinacea": 6350, "phaseolus coccineus": 6360,
                 "phaseolus vulgaris": 6370, "phleum": 6390, "physocarpus (cambess.) maxim.": 6400,
                 "picea a. dietr.": 6410, "pisum sativum   (partim)": 6430, "poa": 6470, "poa pratensis": 6480,
                 "prunus": 6500, "prunus avium ( )": 6520, "prunus cerasus": 6530, "prunus persica ( ) batsch": 6550,
                 "pyracantha m.j. roem.": 6570, "pyrus": 6580, "raphanobrassica": 6610,
                 "raphanus sativus   var. niger (miller) s. kerner": 6620,
                 "raphanus sativus   var. oleiformis pers.": 6630, "raphanus sativus   var. sativus": 6640,
                 "rehmannia libosch. ex fisch. et c. a. mey.": 6650, "rhododendron simsii planch.": 6670, "ribes": 6680,
                 "ribes nigrum": 6700, "ribes x nidigrolaria r. et a. bauer": 6710, "rosa": 6720, "rubus": 6730,
                 "saintpaulia h. wend": 6750, "sanvitalia lam.": 6770, "satureja hortensis": 6780,
                 "scorzonera hispanica": 6790, "secale": 6800, "silybum marianum ( ) gaertn.": 6820,
                 "sinapis alba": 6830, "sinningia nees": 6840, "solanum": 6850, "solanum tuberosum": 6860,
                 "spinacia oleracea": 6870, "streptocarpus lind": 6880, "sutera roth": 6890,
                 "symphoricarpos duham.": 6900, "syringa": 6910, "tagetes": 6920,
                 "tanacetum parthenium ( ) schultz bip.": 6930, "tilia": 6940, "trifolium alexandrinum": 6950,
                 "trifolium hybridum": 6960, "trifolium incarnatum": 6970, "trifolium pratense": 6980,
                 "trifolium repens": 6990, "trifolium resupinatum": 7000, "trisetum flavescens ( ) p. beauv.": 7010,
                 "triticum aestivum   emend. fiori et pao": 7020, "triticum durum desf.": 7040,
                 "triticum monococcum": 7050, "triticum spelta": 7060, "tulipa": 7070, "tussilago farfara": 7080,
                 "ulmus": 7090, "urtica": 7100, "vaccinium": 7110, "valeriana officinalis": 7120,
                 "valerianella locusta ( ) laterr.": 7130, "vallisneria": 7140, "vicia   (partim)": 7150,
                 "vicia faba   (partim)": 7160, "vicia sativa": 7180, "vinca minor": 7190, "vitex agnus-castus": 7200,
                 "vitis": 7210, "vitis vinifera": 7220, "vriesea splendens (brongn.) lem.": 7230,
                 "zantedeschia spreng.": 7240, "zea mays": 7250, "x festulolium": 7260, "x triticosecale wittm.": 7270,
                 "unknown": 9999}
        veg_column = self.choice_vegetation_col.GetStringSelection()

        self.GetParent().db.add_col("code", "INT")
        self.GetParent().db.commit()
        con = BasicConnection(self.__DbPath)
        for k in codes:
            con.update_value(self.__DbTreeTableName, "code", codes[k], veg_column, k, True)
        con.commit()
        self.EndModal(12347)

