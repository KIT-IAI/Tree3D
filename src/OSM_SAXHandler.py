from xml.sax import handler

from ast import literal_eval


# Handler for OSM data
# Inspects data to find all data keys and data types
class OSMHandlerInspector(handler.ContentHandler):

    def __init__(self):
        handler.ContentHandler.__init__(self)

        self.__attribute_dict = {}

        self.__tree_list = []
        self.__activeTree = None
        
    def startElement(self, name, atts):
        if name == "node":
            self.__activeTree = {"OSM_ID": int(atts["id"]),
                                 "X_VALUE": float(atts["lon"]),
                                 "Y_VALUE": float(atts["lat"])}
            self.__tree_list.append(self.__activeTree)

        if name == "tag":
            key = atts["k"]
            value = atts["v"]

            if key not in self.__attribute_dict:
                self.__attribute_dict[key] = [False, False, False]

            self.check_datatype(key, value)

            self.__activeTree["%s" % key] = value

    def check_datatype(self, key, value):
        try:
            dat = literal_eval(value.replace(",", "."))

            if not dat:
                return

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

            column_list.append(["'%s'" % key, data_type, True])

        return column_list

    def get_tree_list(self):
        return self.__tree_list
