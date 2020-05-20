from pyproj import CRS
from pyproj import Transformer

import xml.etree.ElementTree as ET


class Geometry:
    """
    Class to represent geometry.
    Superclass to all other geometric representations in thie module.
    """

    def __init__(self, epsg, dimension, geom_id=None):
        """
        Initialize
        :param epsg: EPSG Code of Geometry (int)
        :param dimension: Dimension of Geometry (int)
        :param geom_id: ID of geom object
        """

        self._epsg = epsg
        self._dimension = dimension
        self._id = geom_id

    def get_epsg(self):
        """
        Returns the EPSG Code of Geometry cooridnate system
        :return: EPSG Code (int)
        """
        return self._epsg

    def get_dimension(self):
        """
        Returns dimension of Geometry (2 or 3)
        :return: dimension (int)
        """
        return self._dimension

    def transform(self, to_epsg):
        """
        Method to transform Geometry to other Coordinate system.
        Is overwritten in subclasses: Does Nothing
        :param to_epsg: EPSG Code of target reference system
        :return: None
        """
        pass

    def get_citygml_geometric_representation(self):
        """
        Method to transform Geometry to other Coordinate system
        Is overwritten in subclasses: Does Nothing
        :return: None
        """
        pass


# class to represent a Point in 2D or 3D
class Point(Geometry):
    """
    Class to represent a Point in 2D or 3D
    """

    def __init__(self, epsg, dimension, x, y, z=0.0):
        """
        Initialize
        :param epsg: EPSG Code of Geometry (int)
        :param dimension: Dimension of Geometry: 2 or 3 (int)
        :param x: X Coordinate (float)
        :param y: Y Coordinate (float)
        :param z: Z Coordinate (float)
        """

        Geometry.__init__(self, epsg, dimension)
        self.__x = x
        self.__y = y
        self.__z = z

    def __str__(self):
        return "EPSG: %s, Dimension: %s, (%s, %s, %s)" % (self._epsg, self._dimension, self.__x, self.__y, self.__z)

    def get_coordinates(self):
        """
        Get Point coordinates
        :return: Point coordinates as tuple (x, y, z)
        """
        return self.__x, self.__y, self.__z

    def get_x(self):
        """
        Returns X value
        :return: X value (float)
        """
        return self.__x

    def get_y(self):
        """
        Returns Y value
        :return: Y value (float)
        """
        return self.__y

    def get_z(self):
        """
        Returns Z value
        :return: Z value (float)
        """
        return self.__z

    def transform(self, to_epsg):
        """
        Method to perform coordinate transformation
        :param to_epsg: EPSG Code of target coordinate system (int)
        :return: New point object (transformed)
        """
        source_epsg = CRS.from_epsg(self._epsg)
        target_epsg = CRS.from_epsg(to_epsg)

        trans = Transformer.from_crs(source_epsg, target_epsg)
        result = trans.transform(self.__x, self.__y)
        return Point(to_epsg, self._dimension, result[0], result[1], self.__z)

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML Point geometry
        :return: GML Point geometry (ET.Element() object)
        """
        point = ET.Element("gml:Point")
        point.set("srsDimension", str(self._dimension))
        point.set("srsName", "EPSG:%s" % self._epsg)
        if self._id is not None:
            point.set("gml:id", self._id)

        pos = ET.SubElement(point, "gml:pos")
        pos.set("srsDimension", str(self._dimension))

        postext = "%s %s" % (self.__x, self.__y)
        if self._dimension == 3:
            postext += " %s" % self.__z
        pos.text = postext
        return point


class LineString(Geometry):
    """
    Class to represent a Line String
    """
    def __init__(self, epsg, dimension, startpoint, endpoint, geom_id=None):
        """
        Initialize
        :param epsg: EPSG code of Geometry (int)
        :param dimension: Dimension of Geometry (int)
        :param startpoint: Starting point of line string (Point object)
        :param endpoint: Endign point of line string (Point object)
        :param geom_id: ID of geometry
        """
        Geometry.__init__(self, epsg, dimension, geom_id)
        self.__start = startpoint
        self.__end = endpoint

    def get_start(self):
        """
        Returns starting point of line string
        :return: Starting poing (Point object)
        """
        return self.__start

    def get_end(self):
        """
        Returns end point of line string
        :return: Ending point (Point object)
        """
        return self.__end

    def transform(self, to_epsg):
        """
        Method to perform coordinate transformation
        :param to_epsg: EPSG Code of target coordinate system
        :return: New LineString object (transfomred)
        """
        start_new = self.__start.transform(to_epsg)
        end_new = self.__end.transform(to_epsg)

        return LineString(to_epsg, self._dimension, start_new, end_new)

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML LineString geometry
        :return: GML LineString geometry (ET.Element() object)
        """
        linestring = ET.Element("gml:LineString")
        linestring.set("srsDimension", str(self._dimension))
        linestring.set("srsName", "EPSG:%s" % self._epsg)
        if self._id is not None:
            linestring.set("gml:id", self._id)

        poslist = ET.SubElement(linestring, "gml:posList")
        poslist.set("srsDimension", str(self._dimension))
        postext = ""
        if self._dimension == 2:
            postext = "%s %s " % (self.__start.get_x(), self.__start.get_y())
            postext += "%s %s" % (self.__end.get_x(), self.__end.get_y())
        elif self._dimension == 3:
            postext = "%s %s %s " % (self.__start.get_x(), self.__start.get_y(), self.__start.get_z())
            postext += "%s %s %s" % (self.__end.get_x(), self.__end.get_y(), self.__end.get_z())
        poslist.text = postext
        return linestring


class Polygon(Geometry):
    """
    Class to represent a polygon.
    Inner rings not supported (yet?)
    """
    def __init__(self, epsg, dimension, l_ext_pnts=None, geom_id=None):
        """
        Initialize
        :param epsg: EPSG code of Geometry (int)
        :param dimension: Dimension of Geometry (int)
        :param l_ext_pnts: List of Point objects for outer polygon ring, Default: None -> []
        geom_id: ID of geometry
        """
        Geometry.__init__(self, epsg, dimension, geom_id)

        if l_ext_pnts is None:
            l_ext_pnts = []

        self.__exterior = l_ext_pnts

    def set_exterior(self, l_ext_pnts):
        """
        Method to set exterior ring
        :param l_ext_pnts: List of Point objects for outer polygon ring
        :return: None
        """
        self.__exterior = l_ext_pnts

    def exterior_add_point(self, pnt):
        """
        Method to add point to outer polygon ring
        :param pnt: Point object
        :return: None
        """
        self.__exterior.append(pnt)

    def transform(self, to_epsg):
        """
        Method to perform coordiante transformation
        :param to_epsg: EPSG code of target coordinate system
        :return: New Polygon object (transformed)
        """
        ext_pnts_new = []
        for point in self.__exterior:
            pnt_new = point.transform(to_epsg)
            ext_pnts_new.append(pnt_new)

        return Polygon(to_epsg, self._dimension, ext_pnts_new)

    def get_citygml_geometric_representation_nometadata(self):
        """
        Method to generate GML Polygon geometry without Metadata (srsDimension, srsName)
        :return: GML Polygon geometry (ET.Element() object)
        """
        polygon = ET.Element("gml:Polygon")
        if self._id is not None:
            polygon.set("gml:id", self._id)

        exterior = ET.SubElement(polygon, "gml:exterior")
        linearring = ET.SubElement(exterior, "gml:LinearRing")
        poslist = ET.SubElement(linearring, "gml:posList")
        poslist.set("srsDimension", str(self._dimension))
        postext = ""
        for point in self.__exterior:
            postext += "%s %s " % (point.get_x(), point.get_y())
            if self._dimension == 3:
                postext += "%s " % point.get_z()
        poslist.text = postext
        return polygon

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML Polygon geometry
        :return: GML Polygon geometry (ET.Element() object)
        """
        polygon = self.get_citygml_geometric_representation_nometadata()
        polygon.set("srsDimension", str(self._dimension))
        polygon.set("srsName", "EPSG:%s" % self._epsg)
        return polygon


class CompositePolygon(Geometry):
    """
    Class to represent a composite polygon
    """
    def __init__(self, epsg, dimension, l_polygons=None, geom_id=None):
        """
        Initialize
        :param epsg: EPSG code of Geometry (int)
        :param dimension: Dimension of Geometry (int)
        :param l_polygons: List of Polygon objects, Default: None -> []
        :param geom_id: Geometry ID
        """
        Geometry.__init__(self, epsg, dimension, geom_id)

        if l_polygons is None:
            l_polygons = []

        self.__polygons = l_polygons

    def set_polygons(self, l_polygons):
        """
        Method to set list of polygons
        :param l_polygons: list of Polygon objects
        :return: None
        """
        self.__polygons = l_polygons

    def add_polygon(self, polygon):
        """
        Method to add a polygon to Composite polygon object
        :param polygon: Polygon object
        :return: None
        """
        self.__polygons.append(polygon)

    def transform(self, to_epsg):
        """
        Method to perform coordinate transformation
        :param to_epsg: EPSG code of target coordinate system
        :return: New CompositeSurface object (transfomred)
        """
        polygons_new = []
        for polygon in self.__polygons:
            polygon.transform(to_epsg)

        return CompositePolygon(to_epsg, self._dimension, polygons_new)

    def get_citygml_geometric_representation_nometadata(self):
        """
        Method to generate GML CompositeSurface geometry without Metadata (srsDimension, srsName)
        :return: GML CompositeSurface geometry (ET.Element() object)
        """
        compsurface = ET.Element("gml:CompositeSurface")
        if self._id is not None:
            compsurface.set("gml:id", self._id)
        for polygon in self.__polygons:
            surfacemember = ET.SubElement(compsurface, "gml:surfaceMember")
            polygonxml = polygon.get_citygml_geometric_representation_nometadata()
            surfacemember.append(polygonxml)
        return compsurface

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML CompositeSurface geometry
        :return: GML CompositeSurface geometry (ET.Element() object)
        """
        compsurface = self.get_citygml_geometric_representation_nometadata()
        compsurface.set("srsDimension", str(self._dimension))
        compsurface.set("srsName", "EPSG:%s" % self._epsg)
        return compsurface


class Solid(Geometry):
    """
    Class to represent a solid object
    Interior not supported (yet?)
    """
    def __init__(self, epsg, dimension, ext_comp_polygon=None, geom_id=None):
        """
        Initialize
        :param epsg: EPSG code of geometry
        :param dimension: dimension of geometry
        :param ext_comp_polygon: CompositePolygon object for exterior, Default: None
        :param geom_id: Geometry ID
        """
        Geometry.__init__(self, epsg, dimension, geom_id)

        self.__ExteriorCompositePolygon = ext_comp_polygon

    def set_exterior_comp_polygon(self, ext_comp_polygon):
        """
        Method to set Solid exterior
        :param ext_comp_polygon: CompositePolygon object
        :return: None
        """
        self.__ExteriorCompositePolygon = ext_comp_polygon

    def transform(self, to_epsg):
        """
        Method to perform coordinate transformation
        :param to_epsg: EPSG code of target coordinate system
        :return: New Solid object (transformed)
        """
        exterior_comp_polygon_new = self.__ExteriorCompositePolygon.transform(to_epsg)
        return Solid(to_epsg, self._dimension, exterior_comp_polygon_new)

    def get_citygml_geometric_representation_nometadata(self):
        """
        Method to generate GML Solid geometry without Metadata (srsDimension, srsName)
        :return: GML Solid geometry (ET.Element() object)
        """
        solid = ET.Element("gml:Solid")
        if self._id is not None:
            solid.set("gml:id", self._id)

        exterior = ET.SubElement(solid, "gml:exterior")
        compsurface = self.__ExteriorCompositePolygon.get_citygml_geometric_representation_nometadata()
        exterior.append(compsurface)
        return solid

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML Solid geometry
        :return: GML Solid geometry (ET.Element() object)
        """
        solid = self.get_citygml_geometric_representation_nometadata()
        solid.set("srsDimension", str(self._dimension))
        solid.set("srsName", "EPSG:%s" % self._epsg)
        return solid


class CompositeSolid(Geometry):
    """
    Method to represent CompositeSolid object
    """
    def __init__(self, epsg, dimension, l_solids=None, geom_id=None):
        """
        Initialize
        :param epsg: EPSG code of geometry
        :param dimension: dimension of geometry
        :param l_solids: List of Solid objects, Default: None -> []
        :param geom_id Geometry ID
        """
        Geometry.__init__(self, epsg, dimension, geom_id)

        if l_solids is None:
            l_solids = []

        self.__Solids = l_solids

    def set_solids(self, l_solids):
        """
        Method to set Solid Members
        :param l_solids: List of Solid objects
        :return: None
        """
        self.__Solids = l_solids

    def add_solid(self, solid):
        """
        Method to add Solid object to ComposteSolid
        :param solid: Solid object
        :return: None
        """
        self.__Solids.append(solid)

    def transform(self, to_epsg):
        """
        Method to perform coordinate transformation
        :param to_epsg: EPSG code of target coordinate system
        :return: New CompositeSolid object (transformed)
        """
        solids_new = []
        for solid in self.__Solids:
            solid.transform(to_epsg)

        return CompositeSolid(to_epsg, self._dimension, solids_new)

    def get_citygml_geometric_representation_nometadata(self):
        """
        Method to generate GML CompositeSolid geometry without Metadata (srsDimension, srsName)
        :return: GML CompositeSolid geometry (ET.Element() object)
        """
        compsolid = ET.Element("gml:CompositeSolid")
        if self._id is not None:
            compsolid.set("gml:id", self._id)
        for solid in self.__Solids:
            solidmember = ET.SubElement(compsolid, "gml:solidMember")
            solidxml = solid.get_citygml_geometric_representation_nometadata()
            solidmember.append(solidxml)
        return compsolid

    def get_citygml_geometric_representation(self):
        """
        Method to generate GML CompositeSolid geometry
        :return: GML CompositeSolid geometry (ET.Element() object)
        """
        compsolid = self.get_citygml_geometric_representation_nometadata()
        compsolid.set("srsDimension", str(self._dimension))
        compsolid.set("srsName", "EPSG:%s" % self._epsg)
        return compsolid
