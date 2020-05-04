# this module stores global program settings


class ColumnNames:
    def __init__(self):
        self.__id = None

        self.__x = None
        self.__y = None
        self.__RefHeight = None

        self.__TreeHeight = None
        self.__TreeHeightUnit = None

        self.__TrunkDiam = None
        self.__TrunkDiamMode = None
        self.__TrunkDiamUnit = None

        self.__CrownDiam = None
        self.__CrownDiamMode = None
        self.__CrownDiamUnit = None

        self.__Class = None
        self.__Species = None
        self.__CrownHeight = None

    def print(self):
        print("X:", self.__x)
        print("Y:", self.__y)
        print("RefHeight:", self.__RefHeight)
        print("Tree Height:", self.__TreeHeight, "unit:", self.__TreeHeightUnit)
        print("Trunk:", self.__TrunkDiam, "mode:", self.__TrunkDiamMode, "unit:", self.__TrunkDiamUnit)
        print("crown:", self.__CrownDiam, "mode:", self.__CrownDiamMode, "unit:", self.__CrownDiamUnit)
        print("class:", self.__Class)
        print("species:", self.__Species)
        print("crown height:", self.__CrownHeight)
        print("- - - - - - - - - - -")

    def set_id(self, col):
        self.__id = col

    def get_id(self):
        return self.__id

    def set_coordinates(self, x, y):
        self.__x = x
        self.__y = y

    def get_coordinates(self):
        return self.__x, self.__y

    def set_ref_height(self, colname):
        self.__RefHeight = colname

    def get_ref_height(self):
        return self.__RefHeight

    def set_tree_height(self, colname, unit):
        self.__TreeHeight = colname
        self.__TreeHeightUnit = unit

    def get_tree_height(self):
        return self.__TreeHeight, self.__TreeHeightUnit

    def set_trunk_diam(self, colname, mode, unit):
        self.__TrunkDiam = colname
        self.__TrunkDiamMode = mode
        self.__TrunkDiamUnit = unit

    def get_trunk_diam(self):
        return self.__TrunkDiam, self.__TrunkDiamMode, self.__TrunkDiamUnit

    def set_crown_diam(self, colname, mode, unit):
        self.__CrownDiam = colname
        self.__CrownDiamMode = mode
        self.__CrownDiamUnit = unit

    def get_crown_diam(self):
        return self.__CrownDiam, self.__CrownDiamMode, self.__CrownDiamUnit

    def set_class(self, colname):
        self.__Class = colname

    def get_class(self):
        return self.__Class

    def set_species(self, colname):
        self.__Species = colname

    def get_species(self):
        return self.__Class

    def set_crown_height(self, colname):
        self.__CrownHeight = colname

    def get_crown_height(self):
        return self.__CrownHeight
