import os
import csv
import sqlite3
from ast import literal_eval


class Database:
    def __init__(self):

        self.__DbFolderPath = ""  # Path to the folder where the database is stored
        self.create_default_database_path()
        self.__DbFilePath = self.__DbFolderPath + '\\ArbokaTransformerDB.sqlite'  # Path to database file

        if os.path.exists(self.__DbFilePath):
            self.delete_db_file()
        if not os.path.exists(self.__DbFolderPath):
            os.makedirs(self.__DbFolderPath)

        self.__DbConnection = None
        self.__DbCursor = None
        self.establish_db_connection()
        self.__DbTreeTableName = "trees"
        self.__lTableColmnNames = []

    # Creates Database Path
    def create_default_database_path(self):
        if 'TEMP' in os.environ:
            path = os.environ['TMP']
        elif 'TMP' in os.environ:
            path = os.environ['TEMP']
        else:
            path = '.'
        path = path + '\\ArbokaTransformer'
        self.__DbFolderPath = path

    # method to create database table from csv file
    def import_csv_file(self, filepath, sep=";"):
        with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
            filereader = csv.reader(csvfile, delimiter=sep)
            for idx, row in enumerate(filereader):
                if idx == 0:
                    # Extract table column names from first row of csv file, create database table with it
                    tableheaders = row
                    for idx2, col in enumerate(tableheaders):
                        coldata = ["'%s'" % col, self.get_csv_datatypes(filereader, csvfile, idx2), True]
                        self.__lTableColmnNames.append(coldata)
                    self.create_db_table()
                else:
                    # Insert data rows from csv file into database
                    self.populate_db_table(row)
        self.__DbConnection.commit()

    # method to automatically detect a columns data type.
    # number of rows to be consider when determining data type can be configured using inspection_limit variable
    # returns "INTEGER", "REAL" or "TEXT"
    def get_csv_datatypes(self, filereader, csvfile, col_index):
        inspection_limit = 50
        type_list = []

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
                    datatype = "INTEGER"
                elif isinstance(dat, float):
                    datatype = "REAL"
                else:
                    datatype = "TEXT"
            except:
                datatype = "TEXT"
            type_list.append(datatype)

        # reset position of cursor in csvfile to line 1, because cursor has been moved in this method
        # method: move cursor back to line 0 and go to next lin
        # seek(1) gives errors with encoding for some reason, therefore use this method
        csvfile.seek(0)
        csvfile.readline()

        # loop over all cell's data type predictions of one column to make one prediction for column in general
        for idx in range(0, len(type_list)-1, 1):
            if type_list[idx] == type_list[idx+1]:
                continue
            else:
                return "TEXT"
        return type_list[0]

    # creates the database table to store the csv in
    # method may be vulnerable to sql injections
    def create_db_table(self):
        for idx, col in enumerate(self.__lTableColmnNames):
            if idx == 0:
                self.__DbCursor.execute("CREATE TABLE %s(%s %s);" % (self.__DbTreeTableName, col[0], col[1]))
            else:
                self.__DbCursor.execute("ALTER TABLE %s ADD COLUMN %s %s" % (self.__DbTreeTableName, col[0], col[1]))

    # populates database table with values from csv file
    def populate_db_table(self, row):
        statement = 'INSERT INTO %s VALUES ('
        for _ in row:
            statement += "?, "
        statement = statement[:-2] + ");"
        self.__DbCursor.execute(statement % self.__DbTreeTableName, row)

    # returns the number of table columns
    def get_column_number(self):
        return len(self.__lTableColmnNames)

    # returns the names of all table columns
    def get_column_names(self):
        column_list = []
        for row in self.__lTableColmnNames:
            if row[2]:
                column_list.append(row[0][1:-1])
        return column_list

    # Prepares Databse for new file to be opened and imported:
    # Drops table and resets list with table column names
    def reset_database_table(self):
        self.__DbCursor.execute("DROP TABLE IF EXISTS %s" % self.__DbTreeTableName)
        self.__lTableColmnNames = []

    # establishes database_connection: Creates Database File, Connection and Cursor
    def establish_db_connection(self):
        self.__DbConnection = sqlite3.connect(self.__DbFilePath)
        self.__DbCursor = self.__DbConnection.cursor()

    # closes database connection
    def close_db_connection(self):
        if self.__DbConnection is not None:
            self.__DbConnection.close()

    # deletes database folder
    def delete_db_folder(self):
        if os.path.exists(self.__DbFolderPath):
            os.rmdir(self.__DbFolderPath)

    # deletes database file
    def delete_db_file(self):
        if os.path.exists(self.__DbFilePath):
            os.remove(self.__DbFilePath)

    # Deletes created database file and folder
    def delete_db(self):
        self.delete_db_file()
        self.delete_db_folder()

    # returns the number of rows in database tables
    def get_number_of_tablerecords(self):
        try:
            self.__DbCursor.execute("SELECT count(*) FROM %s" % self.__DbTreeTableName)
            res = self.__DbCursor.fetchall()
            return res[0][0]
        except sqlite3.OperationalError:
            return 0

    # fetches and returns table data from database
    def get_data(self):
        # generates sql statement
        statement = "SELECT "
        for colname in self.get_column_names():
            statement += '"%s", ' % colname
        statement = statement[:-2]
        statement += " FROM %s;" % self.__DbTreeTableName

        # executes statement and fetches data
        self.__DbCursor.execute(statement)
        result = self.__DbCursor.fetchall()
        return result


if __name__ == "__main__":
    db = Database()
    db.import_csv_file(filepath=".\..\data\ArbokatBaumdaten_test.csv")
    db.close_db_connection()
    db.delete_db()
