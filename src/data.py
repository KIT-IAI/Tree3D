import os
import csv
import sqlite3
from ast import literal_eval
import xml.etree.ElementTree as ET
import xml.sax

import requests
from pyproj import CRS, Transformer

import OSM_SAXHandler

# custom exception: Too many items in a line:More than in table headers (used in CSV only)
class TooManyItemsException(Exception):
    pass


# custom exception: Less many items in a line:More than in table headers (used in CSV only)
class NotEnoughItemsException(Exception):
    pass


class Database:
    def __init__(self):

        self._DbFolderPath = ""  # Path to the folder where the database is stored
        self.create_default_database_path()
        self._DbFilePath = self.generate_filepath('\\tree3d_db.sqlite')

        # Delete database file and folder
        if os.path.exists(self._DbFilePath):
            self.delete_db_file()
        if not os.path.exists(self._DbFolderPath):
            os.makedirs(self._DbFolderPath)

        self._SpatiaLiteLoaded = [False, ""]  # String gives error message if False, indicates if spatialite was loaded
        self._DbConnection = None
        self._DbCursor = None
        self.establish_db_connection()  # connect to database

        self._DbTreeTableName = "trees"  # name of table in database, into which the csv file is imported
        self._lTableColmnNames = []  # list of all table column names

        self._SQLGetAllDataStatement = ""  # SQL Statement to get all data

        self._CreateTwoColID = False  # variable to determine weather a tree id should be created
        self._CreateTwoColIDColumns = []  # list storing the list-indexes of columns, from which id should be created
        self._DataInspectionLimit = 0  # Limit of data inspection before input

        self._CreateRowid = False  # variable to determine weather sqlite rowid should be used

        self._ContainsGeom = False  # variable to indicate, if geom object has been generated

    # Creates Database Path
    # Database is stored in temporary folder by default
    # Path to temporary folder is read from environment variables TMP or TEMP
    # if these environment variables dont exists, database is stored in working directory
    def create_default_database_path(self):
        # find temporary folder from system variables
        if 'TEMP' in os.environ:
            path = os.environ['TMP']
        elif 'TMP' in os.environ:
            path = os.environ['TEMP']
        else:
            # use current directory, if variable was not found
            path = '.'
        path = path + '\\tree3d_data'
        self._DbFolderPath = path

    # returns path of database file
    def get_db_filepath(self):
        return self._DbFilePath

    # creates the database table to store the csv in
    # method may be vulnerable to sql injections
    def create_db_table(self):
        for idx, col in enumerate(self._lTableColmnNames):
            if idx == 0:
                self._DbCursor.execute('CREATE TABLE %s(%s %s);' % (self._DbTreeTableName, col[0], col[1]))
            else:
                self._DbCursor.execute('ALTER TABLE %s ADD COLUMN %s %s' % (self._DbTreeTableName, col[0], col[1]))
        self._DbConnection.commit()

    # combines db folder path with db file name
    def generate_filepath(self, filename):
        path = self._DbFolderPath + filename
        return path

    # returns name of tree table in database
    def get_tree_table_name(self):
        return self._DbTreeTableName

    # returns the number of table columns
    def get_number_of_columns(self):
        return len(self._lTableColmnNames)

    # returns the names of all table columns
    def get_column_names(self):
        column_list = []
        for row in self._lTableColmnNames:
            if row[2]:
                column_list.append(row[0][1:-1])
        return column_list

    # return all column names that have numeric data type (INT, REAL)
    def get_column_names_numeric(self):
        column_list = []
        for row in self._lTableColmnNames:
            if row[1] == "INTEGER" or row[1] == "REAL":
                column_list.append(row[0][1:-1])
        return column_list

    # returns all column names that have GEOM data type
    def get_column_names_geom(self):
        column_list = []
        for row in self._lTableColmnNames:
            if row[1] == "GEOM":
                column_list.append(row[0][1:-1])
        return column_list

    # returns data types of all columns
    def get_column_datatypes(self):
        type_list = []
        for row in self._lTableColmnNames:
            type_list.append(row[1])
        return type_list

    # Prepares Databse for new file to be opened and imported:
    # Drops table and resets list with table column names
    def reset_database_table(self):
        self._DbCursor.execute("DROP TABLE IF EXISTS %s" % self._DbTreeTableName)
        self._lTableColmnNames = []
        self._DbConnection.commit()

    # establishes database_connection: Creates Database File, Connection and Cursor
    def establish_db_connection(self):
        self._DbConnection = sqlite3.connect(self._DbFilePath)
        self._DbCursor = self._DbConnection.cursor()
        self._DbConnection.enable_load_extension(True)
        try:
            self._DbConnection.execute('SELECT load_extension("mod_spatialite")')
            self._DbConnection.execute('SELECT InitSpatialMetaData(1);')
            self._DbConnection.commit()
            self._SpatiaLiteLoaded[0] = True
        except sqlite3.OperationalError as e:
            self._SpatiaLiteLoaded[1] = str(e)

    # closes database connection
    def close_db_connection(self):
        if self._DbConnection is not None:
            self._DbConnection.close()

    # deletes database folder. If folder isnt empty: catch exception and do nothing
    def delete_db_folder(self):
        try:
            if os.path.exists(self._DbFolderPath):
                os.rmdir(self._DbFolderPath)
        except OSError:
            pass

    # deletes database file
    def delete_db_file(self):
        i = 1
        while os.path.exists(self._DbFilePath):
            try:
                os.remove(self._DbFilePath)
            except PermissionError:
                self._DbFilePath = self.generate_filepath('\\tree3d_db%s.sqlite' % i)
                i += 1

    # Deletes created database file and folder
    def delete_db(self):
        self.delete_db_file()
        self.delete_db_folder()

    # returns status of spatialite: False, if it could not be loaded
    def get_spatialite_status(self):
        return self._SpatiaLiteLoaded

    # returns the number of rows in database tables
    def get_number_of_tablerecords(self):
        try:
            self._DbCursor.execute("SELECT count(*) FROM %s" % self._DbTreeTableName)
            res = self._DbCursor.fetchall()
            return res[0][0]
        except sqlite3.OperationalError:
            return 0

    # generates SQL Statement to fetch all Data from Database table
    # Only Select, no sorting, no conditions etc
    def generate_sql_statement(self):
        statement = "SELECT "
        for colname in self.get_column_names():
            if colname == "geom":
                statement += 'AsText("geom"), '
            else:
                statement += '"%s", ' % colname
        statement = statement[:-2]
        statement += " FROM %s;" % self._DbTreeTableName
        self._SQLGetAllDataStatement = statement

    # fetches and returns table data from database
    def get_data(self):
        # executes statement to fetch all data from database table
        self._DbCursor.execute(self._SQLGetAllDataStatement)
        return self._DbCursor

    # appends sql statement with a where condition to filter data
    def get_data_with_condition(self, wherestatement):
        statement = self._SQLGetAllDataStatement[:-1] + " " + wherestatement + ";"
        self._DbCursor.execute(statement)
        return self._DbCursor

    # fetch data from database with sorting
    def get_data_with_sorting(self, sortstatement):
        statement = self._SQLGetAllDataStatement[:-1] + " " + sortstatement + ";"
        self._DbCursor.execute(statement)
        return self._DbCursor

    # alters sql statement to perform SELECT DISTINCT, includes WHERE condition
    def get_data_with_condition_distinct(self, wherestatement):
        statement = self._SQLGetAllDataStatement[0:7] + "DISTINCT " + self._SQLGetAllDataStatement[7:-1]
        statement += " " + wherestatement + ";"
        self._DbCursor.execute(statement)
        return self._DbCursor

    # performs a SELECT DISTINCT with columns written in collist
    def get_data_by_collist_distinct(self, collist):
        # generates sql statement
        statement = "SELECT DISTINCT "
        for colname in collist:
            statement += '"%s", ' % colname
        statement = statement[:-2]
        statement += " FROM %s;" % self._DbTreeTableName

        # executes statement and fetches data
        self._DbCursor.execute(statement)
        return self._DbCursor

    # selects data from database from specific columns
    # collist variable has column names
    def get_data_by_collist(self, collist):
        # generates sql statement
        statement = "SELECT "
        for colname in collist:
            statement += '"%s", ' % colname
        statement = statement[:-2]
        statement += " FROM %s;" % self._DbTreeTableName

        # executes statement and fetches data
        self._DbCursor.execute(statement)
        return self._DbCursor

    # get data in a form so that it can find duplicates based on geometry
    def get_data_for_duplicatecheck_geom(self, collist):
        # generate sql statement
        statement = "SELECT "
        statement += 't1."%s", t1."%s", t1."%s", ' % (collist[0], collist[1], collist[2])
        statement += 't2."%s", t2."%s", t2."%s" ' % (collist[0], collist[1], collist[2])
        statement += "FROM %s as t1, %s as t2 " % (self._DbTreeTableName, self._DbTreeTableName)
        statement += "WHERE t2.rowid > t1.rowid;"
        self._DbCursor.execute(statement)
        return self._DbCursor

    # counts number of rows with the same value in row
    def count_unique_values_in_col(self, colname):
        # generates sql statement
        statement = 'SELECT "%s", count("%s") FROM %s GROUP BY "%s";'\
                    % (colname, colname, self._DbTreeTableName, colname)
        self._DbCursor.execute(statement)
        return self._DbCursor

    # returns Value, weather index should be created
    def get_create_id(self):
        return self._CreateTwoColID

    # sets variable whether combined id should be created True or False
    def set_create_id(self, value):
        self._CreateTwoColID = value

    # sets list of columns to create index from
    def set_id_columns(self, value):
        self._CreateTwoColIDColumns = value

    # sets variable weather rowid should be used
    def set_use_rowid(self, value):
        self._CreateRowid = value

    # returns True if rowid is used
    def get_use_rowid(self):
        return self._CreateRowid

    # Add a point geometry column
    def add_geom_col(self, epsg):
        statement = 'SELECT AddGeometryColumn("%s", "geom" , %s, "POINT", "XY");' % (self._DbTreeTableName, epsg)
        self._DbCursor.execute(statement)
        self.add_col_to_collist("geom", "GEOM")
        self.generate_sql_statement()

    # method to generate a spatial Index for a specific column
    def add_spatial_index(self, colname):
        self._DbCursor.execute("SELECT CreateSpatialIndex('elevation', '%s');" % colname)

    # method to add a column to the tree database table
    def add_col(self, name, datatype):
        # find out if a column with this name already exists
        self._DbCursor.execute("pragma table_info('%s')" % self._DbTreeTableName)
        for row in self._DbCursor:
            if row[1] == name:
                # if a column with this name already exists, overwrite it with null values
                self.update_value(name, "null")
                self.commit()
                return
        statement = "ALTER TABLE %s ADD COLUMN '%s' %s;" % (self._DbTreeTableName, name, datatype)
        self._DbCursor.execute(statement)
        self.add_col_to_collist(name, datatype)
        self.generate_sql_statement()

    # method to add a column to the program's internal list of table columns
    def add_col_to_collist(self, name, datatype):
        if name not in self.get_column_names():
            self._lTableColmnNames.append(["'%s'" % name, datatype, True])

    # updates a value in a database column
    # cannot update with string values yet!!!
    def update_value(self, insert_col, insert_val, where_col=None, where_val=None):
        insert_cursor = self._DbConnection.cursor()
        statement = 'UPDATE %s SET "%s" = %s' % (self._DbTreeTableName, insert_col, insert_val)
        if where_col is not None and where_val is not None:
            if type(where_val) == str:
                statement += ' WHERE "%s" = "%s"' % (where_col, where_val)
            else:
                statement += ' WHERE "%s" = %s' % (where_col, where_val)
        statement += ';'
        insert_cursor.execute(statement)

    # removes a column from column list
    def remove_col_from_collist(self, colname):
        for index, row in enumerate(self._lTableColmnNames):
            if row[1] == colname:
                del self._lTableColmnNames[index]
                break

    # commits changes in database
    def commit(self):
        self._DbConnection.commit()

    # roll back database to last commit
    def rollback(self):
        self._DbConnection.rollback()

    # sets data inspection limit:
    # number of rows that will be analyzed before input to find out data type
    def set_data_inspection_limit(self, value):
        self._DataInspectionLimit = value

    # set geom status
    def set_contains_geom(self, value):
        self._ContainsGeom = value

    # returns, if geom data type column is present
    def get_contains_geom(self):
        return self._ContainsGeom


class DatabaseFromCsv(Database):
    def __init__(self):
        super().__init__()
        self.__seperator = ""  # seperator in csv file
        self.__FileEncoding = ""  # file encoding of csv file
        self.__StartLine = 0  # line at which data starts (in case there are empty lines in the beginning)

    # method to create database table from csv file
    def import_csv_file(self, filepath):
        headers_found = False
        with open(filepath, newline='', encoding=self.__FileEncoding) as csvfile:
            filereader = csv.reader(csvfile, delimiter=self.__seperator)
            for idx, row in enumerate(filereader):
                if not row and not headers_found:
                    self.__StartLine += 1
                    continue

                if not row and headers_found:
                    continue

                if idx == self.__StartLine:
                    headers_found = True
                    # add column for unique tree ID to data model
                    if self._CreateTwoColID:
                        self._lTableColmnNames.append(["'IAI_TreeID'", "TEXT", True])

                    # Extract table column names from first row of csv file, create database table with it
                    tableheaders = row
                    col_num = len(tableheaders)
                    for idx2, col in enumerate(tableheaders):
                        try:
                            coldata = ["'%s'" % col, self.get_csv_datatypes(filereader, csvfile, idx2, col_num), True]
                            self._lTableColmnNames.append(coldata)
                        except NotEnoughItemsException as e:
                            raise NotEnoughItemsException("Line %s" % (idx + int(str(e))+2))
                        except TooManyItemsException as e:
                            raise TooManyItemsException("Line %s" % (idx + int(str(e))+2))

                    self.create_db_table()
                else:
                    # Insert data rows from csv file into database, raise exceptions if row is under- or overpopulated
                    try:
                        self.populate_db_table(row)
                    except NotEnoughItemsException:
                        raise NotEnoughItemsException(idx+1)
                    except TooManyItemsException:
                        raise TooManyItemsException(idx+1)
        if self._CreateTwoColID:
            self._DbCursor.execute("CREATE INDEX iaitreeidindex on trees(IAI_TreeID);")
        self._DbConnection.commit()
        if self._CreateRowid:
            self._lTableColmnNames.insert(0, ["'ROWID'", "TEXT", True])
        self.generate_sql_statement()
        return True

    # method to insert a row into the database
    def populate_db_table(self, row):
        if not self._CreateTwoColID and len(row) < self.get_number_of_columns():
            raise NotEnoughItemsException

        if self._CreateTwoColID and len(row) < self.get_number_of_columns()-1:
            raise NotEnoughItemsException

        if len(row) > self.get_number_of_columns():
            raise TooManyItemsException
        insert_row = []
        if self._CreateTwoColID:
            row.insert(0, "%s_%s" % (row[self._CreateTwoColIDColumns[0]], row[self._CreateTwoColIDColumns[1]]))
        statement = 'INSERT INTO %s VALUES ('
        for _ in row:
            statement += "?, "
        statement = statement[:-2] + ");"

        for idx, element in enumerate(row):
            if self._lTableColmnNames[idx][1] == "INTEGER" and element != "":
                insert_row.append(int(element))
            elif self._lTableColmnNames[idx][1] == "REAL" and element != "":
                insert_row.append(float(element.replace(",", ".")))
            elif element != "":
                insert_row.append(element)
            else:
                insert_row.append(None)
        self._DbCursor.execute(statement % self._DbTreeTableName, insert_row)

    # method to automatically detect the data type of a column in the opened csv file.
    # number of rows to be consider when det4000*12
    # ermining data type can be configured using inspection_limit variable
    # returns string "INTEGER", "REAL" or "TEXT", (data types used in sqlite databases)
    def get_csv_datatypes(self, filereader, csvfile, col_index, number_of_cols):
        inspection_limit = self._DataInspectionLimit

        int_type_in_list = False
        real_type_in_list = False
        text_type_in_list = False

        # make data type prediction for each cell of one column
        for index2, row in enumerate(filereader):

            # break loop if row inspection limit is reached
            if index2 > inspection_limit:
                break

            if not row:
                continue

            # if there is no value for an attribute in a row: ignore this row to prevent false data type predictions
            if row[col_index] == "":
                continue

            if not self._CreateTwoColID and len(row) < number_of_cols:
                raise NotEnoughItemsException(index2)

            if self._CreateTwoColID and len(row) < number_of_cols-1:
                raise NotEnoughItemsException(index2)

            if len(row) > number_of_cols:
                raise TooManyItemsException(index2)

            try:
                dat = literal_eval(row[col_index].replace(",", "."))
                if isinstance(dat, int):
                    int_type_in_list = True
                elif isinstance(dat, float):
                    real_type_in_list = True
                else:
                    text_type_in_list = True
            except:
                text_type_in_list = True

        # reset position of cursor in csvfile to line 1, because cursor has been moved in this method
        # method: move cursor back to line 0 and go to next lin
        # seek(1) gives errors with encoding for some reason, therefore use this method
        csvfile.seek(0)
        counter = 0
        while counter <= self.__StartLine:
            csvfile.readline()
            counter += 1

        if int_type_in_list and not real_type_in_list and not text_type_in_list:
            data_type = "INTEGER"
        elif real_type_in_list and not text_type_in_list:
            data_type = "REAL"
        else:
            data_type = "TEXT"

        return data_type

    # sets csv seperator
    def set_seperator(self, sep):
        self.__seperator = sep

    # sets file encoding for csv file
    def set_file_encoding(self, codec):
        self.__FileEncoding = codec


class DatabaseFromXml(Database):
    def __init__(self):
        super().__init__()
        self.__XmlTree = None
        self.__RootNode = None  # Root node of xml tree
        self.__ns = {}  # xml namespaces: associates prefix with full qualified name

    def import_xml_file(self, filepath, attribute_path, geom_path, ignorestring, tree):
        self.__XmlTree = tree
        self.__RootNode = self.__XmlTree.getroot()

        # Fill dictionary of namespaces with {prefix: namespace}
        self.__ns = dict([node for _, node in ET.iterparse(filepath, events=['start-ns'])])

        # Create list with elements to ignore from string.
        # Format list: Remove leading and tailing whitespaces
        ignorelist = ignorestring.split(";")
        for idx, element in enumerate(ignorelist):
            ignorelist[idx] = element.strip()

            # add column for unique tree ID to data model
            if self._CreateTwoColID:
                self._lTableColmnNames.append(["'IAI_TreeID'", "TEXT", True])

        # Inspect data: Find Columns to add to database table
        # Find data type of each column
        inspected_cols = []
        for element in self.__RootNode.findall(attribute_path, self.__ns):
            for subelement in element:
                tag = subelement.tag
                tag_no_pref = tag.split("}")[1]
                if (tag_no_pref not in ignorelist) and (tag_no_pref not in inspected_cols):
                    datatype = self.get_xml_datatype(attribute_path+"/"+tag)
                    inspected_cols.append(tag_no_pref)
                    self._lTableColmnNames.append(["'%s'" % tag_no_pref, datatype, True])

        # Add geometry columns to Table columns
        if geom_path != "":
            self._lTableColmnNames.append(["'X_VALUE'", "REAL", True])
            self._lTableColmnNames.append(["'Y_VALUE'", "REAL", True])

        self.create_db_table()
        self._DbConnection.commit()

        # create row (insert_row) that will be inserted into database
        # create list of columns, to which the inserted data refers
        for element in self.__RootNode.findall(attribute_path, self.__ns):
            col_list = []
            insert_row = []
            if self._CreateTwoColID:
                col_list.append("'IAI_TreeID'")
            for subelement in element:
                if subelement.tag.split("}")[1] not in ignorelist:
                    col_list.append("'%s'" % subelement.tag.split("}")[1])
                    insert_row.append(subelement.text)
                if geom_path != "":
                    path = geom_path.split("/", 2)[2]
                    for geom in subelement.findall(path, self.__ns):
                        coords = geom.text.split(" ")
                        col_list.append("'X_VALUE'")
                        insert_row.append(str(coords[0]))
                        col_list.append("'Y_VALUE'")
                        insert_row.append(str(coords[1]))

            # insert row into specified columns
            self.populate_db_table(insert_row, col_list)

        if self._CreateTwoColID:
            self._DbCursor.execute("CREATE INDEX iaitreeidindex on trees(IAI_TreeID);")
        self._DbConnection.commit()
        if self._CreateRowid:
            self._lTableColmnNames.insert(0, ["'ROWID'", "TEXT", True])
        self.generate_sql_statement()

    # method to automatically detect the data type of an xml attribute
    # number of rows to be consider when determining data type can be configured using inspection_limit variable
    # returns string "INTEGER", "REAL" or "TEXT", (data types used in sqlite databases)
    def get_xml_datatype(self, attribute_path):
        inspection_limit = self._DataInspectionLimit

        int_type_in_list = False
        real_type_in_list = False
        text_type_in_list = False

        for index, element in enumerate(self.__RootNode.findall(attribute_path, self.__ns)):
            # stop data type inspection once the inspection limit is hit
            if index > inspection_limit:
                break

            # if there is no value for an attribute in a row: ignore this row to prevent false data type predictions
            if element.text is None:
                continue

            try:
                dat = literal_eval(element.text.replace(",", "."))
                if isinstance(dat, int):
                    int_type_in_list = True
                elif isinstance(dat, float):
                    real_type_in_list = True
                else:
                    text_type_in_list = True
            except:
                text_type_in_list = True

        if int_type_in_list and not real_type_in_list and not text_type_in_list:
            data_type = "INTEGER"
        elif real_type_in_list and not text_type_in_list:
            data_type = "REAL"
        else:
            data_type = "TEXT"

        return data_type

    # method to add data row to database
    def populate_db_table(self, row, cols):
        col_string = "("
        insert_row = []
        col_type_dict = {}

        # create dictionary and their datatypes {col_name: datatype}
        for col in self._lTableColmnNames:
            col_type_dict["%s" % col[0]] = col[1]

        # create col-string: String of columns that will be used in sql insert statement
        for col in cols:
            col_string += "%s, " % col
        col_string = col_string[:-2] + ") "

        # create sql insert statement
        if self._CreateTwoColID:
            row.insert(0, "%s_%s" % (row[self._CreateTwoColIDColumns[0]], row[self._CreateTwoColIDColumns[1]]))
        statement = 'INSERT INTO %s ' + col_string + 'VALUES ('
        for _ in row:
            statement += "?, "
        statement = statement[:-2] + ");"

        # add values in their correct data types to input_row
        for idx, element in enumerate(row):
            if col_type_dict[cols[idx]] == "INTEGER" and element is not None:
                insert_row.append(int(element))
            elif col_type_dict[cols[idx]] == "REAL" and element is not None:
                insert_row.append(float(element.replace(",", ".")))
            else:
                insert_row.append(element)

        # insert row into database
        self._DbCursor.execute(statement % self._DbTreeTableName, insert_row)

    # method to validate a xpath
    # start element for validation is root node
    def validate_xpath(self, xpath):
        if self.__RootNode.findall(xpath, self.__ns):
            return True
        else:
            return False


class DatabaseFromOSM(Database):
    def __init__(self):
        Database.__init__(self)

        self.__query_bbox = []
        self.__epsg = None

    # method to set query bounding box coordinates
    # coordinates must be WGS84 geographic coordinates (EPSG:4326)
    def set_query_bbox(self, lower_bound, left_bound, upper_bound, right_bound, epsg):
        self.__epsg = epsg

        # convert bounding box coordinates to WGS84, if they are not yet
        if self.__epsg != 4326:
            crs_in = CRS.from_epsg(self.__epsg)
            crs_out = CRS.from_epsg(4326)
            transformer = Transformer.from_crs(crs_in, crs_out)
            lower_bound_new, left_bound_new = transformer.transform(left_bound, lower_bound)
            upper_bound_new, right_bound_new = transformer.transform(right_bound, upper_bound)
            bbox = [lower_bound_new, left_bound_new, upper_bound_new, right_bound_new]
        else:
            bbox = [lower_bound, left_bound, upper_bound, right_bound]

        self.__query_bbox.extend(bbox)

    def import_osm_trees(self):
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_ql_statement = "node(%s, %s, %s, %s)[natural=tree];out;" % (self.__query_bbox[0], self.__query_bbox[1],
                                                                             self.__query_bbox[2], self.__query_bbox[3])
        request_url = overpass_url + "?data=" + overpass_ql_statement

        r = requests.get(request_url, timeout=(9.05, 27))

        request_text = r.text

        osmhandler = OSM_SAXHandler.OSMHandlerInspector()
        xml.sax.parseString(request_text, osmhandler)

        crs_in = CRS.from_epsg(4326)

        # specify output coordinate system
        if self.__epsg != 4326:
            output_epsg = self.__epsg
            crs_out = CRS.from_epsg(output_epsg)
        else:
            output_epsg = get_utm_epsg(self.__query_bbox[1])  # figure out utm epsg code
            crs_out = CRS.from_epsg(output_epsg)
        transformer = Transformer.from_crs(crs_in, crs_out)

        self._lTableColmnNames.append(["'OSM_ID'", "INT", True])
        self._lTableColmnNames.append(["'X_VALUE_%s'" % output_epsg, "REAL", True])
        self._lTableColmnNames.append(["'Y_VALUE_%s'" % output_epsg, "REAL", True])
        self._lTableColmnNames.extend(osmhandler.get_columns())

        self.create_db_table()
        self._DbConnection.commit()

        tree_list = osmhandler.get_tree_list()

        # import trees in database:
        for tree in tree_list:
            columns = "("
            values = "("
            value_list = []

            x_val = tree["X_VALUE"]
            y_val = tree["Y_VALUE"]
            x_val_new, y_val_new = transformer.transform(y_val, x_val)
            tree["X_VALUE_%s" % output_epsg] = x_val_new
            tree["Y_VALUE_%s" % output_epsg] = y_val_new

            # loop over dict and create entry for tree in database
            for key in tree:

                # skip dict entries X_VALUE and Y_VALUE since they are not transformed
                # X_VALUE_epsg is used instead
                if key == "X_VALUE" or key == "Y_VALUE":
                    continue

                columns += '"%s", ' % key
                values += "?, "
                value_list.append(tree[key])
            columns = columns[:-2] + ") "
            values = values[:-2] + ")"

            statement = "INSERT INTO %s " + columns + "VALUES " + values + ";"
            self._DbCursor.execute(statement % self._DbTreeTableName, value_list)

        self._DbCursor.execute('''CREATE INDEX iaitreeidindex on trees("'OSM_ID'");''')
        self._DbConnection.commit()

        self.generate_sql_statement()


# Look up UTM zone for longitude
# Implemented european zones only so far
# returns epsg code of corresponding utm zone code
def get_utm_epsg(long):
    epsg = 25800
    add = 0
    if -18 <= long < -12:
        add = 28
    if -12 <= long < -6:
        add = 29
    if -6 <= long < 0:
        add = 30
    if 0 <= long < 6:
        add = 31
    if 6 <= long < 12:
        add = 32
    if 12 <= long < 18:
        add = 33
    if 18 <= long < 24:
        add = 34
    if 24 <= long < 30:
        add = 35
    if 30 <= long <= 36:
        add = 36
    return epsg+add
