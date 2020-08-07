#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ###########################################################
# Eine Klasse zur Anzeige einer OpenStreetMap-Karte samt
# Scroll- und Zoom-Steuerung.
#
# Detlev Ahlgrimm, 2017
#
#
# 08.04.2017  erste Version
# 10.04.2017  kompletter Umbau, der jetzt die Position (0, 0) als Referenz-Punkt
#             verwendet (statt vorher den Mittelpunkt der Anzeige).
# 13.04.2017  nochmal deutlicher Umbau, weil ein statischer Faktor für "lat/lon zu Pixel"
#             nicht wirklich funktioniert - zumindest nicht für lat.
# 14.04.2017  nicht existente Tiles (außerhalb der Karte) erkennen und nicht
#             ständig versuchen, sie zu laden (bzw. Unterscheidung zwischen
#             "laden unmöglich" und "laden fehlgeschlagen").
# 15.04.2017  getVisibleRectangle() und getZoomAndCenterForAllPointsVisible() zugefügt

import math
import wx  # python-wxWidgets-2.8.12.1-10.4.1.x86_64

from OsmMapWindow.OSM_TileCache import TileCache


# ######################################################################
# Die Referenz ist immer der Punkt (0, 0) im Fenster. Also links oben.
#
# lat - Y-Achse, bei uns gehen höhere Werte nach Norden
# lon - X-Achse, bei uns gehen höhere Werte nach Westen
# östlich von Greenwich wird lon negativ
# südlich vom Äquator wird lat negativ
#
# Notation für Variablennamen:
#   variableXY  - Koordinaten in Pixel auf dem DC
#   variableTN  - TileNumber
#   variableLL  - Koordinaten in Lat/Lon
class OSM_screen():
    def __init__(self, dc_sizeXY, srv_data, centerLL, zoom, border=(2, 2)):
        self.ts = srv_data["tile_size"]
        self.tc = TileCache(srv_data["cache_dir"], srv_data["tile_url"])
        self.max_zoom = srv_data["max_zoom"]
        self.status = self.tc.getStatusDict()
        self.setSize(dc_sizeXY, zoom, border)
        self.shiftXY = self.shift_tempXY = self.shift_statXY = (0, 0)
        self.setCenter(centerLL)

    # ######################################################################
    # Richtet die Karte so aus, dass der Längen/Breitengrad "centerLL" in
    # der Mitte des Anzeigebereiches zu liegen kommt.
    # Während eines Verschiebevorganges wird das Zentrum um "self.shiftXY"
    # verschoben ausgerichtet.
    def setCenter(self, centerLL):
        self.__setPoint(centerLL, (self.dc_sizeXY[0] / 2, self.dc_sizeXY[1] / 2))

    # ######################################################################
    # Richtet die Karte so aus, dass der Längen/Breitengrad "posLL" auf der
    # Pixel-Position "posXY" zu liegen kommt.
    def __setPoint(self, posLL, posXY):
        cpdTN = self.deg2numF(posLL, self.zoom)  # Tile-Nummer unter der Ziel-Koordinate (float)
        cpbTN = (int(cpdTN[0]), int(cpdTN[1]))  # Tile-Nummer unter der Ziel-Koordinate (int)
        cprXY = ((cpdTN[0] - int(cpdTN[0])) * self.ts, (cpdTN[1] - int(cpdTN[1])) * self.ts)  # Pixel-Versatz zu cpdTN
        tcbpXY = (posXY[0] - cprXY[0], posXY[1] - cprXY[1])  # Basis-Position von Tile unter der Ziel-Koordinate
        tdist = (int(math.ceil(tcbpXY[0] / self.ts)),
                 int(math.ceil(tcbpXY[1] / self.ts)))  # Anzahl Tiles bis zum Tile auf (0, 0)
        tn00TN = (cpbTN[0] - tdist[0], cpbTN[1] - tdist[1])  # Tile-Nummer des Tiles auf (0, 0)
        tn0dXY = (tcbpXY[0] - tdist[0] * self.ts, tcbpXY[1] - tdist[1] * self.ts)  # Basis-Position von Tile auf (0, 0)
        t0d = (abs(tn0dXY[0]) / self.ts, abs(tn0dXY[1]) / self.ts)
        self.pos0LL = self.num2deg((tn00TN[0] + t0d[0], tn00TN[1] + t0d[1]),
                                   self.zoom)  # Geo-Koordinaten der (0, 0)-Position vom Tile auf (0, 0)

    # ######################################################################
    # Passt alle entsprechenden Variablen einer [neuen] Fenstergröße an.
    def setSize(self, dc_sizeXY, zoom, border=(2, 2)):
        self.dc_sizeXY = dc_sizeXY  # Breite, Höhe des Darstellungs-Bereiches
        self.zoom = zoom  # der Zoom-Level von OSM
        self.border = border  # pro Rand zusätzlich zu ladende Anzahl von Tiles (horizontal, vertikal)

        # Anzahl der sichtbaren Tiles (x, y) je nach Anzeigegröße
        self.tile_cnt_dc = (float(dc_sizeXY[0]) / self.ts, float(dc_sizeXY[1]) / self.ts)
        self.tile_cnt_dc_max = (int(math.ceil(self.tile_cnt_dc[0])), int(math.ceil(self.tile_cnt_dc[1])))

    # ######################################################################
    # Ändert die Zoom-Stufe und sorgt dafür, dass die Koordinate wieder an
    # der Position des Mauszeigers landet, die vor dem Zoom dort war.
    def setZoom(self, zoom, posXY):
        posLL = self.getLatLonForPixel(posXY)  # Position bei altem Zoom-Level merken
        self.zoom = zoom  # Zoom-Level ändern
        self.__setPoint(posLL, posXY)  # gemerkte Position wieder einstellen
        self.tc.flushQueue()  # alte, ggf. noch anstehende Tile-Requests können jetzt weg

    # ######################################################################
    # Bewegt das an Position (0, 0) angezeigte Pixel (samt der restlichen
    # Karte) um "distXY" Pixel.
    def doMoveMap(self, distXY):
        self.shift_tempXY = distXY
        self.shiftXY = self.shift_tempXY + self.shift_statXY

    # ######################################################################
    # Stellt das derzeit an Position (0, 0) angezeigte Pixel als neue
    # Basis ein.
    def endMoveMap(self):
        self.pos0LL = self.getLatLonForPixel(self.shiftXY)
        self.shift_statXY = self.shiftXY = (0, 0)

    # ######################################################################
    # Liefert Längen/Breitengrad unter dem Pixel "posXY".
    # Wird die Karte gerade per doMoveMap() verschoben, muss der aktuelle
    # Versatz gemäß getOffset() auf "posXY" addiert werden.
    def getLatLonForPixel(self, posXY):
        tile0TN = self.deg2num(self.pos0LL, self.zoom)  # TileNummer vom Tile auf (0, 0)
        tile0iLL = self.num2deg(tile0TN, self.zoom)  # lat/lon des Eckpunktes vom Tile auf (0, 0)
        tile0d0XY = self.distanceLatLonToPixel(self.pos0LL, tile0iLL)  # Abstand Eckpunkt zu (0, 0)
        distXY = (posXY[0] - tile0d0XY[0], posXY[1] - tile0d0XY[1])  # Abstand Eckunkt vom Tile auf (0, 0) zu posXY
        tdist = (float(distXY[0]) / self.ts, float(distXY[1]) / self.ts)  # Abstand von posXY zu (0, 0) in Tiles
        tdp = (tile0TN[0] + tdist[0], tile0TN[1] + tdist[1])
        tpLL = self.num2deg(tdp, self.zoom)
        return (tpLL)

    # ######################################################################
    # Liefert für zwei Längen/Breitengrade deren Abstand in Pixel.
    def distanceLatLonToPixel(self, pos1LL, pos2LL):
        t1TN = self.deg2numF(pos1LL, self.zoom)
        t2TN = self.deg2numF(pos2LL, self.zoom)
        tdist = (t2TN[0] - t1TN[0], t2TN[1] - t1TN[1])
        distXY = (int(round(tdist[0] * self.ts)), int(round(tdist[1] * self.ts)))
        return (distXY)

    # ######################################################################
    # Liefert zu einem Längen/Breitengrad "posLL" die Pixel-Koordinaten.
    # Die Rückgabe ist auch während eines Verschiebevorganges gültig.
    def getPixelForLatLon(self, posLL):
        dx, dy = self.distanceLatLonToPixel(self.pos0LL, posLL)
        return (int(dx) - self.shiftXY[0], int(dy) - self.shiftXY[1])

    # ######################################################################
    # Liefert den aktuellen Versatz in Pixeln während des scrollens.
    def getOffset(self):
        return (self.shiftXY)

    # ######################################################################
    # Liefert die Eckpunkte des aktuell sichtbaren Bereiches in lat/lon.
    # Die Rückgabe ist auch während eines Verschiebevorganges gültig.
    def getVisibleRectangle(self):
        p1 = self.getLatLonForPixel(self.shiftXY)
        p2 = self.getLatLonForPixel((self.shiftXY[0] + self.dc_sizeXY[0], self.shiftXY[1] + self.dc_sizeXY[1]))
        return (p1, p2)

    # ######################################################################
    # Stellt die Map dar.
    # Liefert True, wenn mindestens ein sichtbares Tile ein Leer-Tile ist.
    def drawMap(self, dc):
        imgs, border_fixXY = self.__getImages()
        y = -(self.shiftXY[1] + border_fixXY[1])
        needs_refresh = False
        for yi in imgs:
            x = -(self.shiftXY[0] + border_fixXY[0])
            for tn, (status, xi) in yi:
                if status != self.status["GOOD"]:
                    xi = wx.Bitmap.FromRGBA(256, 256, red=255, alpha=1)
                    if self.__isVisible(x, y) and status != self.status["INVALID"]:
                        needs_refresh = True
                dc.DrawBitmap(xi, x, y)
                # dc.DrawLine(x, y, x+self.ts, y)
                # dc.DrawLine(x, y, x, y+self.ts)
                x += self.ts
            y += self.ts
        # dc.DrawLine(0, 0, self.dc_sizeXY[0], self.dc_sizeXY[1])
        return (needs_refresh)

    # ######################################################################
    # Liefert True, wenn das Tile aktuell sichtbar ist.
    def __isVisible(self, x, y):
        if x + self.ts < 0 or x > self.dc_sizeXY[0] or y + self.ts < 0 or y > self.dc_sizeXY[1]:
            return (False)
        return (True)

    # ######################################################################
    # Liefert die Bilder als Liste von Listen zusammen mit ihrer TileNummer.
    # Also als:
    #     [ [ ((xTN, yTN), img), ((xTN, yTN), img), ... ],    # erste Zeile
    #       [ ((xTN, yTN), img), ((xTN, yTN), img), ... ],    # zweite Zeile
    #       ... ]
    # Als zweiter Wert wird ein Tupel mit dem Pixelversatz geliefert, damit
    # "self.pos0LL" genau in der linken oberen Ecke erscheint.
    def __getImages(self):
        tile0TN = self.deg2num(self.pos0LL, self.zoom)  # das an (0, 0) darzustellen Image bestimmen
        yl = list()
        tile0iLL = self.num2deg((tile0TN[0] - self.border[0], tile0TN[1] - self.border[1]),
                                self.zoom)  # lat/lon vom unsichtbaren Tile00
        border_fixXY = self.distanceLatLonToPixel(tile0iLL, self.pos0LL)
        for y in range(-self.border[1], self.tile_cnt_dc_max[1] + self.border[1]):
            xl = list()
            for x in range(-self.border[0], self.tile_cnt_dc_max[0] + self.border[0]):
                xl.append(
                    ((tile0TN[0] + x, tile0TN[1] + y), self.tc.getTile(tile0TN[0] + x, tile0TN[1] + y, self.zoom)))
            yl.append(xl)
        return (yl, border_fixXY)

    # ######################################################################
    # Liefert die Anzahl der noch unbeantworteten Tile-Requests.
    def getOpenRequests(self):
        return (self.tc.getQueueLength())

    # ######################################################################
    # Liefert ein Tupel aus dem höchsten Zoom-Level, bei dem alle
    # Koordinaten aus "point_listLL" auf den Anzeigebreich passen und den
    # Geo-Koordinaten des Mittelpunktes.
    def getZoomAndCenterForAllPointsVisible(self, point_listLL):
        neLL = swLL = point_listLL[0]
        for pLL in point_listLL:  # Eckpunkte suchen
            if pLL[0] > neLL[0]:  neLL = (pLL[0], neLL[1])  # lat(n)
            if pLL[0] < swLL[0]:  swLL = (pLL[0], swLL[1])  # lat(s)
            if pLL[1] < neLL[1]:  neLL = (neLL[0], pLL[1])  # lon(e)
            if pLL[1] > swLL[1]:  swLL = (swLL[0], pLL[1])  # lon(w)
        for zoom in range(self.max_zoom, -1, -1):
            pneTN = self.deg2numF(neLL, zoom)  # Tile(nord osten) = links oben
            pswTN = self.deg2numF(swLL, zoom)  # Tile(süd westen) = rechts unten
            dx = abs(pswTN[0] - pneTN[0])  # Tile-Delta x
            dy = abs(pswTN[1] - pneTN[1])  # Tile-Delta y
            if dx < self.tile_cnt_dc[0] and dy < self.tile_cnt_dc[1]:
                return (zoom, (neLL[0] - (neLL[0] - swLL[0]) / 2, swLL[1] - (swLL[1] - neLL[1]) / 2))

    # ######################################################################
    # Lon./lat. to tile numbers
    # Quelle: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
    def deg2num(self, latlon, zoom):
        x, y = self.deg2numF(latlon, zoom)
        return (int(x), int(y))

    def deg2numF(self, p_deg, zoom):
        lat_deg, lon_deg = p_deg
        try:
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = (lon_deg + 180.0) / 360.0 * n
            ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        except:
            print("error deg2num()")
            return (0, 0)
        return (xtile, ytile)

    # ######################################################################
    # Tile numbers to lon./lat.
    # Quelle: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
    def num2deg(self, tile, zoom):
        xtile, ytile = tile
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)
