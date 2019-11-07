import os
import csv
import sqlite3


class Database:
    def __init__(self):

        self.__DbFolderPath = ""  # Path to the folder where the database is stored
        self.create_default_database_path()
        self.__DbFilePath = self.__DbFolderPath + '\\ArbokaTransformerDB.db'  # Path to database file

        if not os.path.exists(self.__DbFolderPath):
            os.makedirs(self.__DbFolderPath)

        self.__DbConnection = sqlite3.connect(self.__DbFilePath)
        self.__DbCursor = self.__DbConnection.cursor()
        self.__DbTreeTableName = "trees"
        self.__lTableHeaders = []

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

    def import_csv_file(self, filepath="ArbokatBaumdaten_test.csv", sep=";"):
        with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
            filereader = csv.reader(csvfile, delimiter=sep)
            for idx, row in enumerate(filereader):
                if idx == 0:
                    TableHeaders = row
                    for idx, col in enumerate(TableHeaders):
                        self.__lTableHeaders.append([col, "TEXT", True])
                    self.create_db_table()
                else:
                    pass

    def create_db_table(self):
        for idx, col in enumerate(self.__lTableHeaders):
            if idx==0:
                self.__DbCursor.execute("CREATE TABLE %s(%s %s);" %(self.__DbTreeTableName, col[0], col[1]))
            else:
                self.__DbCursor.execute("ALTER TABLE %s ADD COLUMN %s %s" %(self.__DbTreeTableName, "'"+col[0]+"'", col[1]))

    # closes database connection
    def close_db_connection(self):
        self.__DbConnection.close()

    # deletes database folder
    def delete_db_folder(self):
        if os.path.exists(self.__DbFolderPath):
            os.rmdir(self.__DbFolderPath)

    # deletes database file
    def delete_db_file(self):
        if os.path.exists(self.__DbFilePath):
            os.remove(self.__DbFilePath)

    def delete_database(self):
        self.delete_db_file()
        self.delete_db_folder()


if __name__ == "__main__":
    db = Database()
    db.import_csv_file()
    db.close_db_connection()
    db.delete_database()
