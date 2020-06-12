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
        return Point(to_epsg, self._dimension, result[1], result[0], self.__z)

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

    def get_geojson_geometric_representation(self):
        pnt = [self.__x, self.__y]
        if self.__z != 0.0:
            pnt.append(self.__z)
        return "Point", pnt


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

    def get_cityjson_vertices(self):
        """
        Method to generate CityJSON vertex list
        :return: List of vertices
        """
        vertice_list = [self.__start.get_coordinates(), self.__end.get_coordinates()]
        return vertice_list

    @staticmethod
    def get_cityjson_boundaries():
        """
        Method to generate CityJSON boundary list
        :return: List of boundaries
        """
        return [[0, 1]]

    def get_cityjson_geometric_representation(self):
        """
        Method to generate everything needed for CityJSON geom object construction
        :return: Type, Vertice list, boundary list
        """
        return "MultiLineString", self.get_cityjson_vertices(), self.get_cityjson_boundaries()

    def get_geojson_geometric_representation(self):
        _, start_point = self.__start.get_geojson_geometric_representation()
        _, end_point = self.__end.get_geojson_geometric_representation()
        return "LineString", [start_point, end_point]


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

    def get_cityjson_vertices(self):
        """
        Method to generate CityJSON vertex list
        :return: List of vertices
        """
        vertice_list = []
        for point in self.__exterior:
            vertice_list.append(point.get_coordinates())
        return vertice_list

    def get_cityjson_boundaries(self):
        """
        Method to generate CityJSON boundary list
        :return: List of boundaries
        """
        return list(range(0, len(self.__exterior)))

    def get_cityjson_geometric_representation(self):
        """
        Method to generate everything needed for CityJSON geom object construction
        :return: Type, Vertice list, boundary list
        """
        return "Surface", self.get_cityjson_vertices(), self.get_cityjson_boundaries()

    def get_geojson_geometric_representation(self):
        polygon = []
        exterior = []

        for pnt in self.__exterior:
            _, pnt_geom = pnt.get_geojson_geometric_representation()
            exterior.append(pnt_geom)

        polygon.append(exterior)
        return "Polygon", polygon


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
            poly_new = polygon.transform(to_epsg)
            polygons_new.append(poly_new)

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

    def get_cityjson_vertices(self):
        """
        Method to generate CityJSON vertex list
        :return: List of vertices
        """
        vertice_list = []
        for polygon in self.__polygons:
            vertice_list.extend(polygon.get_cityjson_vertices())
        return vertice_list

    def get_cityjson_boundaries(self):
        """
        Method to generate CityJSON boundary list
        :return: List of boundaries
        """
        boundary_list = []
        for polygon in self.__polygons:
            polygon_boundary_list = polygon.get_cityjson_boundaries()
            add_number = get_cityjson_vertex_number(boundary_list)
            polygon_boundary_list = [x+add_number for x in polygon_boundary_list]
            boundary_list.append([polygon_boundary_list])
        return boundary_list

    def get_cityjson_geometric_representation(self):
        """
        Method to generate everything needed for CityJSON geom object construction
        :return: Type, Vertice list, boundary list
        """
        vertices = self.get_cityjson_vertices()
        boundaries = self.get_cityjson_boundaries()

        cleanup_cityjson_geometry(boundaries, vertices)

        return "MultiSurface", vertices, boundaries

    def get_geojson_geometric_representation(self):
        multi_poly = []
        for poly in self.__polygons:
            _, polygon = poly.get_geojson_geometric_representation()
            multi_poly.append(polygon)
        return "MultiPolygon", multi_poly


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

    def get_cityjson_geometric_representation(self):
        """
        Method to generate everything needed for CityJSON geom object construction
        :return: Type, Vertice list, boundary list
        """
        _, vertices, ext_boundaries = self.__ExteriorCompositePolygon.get_cityjson_geometric_representation()
        boundaries = [ext_boundaries]
        return "Solid", vertices, boundaries

    def get_geojson_geometric_representation(self):
        typ, geom = self.__ExteriorCompositePolygon.get_geojson_geometric_representation()
        return typ, geom


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
            solid_new = solid.transform(to_epsg)
            solids_new.append(solid_new)

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

    def get_cityjson_geometric_representation(self):
        """
        Method to generate everything needed for CityJSON geom object construction
        :return: Type, Vertice list, boundary list
        """
        vertices = []
        boundaris = []
        for solid in self.__Solids:
            _, solid_vertices, solid_boundaries = solid.get_cityjson_geometric_representation()
            add_number = len(vertices)
            vertices.extend(solid_vertices)

            add_cityjson_number(solid_boundaries, add_number)
            boundaris.append(solid_boundaries)

        cleanup_cityjson_geometry(boundaris, vertices)

        return "CompositeSolid", vertices, boundaris

    def get_geojson_geometric_representation(self):
        multi_poly = []
        for solid in self.__Solids:
            _, multipoly = solid.get_geojson_geometric_representation()
            multi_poly.extend(multipoly)
        return "MultiPolygon", multi_poly


def get_cityjson_vertex_number(vertex_list):
    """
    Recursive function to count number of vertices in a CityJSON geometry
    :param vertex_list: CityJSON boundary list
    :return: number of vertices
    """
    count = 0
    for element in vertex_list:
        if type(element) == list:
            count += get_cityjson_vertex_number(element)
        else:
            count += 1
    return count


def cleanup_cityjson_geometry(boundaries, vertices):
    """
    Recursive function to clean up CityJSON geometries
    Removes duplicate vertices from vertice list and updates number in boundary list
    :param boundaries: CityJSON boundary list of a geometry
    :param vertices: CityJSON List of vertices
    :return: None
    """
    delete_verteces = []
    for i in range(0, len(vertices)):
        for j in range(i + 1, len(vertices)):
            if vertices[i] == vertices[j]:
                if j not in delete_verteces:
                    delete_verteces.append(j)
                    replace_cityjson_vertex_number(boundaries, j, i)

    for i in sorted(delete_verteces, reverse=True):
        del (vertices[i])
        reduce_cityjson_vertex_number(boundaries, i)


def replace_cityjson_vertex_number(boundaries_list, replace_from, replace_to):
    """
    Recursive function to replace a vertex number with a different number
    Function is used when updateing vertex list in Cleanup
    :param boundaries_list: CityJSON boundary list of a geometry
    :param replace_from: Number that will be replaced (int)
    :param replace_to: Number it is replaced by (int)
    :return: None
    """
    for i in range(0, len(boundaries_list)):
        if type(boundaries_list[i]) == list:
            replace_cityjson_vertex_number(boundaries_list[i], replace_from, replace_to)
        else:
            if boundaries_list[i] == replace_from:
                boundaries_list[i] = replace_to


def reduce_cityjson_vertex_number(boundaries_list, threshold):
    """
    Recursive function to reduce all vertex numbers by 1, if number is greater than a certain threshold
    Function is used when duplicate vertice is removed from vertice list
    :param boundaries_list: CityJSON boundary list of a geometry
    :param threshold: int
    :return: None
    """
    for i in range(0, len(boundaries_list)):
        if type(boundaries_list[i]) == list:
            reduce_cityjson_vertex_number(boundaries_list[i], threshold)
        else:
            if boundaries_list[i] > threshold:
                boundaries_list[i] -= 1


def add_cityjson_number(boundaries_list, number):
    """
    Recursive function to Add a number to any vertex in CityJSON boundary list
    :param boundaries_list: CityJSON boundary list of a geometry
    :param number: Number to add to each vertex
    :return: None
    """
    for i in range(0, len(boundaries_list)):
        if type(boundaries_list[i]) == list:
            add_cityjson_number(boundaries_list[i], number)
        else:
            boundaries_list[i] += number
