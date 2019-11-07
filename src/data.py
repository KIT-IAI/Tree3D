import os
import csv
import sqlite3


class Database:
    def __init__(self):

        self.__DbFolderPath = ""  # Path to the folder where the database is stored
        self.create_default_database_path()
        self.__DbFilePath = self.__DbFolderPath + '\\ArbokaTransformerDB.db'  # Path to database file

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
                    for col in tableheaders:
                        self.__lTableColmnNames.append(["'%s'" % col, "TEXT", True])
                    self.create_db_table()
                else:
                    # Insert data rows from csv file into database
                    self.populate_db_table(row)
        self.__DbConnection.commit()

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
        list = []
        for row in self.__lTableColmnNames:
            if row[2] == True:
                list.append(row[0][1:-1])
        return list

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

    def get_number_of_tablerecords(self):
        self.__DbCursor.execute("SELECT count(*) FROM %s" % self.__DbTreeTableName)
        res = self.__DbCursor.fetchall()


if __name__ == "__main__":
    db = Database()
    db.import_csv_file(filepath="ArbokatBaumdaten_test.csv")
    db.get_number_of_tablerecords()
    db.close_db_connection()
    db.delete_db()
