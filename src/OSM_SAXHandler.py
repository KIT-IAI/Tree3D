# -*- coding: cp1252 -*-
# Autor: J. Benner
# Datum: 9.12.2015
# Zweck: OSM SAX Handler

from xml.sax import handler

from ast import literal_eval


class OSMHandlerInspector(handler.ContentHandler):

    def __init__(self):
        handler.ContentHandler.__init__(self)

        self.__attribute_dict = {}

        self.__actNode = None
        self.__actContent = ""
        
    def startElement(self, name, atts):
        if name == "tag":
            key = atts["k"]
            value = atts["v"]

            if key not in self.__attribute_dict:
                self.__attribute_dict[key] = [False, False, False]

            self.check_datatype(key, value)

    def check_datatype(self, key, value):
        try:
            dat = literal_eval(value.replace(",", "."))
            if isinstance(dat, int):
                self.__attribute_dict[key][0] = True
            elif isinstance(dat, float):
                self.__attribute_dict[key][1] = True
            else:
                self.__attribute_dict[key][2] = True
        except:
            self.__attribute_dict[key][2] = True

    def get_columns(self):
        column_list = []

        for key in self.__attribute_dict:
            int_type_in_list = self.__attribute_dict[key][0]
            real_type_in_list = self.__attribute_dict[key][1]
            text_type_in_list = self.__attribute_dict[key][2]

            if int_type_in_list and not real_type_in_list and not text_type_in_list:
                data_type = "INTEGER"
            elif real_type_in_list and not text_type_in_list:
                data_type = "REAL"
            else:
                data_type = "TEXT"

            column_list.append([key, data_type, True])

        return column_list
