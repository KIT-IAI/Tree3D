import os
import csv
import sqlite3
from ast import literal_eval
import xml.etree.ElementTree as ET


class Database:
    def __init__(self):

        self._DbFolderPath = ""  # Path to the folder where the database is stored
        self.create_default_database_path()
        self._DbFilePath = self._DbFolderPath + '\\ArbokaTransformerDB.sqlite'  # Path to database file

        if os.path.exists(self._DbFilePath):
            self.delete_db_file()
        if not os.path.exists(self._DbFolderPath):
            os.makedirs(self._DbFolderPath)

        self._DbConnection = None
        self._DbCursor = None
        self.establish_db_connection()
        self._DbTreeTableName = "trees"  # name of table in database, into which the csv file is imported
        self._lTableColmnNames = []  # list of all table column names

        self._SQLGetAllDataStatement = ""  # SQL Statement to get all data

        self._CreateTwoColID = False  # variable to determine weather a tree id should be created
        self._CreateTwoColIDColumns = []  # list storing the list-indexes of columns, from which id should be created
        self._DataInspectionLimit = 0  # Limit of data inspection before input

    # Creates Database Path
    # Database is stored in temporary folder by default
    # Path to temporary folder is read from environment variables TMP or TEMP
    # if these environment variables dont exists, database is stored in working directory
    def create_default_database_path(self):
        if 'TEMP' in os.environ:
            path = os.environ['TMP']
        elif 'TMP' in os.environ:
            path = os.environ['TEMP']
        else:
            path = '.'
        path = path + '\\ArbokaTransformer'
        self._DbFolderPath = path

    # creates the database table to store the csv in
    # method may be vulnerable to sql injections
    def create_db_table(self):
        for idx, col in enumerate(self._lTableColmnNames):
            if idx == 0:
                self._DbCursor.execute("CREATE TABLE %s(%s %s);" % (self._DbTreeTableName, col[0], col[1]))
            else:
                self._DbCursor.execute("ALTER TABLE %s ADD COLUMN %s %s" % (self._DbTreeTableName, col[0], col[1]))
        self._DbConnection.commit()

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

    # closes database connection
    def close_db_connection(self):
        if self._DbConnection is not None:
            self._DbConnection.close()

    # deletes database folder
    def delete_db_folder(self):
        if os.path.exists(self._DbFolderPath):
            os.rmdir(self._DbFolderPath)

    # deletes database file
    def delete_db_file(self):
        if os.path.exists(self._DbFilePath):
            os.remove(self._DbFilePath)

    # Deletes created database file and folder
    def delete_db(self):
        self.delete_db_file()
        self.delete_db_folder()

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

    # counts number of rows with the same value in row
    def count_unique_values_in_col(self, colname):
        # generates sql statement
        statement = 'SELECT "%s", count("%s") FROM %s GROUP BY "%s";' % (colname, colname, self._DbTreeTableName, colname)
        self._DbCursor.execute(statement)
        return self._DbCursor

    # returns Value, weather index should be created
    def get_create_id(self):
        return self._CreateTwoColID

    # sets variable whether index should be created True or False
    def set_create_id(self, value):
        self._CreateTwoColID = value

    # sets list of columns to create index from
    def set_id_columns(self, value):
        self._CreateTwoColIDColumns = value

    # sets data inspection limit:
    # number of rows that will be analyzed before input to find out data type
    def set_data_inspection_limit(self, value):
        self._DataInspectionLimit = value


class DatabaseFromCsv(Database):
    def __init__(self):
        super().__init__()
        self.__seperator = ""  # seperator in csv file
        self.__FileEncoding = ""  # file encoding of csv file
        self.__StartLine = 0  # line at which data starts (in case there are empty lines in the beginning)

    # method to create database table from csv file
    def import_csv_file(self, filepath):
        with open(filepath, newline='', encoding=self.__FileEncoding) as csvfile:
            filereader = csv.reader(csvfile, delimiter=self.__seperator)
            for idx, row in enumerate(filereader):
                if not row:
                    self.__StartLine += 1
                    continue
                if idx == self.__StartLine:
                    # add column for unique tree ID to data model
                    if self._CreateTwoColID:
                        self._lTableColmnNames.append(["'IAI_TreeID'", "TEXT", True])

                    # Extract table column names from first row of csv file, create database table with it
                    tableheaders = row
                    for idx2, col in enumerate(tableheaders):
                        coldata = ["'%s'" % col, self.get_csv_datatypes(filereader, csvfile, idx2), True]
                        self._lTableColmnNames.append(coldata)
                    self.create_db_table()
                else:
                    # Insert data rows from csv file into database
                    self.populate_db_table(row)
        if self._CreateTwoColID:
            self._DbCursor.execute("CREATE INDEX iaitreeidindex on trees(IAI_TreeID);")
        self._DbConnection.commit()
        self.generate_sql_statement()
        return True

    # method to insert a row into the database
    def populate_db_table(self, row):
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
    def get_csv_datatypes(self, filereader, csvfile, col_index):
        inspection_limit = self._DataInspectionLimit

        int_type_in_list = False
        real_type_in_list = False
        text_type_in_list = False

        # make data type prediction for each cell of one column
        for index2, row in enumerate(filereader):

            # break loop if row inspection limit is reached
            if index2 > inspection_limit:
                break

            # if there is no value for an attribute in a row: ignore this row to prevent false data type predictions
            if row[col_index] == "":
                continue
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


if __name__ == "__main__":
    db = DatabaseFromCsv()
    db.import_csv_file(filepath=".\..\data\ArbokatBaumdaten_komplett.csv")
    db.close_db_connection()
    # db.delete_db()
