#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ###########################################################
# Ein kleines GUI als Test der OSM_screen-Klasse.
# Also Anzeige der OpenStreetMap-Karte mit der Möglichkeit
# des scrollens, zoomens und einer Track-Anzeige.
#
# Detlev Ahlgrimm, 2017
#
#
# 08.04.2017  erste Version
# 10.04.2017  kompletter Umbau
# 14.04.2017  scrollMapToPoint() und Server-Wahl mittels SOURCE eingebaut
# 15.04.2017  Zoomlevel-Anpassung nach Track-Laden eingebaut
#

import wx  # python-wxWidgets-2.8.12.1-10.4.1.x86_64
import time
import math
import os
from lxml import etree  # python-lxml-3.3.5-2.1.4.x86_64
from datetime import datetime, tzinfo, timedelta
from time import mktime
from calendar import timegm

from OsmMapWindow.OSM_screen import OSM_screen

VERSION = "1.2"

HOME_DIR = os.path.expanduser('~')
# http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_servers
# http://www.thunderforest.com/docs/apikeys/
SOURCE = {
    "OSM": {"tile_url": "https://a.tile.openstreetmap.de/16/34501/20788.png",
            "tile_size": 256,
            "max_zoom": 19,
            "cache_dir": os.path.join(HOME_DIR, "tilecache", "osm")
            },
    "OCM": {"tile_url": "https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=...selbst.API-Key.holen.........",
            "tile_size": 256,
            "max_zoom": 18,
            "cache_dir": os.path.join(HOME_DIR, "tilecache", "ocm")
            },
    "FAU": {"tile_url": "https://osm.rrze.fau.de/osmde/{z}/{x}/{y}.png",
            "tile_size": 256,
            "max_zoom": 19,
            "cache_dir": os.path.join(HOME_DIR, "tilecache", "fau")
            },
    "FAUHD": {"tile_url": "https://osm.rrze.fau.de/osmhd/{z}/{x}/{y}.png",
              "tile_size": 512,
              "max_zoom": 19,
              "cache_dir": os.path.join(HOME_DIR, "tilecache", "fauhd")
              },
    "OSMDE": {"tile_url": "https://a.tile.openstreetmap.de/{z}/{x}/{y}.png",
              "tile_size": 256,
              "max_zoom": 19,
              "cache_dir": os.path.join(HOME_DIR, "tilecache", "osmde")
              }
}
SERVER = "OSMDE"


# Notation für Variablennamen:
#   variableXY  - Koordinaten in Pixel auf dem DC
#   variableTN  - TileNumber
#   variableLL  - Koordinaten in Lat/Lon

# ###########################################################
# Quelle: https://aboutsimon.com/blog/2013/06/06/Datetime-hell-Time-zone-aware-to-UNIX-timestamp.html
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


# ###########################################################
# Liefert den UNIX-Timestamp für einen Timestamp-String in
# UTC.
# Erweitert mit: http://stackoverflow.com/a/33148723/3588613
def getTimestampStringAsUTC(strg):
    if "." in strg:
        datetime_obj = datetime.strptime(strg, '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        datetime_obj = datetime.strptime(strg, '%Y-%m-%dT%H:%M:%SZ')
    datetime_obj = datetime_obj.replace(tzinfo=UTC())
    timestamp = timegm(datetime_obj.timetuple())
    return (timestamp)


# ###########################################################
# eine kleine Klasse, um neue Dateien via Drag&Drop öffnen
# zu können.
class FileDrop(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) > 1:
            wx.MessageBox('Es kann nur eine Datei geladen werden!', 'Fehler', wx.OK | wx.ICON_ERROR)
            return
        self.window.fileDropped(filenames[0])


# ######################################################################
# Das eigentliche Fenster mit der OSM-Ansicht.
class MapWindow(wx.Window):
    def __init__(self, parent, centerLL, zoom, border, title, size):
        wx.Window.__init__(self, parent)
        self.parent = parent
        self.centerLL = centerLL
        self.zoom = zoom
        self.border = border

        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_MOTION, self.onMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        self.timer_interval = 100
        self.timer = wx.Timer(self)
        self.timer.Start(self.timer_interval)

        self.statusbar = self.parent.CreateStatusBar(5)
        self.statusbar.SetStatusWidths([50, 50, 100, -1, -1])
        self.dc_sizeXY = self.GetSize()  # das ist schon die Größe abzüglich der Statusbar

        self.line_list = list()
        self.leftDown = False
        self.ctrlIsDown = False
        self.osm = OSM_screen(self.dc_sizeXY, SOURCE[SERVER], centerLL, self.zoom, self.border)
        self.pt1LL = None
        self.esc = False
        self.file_loaded = False
        self.refresh_needed = False
        self.was_moved = False
        self.superspeed = False
        self.initial_follow_pointLL = None
        self.autofollow_running = False

        self.bbox = []

        bsizer = wx.BoxSizer(wx.VERTICAL)

        self.text1 = wx.StaticText(self, wx.ID_ANY, u"Select upper left bounding box coordinate",
                                            wx.DefaultPosition, wx.DefaultSize, 0)
        self.text1.SetBackgroundColour("white")
        font = wx.Font(wx.FontInfo(15))
        self.text1.SetFont(font)
        self.text1.Wrap(-1)
        bsizer.Add(self.text1)

        text2 = wx.StaticText(self, wx.ID_ANY, u"Use Ctrl+Leftclick to select Point", wx.DefaultPosition, wx.DefaultSize, 0)
        text2.SetBackgroundColour("white")
        font = wx.Font(wx.FontInfo(13))
        text2.SetFont(font)
        text2.Wrap(-1)
        bsizer.Add(text2)

        self.SetSizer(bsizer)

        self.Layout()
        bsizer.Fit(self)

        self.statusbar.SetStatusText("%d" % (self.zoom,), 0)

        self.filename_dt = FileDrop(self)
        self.SetDropTarget(self.filename_dt)

        # wx.FutureCall(10, self.SetFocus)  # damit EVT_KEY_xx kommt
        wx.CallLater(10, self.SetFocus)  # damit EVT_KEY_xx kommt

    # ###########################################################
    # Wird aus FileDrop aufgerufen, wenn ein DateiObjekt auf dem
    # Fenster "fallengelassen" wurde.
    def fileDropped(self, filename):
        self.lstsLL = self.loadGPX(filename)
        # Format von self.lstsLL:
        #   [ [((lat, lon), time), ((lat, lon), time), ...],   - erster Track + Timestamps
        #     [((lat, lon), time), ((lat, lon), time), ...],   - zweiter Track + Timestamps
        #      ... ]

        tlLL = list()
        for l in self.lstsLL:  # alle Tracks in einer Liste ablegen, um Zoom-Level und Mittelpunkt zu bestimmen
            for pLL, t in l:
                tlLL.append(pLL)
        self.zoom, centerLL = self.osm.getZoomAndCenterForAllPointsVisible(tlLL)
        self.osm.setZoom(self.zoom, (0, 0))
        self.osm.setCenter(centerLL)
        self.initial_follow_pointLL = tlLL[0]
        self.statusbar.SetStatusText("%d" % (self.zoom,), 0)

        self.line_list = list()  # lat/lon-Tracks umwandeln in relative Pixel-Abstands-Listen
        for pLL in self.lstsLL:
            self.line_list.append(
                (pLL[0][0], self.convGPX2Pixel(pLL)))  # erstes Element ist LL, zweites ist Liste aus XY
            # Format von self.line_list:
            #   [ (base_posLL, [(xXY, yXY), (xXY, yXY), ...]),  - erster Track
            #     (base_posLL, [(xXY, yXY), (xXY, yXY), ...]),  - zweiter Track
            #     ... ]
        # solange der Zoom-Level nicht geändert wird, bleiben die Pixel-Abstände zwischen
        # den Punkten gültig - und der convGPX2Pixel() muss nicht bei jeder Karten-Verschiebung
        # neu aufgerufen werden. Lediglich der erste Punkt ist jeweils anzupassen.
        if len(self.lstsLL) > 0:
            self.pt1LL = self.lstsLL[0][0]  # Punkte zur Geschwindigkeitsbestimmung initialisieren
            self.pt0LL = self.pt1LL  # Format ist: ((lat, lon), UNIX-Timestamp)
        self.Refresh()

    # ######################################################################
    # GPX-Datei laden, parsen und als Liste von Tracks, bestehend aus Listen
    # von Tupeln ((lat, lon), Timestamp), zurückgeben.
    def loadGPX(self, filename):
        with open(filename, "r") as fl:
            filedata = fl.read()
        root = etree.fromstring(filedata)
        ns = ""
        if None in root.nsmap:
            ns = "{" + root.nsmap[None] + "}"
        tracks = list()
        if etree.iselement(root) and root.tag == ns + "gpx":
            for trk in root:
                track = list()
                if etree.iselement(trk) and trk.tag == ns + "trk":
                    for trkseg in trk:
                        if etree.iselement(trkseg) and trkseg.tag == ns + "trkseg":
                            for trkpt in trkseg:
                                if etree.iselement(trkpt) and trkpt.tag == ns + "trkpt":
                                    t = ""
                                    for e in trkpt:
                                        if etree.iselement(e) and e.tag == ns + "time":
                                            t = getTimestampStringAsUTC(e.text)
                                            break
                                    track.append(((float(trkpt.get("lat")), float(trkpt.get("lon"))), t))
                if len(track) > 0:
                    tracks.append(track)
        if len(tracks) > 0:
            self.file_loaded = True
        return (tracks)

    # ######################################################################
    # Einen geladenen GPX-Track von LL nach XY umwandeln.
    def convGPX2Pixel(self, lstLL):
        lstXY = list()
        for pLL, t in lstLL:
            lstXY.append(self.osm.getPixelForLatLon(pLL))
        return (lstXY)

    # ######################################################################
    # Fensterinhalt darstellen.
    def onPaint(self, evt):
        # wx.BeginBusyCursor()
        self.dc = wx.PaintDC(self)
        self.refresh_needed = self.osm.drawMap(self.dc)  # Karte darstellen

        self.dc.SetPen(wx.Pen("BLACK"))
        self.dc.SetBrush(wx.Brush("RED"))
        pXY = self.osm.getPixelForLatLon(self.centerLL)  # statischen Punkt anzeigen
        # self.dc.DrawCirclePoint(pXY, 5)

        if self.file_loaded:  # wenn GPX-Track geladen ist
            if self.zoom < 14:
                self.dc.SetPen(wx.Pen("MEDIUM VIOLET RED", width=4))
            else:
                self.dc.SetPen(wx.Pen("MEDIUM VIOLET RED", width=2))
            for bpLL, llXY in self.line_list:  # alle Tracks darin anzeigen
                delta = self.osm.getPixelForLatLon(bpLL)  # Basis-Koordinate holen
                ox, oy = delta[0] - llXY[0][0], delta[1] - llXY[0][1]  # Offset berechnen
                self.dc.DrawLines(llXY, ox, oy)  # Track mit Offset anzeigen
            if self.initial_follow_pointLL is not None:
                self.drawFollowPoint(self.osm.getPixelForLatLon(self.initial_follow_pointLL))

        if self.autofollow_running:  # wenn auto-follow läuft
            secs = self.pt1LL[1] - self.pt0LL[1]
            self.drawFollowPoint((self.dc_sizeXY[0] / 2, self.dc_sizeXY[1] / 2))
            self.dc.SetPen(wx.Pen("BLACK"))
            self.dc.SetBrush(wx.Brush("WHITE"))
            if secs > 0:
                txt = "%6.2f km/h " % (self.haversine(self.pt0LL[0], self.pt1LL[0]) / secs * 3600,)
            else:
                txt = " ??.?? km/h "
            w, h = self.dc.GetTextExtent(txt)
            x, y = (self.dc_sizeXY[0] / 2 + 5, self.dc_sizeXY[1] / 2 - h - 5)
            self.dc.DrawRectangle(x, y, w, h)
            self.dc.DrawText(txt, x, y)

        self.statusbar.SetStatusText(str(self.osm.getOpenRequests()), 1)
        # wx.EndBusyCursor()
        # wx.EndBusyCursor()  # doppelt hält besser - sonst bleibt manchmal der BusyCursor dauerhaft an

    # ######################################################################
    # Stellt für die Track-Anzeige den Startpunkt und bei Auto-Follow die
    # aktuelle Positionsmarkierung dar.
    def drawFollowPoint(self, posXY):
        self.dc.SetPen(wx.Pen("BLACK"))
        self.dc.SetBrush(wx.Brush("WHITE"))
        self.dc.DrawCirclePoint(posXY, 5)

    # ######################################################################
    # Linke Maustaste geklickt - Map scrollen.
    def onLeftDown(self, evt):
        self.leftDown = True
        self.was_moved = False
        self.leftDownPosXY = evt.GetPosition()
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.statusbar.SetStatusText("%dx%d" % (self.leftDownPosXY[0], self.leftDownPosXY[1]), 2)
        posLL = self.osm.getLatLonForPixel(self.leftDownPosXY)
        self.statusbar.SetStatusText("%14.12f, %14.12f" % (posLL[0], posLL[1]), 3)

    # ######################################################################
    # Linke Maustaste losgelassen - Map scrollen beenden.
    def onLeftUp(self, evt):
        self.leftDown = False
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        if self.was_moved:
            self.osm.endMoveMap()
            self.Refresh()
            # der Refresh() wird hier gebraucht, um nach einem Verschiebevorgang
            # außerhalb der vorgeladenen Rand-Tiles die fehlenden Tiles nachzuladen.

        if self.ctrlIsDown and not self.was_moved:
            posLL = self.osm.getLatLonForPixel(self.leftDownPosXY)
            self.bbox.extend(posLL)

            if len(self.bbox) == 2:
                self.text1.SetLabel("Select lower right bounding box coordinate")
                print("lol")
            if len(self.bbox) == 4:
                self.GetParent().GetParent().coordinates_from_map(self.bbox)
                evt.Skip()
                evt.StopPropagation()
                self.Close()

    # ######################################################################
    # Mauscursor wird über das Fenster bewegt.
    # Hier könnte man vielleicht noch einbauen, dass das Bild nicht jedesmal
    # neu berechnet wird.
    def onMotion(self, evt):
        self.cur_mouse_posXY = evt.GetPosition()
        if self.leftDown:
            self.was_moved = True
            scroll_distXY = self.leftDownPosXY - evt.GetPosition()
            self.osm.doMoveMap(scroll_distXY)
            self.Refresh()
            # print "getVisibleRectangle", self.osm.getVisibleRectangle()

    # ######################################################################
    # Scrollrad betätigt - Map ändern und ggf. Tracks neu von LL nach XY
    # umrechnen.
    def onMouseWheel(self, evt):
        zoom_old = self.zoom
        if evt.GetWheelRotation() > 0:
            self.zoom = min(SOURCE[SERVER]["max_zoom"], self.zoom + 1)
        else:
            self.zoom = max(0, self.zoom - 1)
        if self.zoom != zoom_old:
            self.osm.setZoom(self.zoom, evt.GetPosition())
            if self.file_loaded:
                self.line_list = list()
                for pLL in self.lstsLL:
                    self.line_list.append(
                        (pLL[0][0], self.convGPX2Pixel(pLL)))  # erstes Element ist LL, zweites ist Liste aus XY
            self.statusbar.SetStatusText("%d" % (self.zoom,), 0)
            self.Refresh()

    # ######################################################################
    # Fenstergröße wurde geändert - Variablen anpassen.
    def onSize(self, evt):
        self.dc_sizeXY = self.GetSize()
        try:
            self.osm.setSize(self.dc_sizeXY, self.zoom, self.border)
        except:
            pass  # der allererste EVT_SIZE kommt, bevor self.osm existiert

    # ######################################################################
    # Eine Taste wurde betätigt - ggf. auto-follow starten.
    def onKeyDown(self, evt):
        if evt.GetKeyCode() == wx.WXK_CONTROL:
            self.ctrlIsDown = True

        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.esc = True

        if evt.GetKeyCode() == ord("A"):
            print("a")
            self.autoFollow()
        evt.Skip(True)

    # ######################################################################
    # Eine Taste wurde losgelassen.
    def onKeyUp(self, evt):
        if evt.GetKeyCode() == wx.WXK_CONTROL:
            self.ctrlIsDown = False

        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.esc = False

        if evt.GetKeyCode() == ord("S"):
            self.superspeed = not self.superspeed

        if evt.GetKeyCode() == ord("Q"):
            self.osm.setCenter((54.805109, 9.524913))
            self.Refresh()
        evt.Skip(True)

    # ###########################################################
    # Ruft einmal pro Update-Intervall die Prüfung wegen Refresh
    # auf, um damit ggf. mittlerweile verfügbare Tiles anzuzeigen.
    def onTimer(self, evt):
        if self.refresh_needed:
            self.Refresh()

    # ######################################################################
    # Scrollt von der Geo-Koordinate "posFromLL" nach "posToLL" mit einer
    # Schrittgröße von "step_size" Pixeln und "delay" Sekunden Wartezeit
    # zwischen den Schritten.
    # Der Abstand der Koodinaten sollte in "self.border" passen, weil
    # zwischendurch keine Tiles nachgeladen werden.
    def scrollMapToPoint(self, posFromLL, posToLL, step_size, delay):
        p1XY = self.osm.getPixelForLatLon(posFromLL)
        p2XY = self.osm.getPixelForLatLon(posToLL)
        wXY = self.get_line(p1XY, p2XY)
        pcXY = wXY[0]
        for idx in range(1, len(wXY) - (step_size - 1), step_size):
            d = (wXY[idx][0] - pcXY[0], wXY[idx][1] - pcXY[1])
            self.osm.doMoveMap(d)
            self.Refresh()
            wx.Yield()
            if self.esc:
                break
            time.sleep(delay)
        self.osm.endMoveMap()
        self.osm.setCenter(posToLL)
        self.Refresh()
        wx.Yield()

    # ######################################################################
    # Fährt die geladenen Tracks ab.
    def autoFollow(self):
        if not self.file_loaded:
            return
        print("autoGPXfollow", len(self.line_list))
        self.autofollow_running = True
        delay = 0.01
        step_size = 8
        self.timer.Stop()
        self.initial_follow_pointLL = None
        for t in range(len(self.line_list)):  # über alle Tracks
            curLL = self.lstsLL[t][0]
            self.osm.setCenter(curLL[0])
            self.Refresh()
            for pLL, tl in self.lstsLL[t]:  # über alle (Punkte, Zeiten) des Tracks
                if pLL != curLL[0]:  # wenn Bewegung stattfand
                    self.pt1LL = (pLL, tl)  # Koordinaten+Zeit des aktuellen Punktes für onPaint()
                    if self.superspeed:
                        self.osm.setCenter(pLL)
                        self.Refresh()
                        wx.Yield()
                    else:
                        self.scrollMapToPoint(curLL[0], pLL, step_size, delay)
                    curLL = (pLL, tl)
                    self.pt0LL = curLL
                    self.statusbar.SetStatusText("%14.12f, %14.12f" % (pLL[0], pLL[1]), 3)
                else:
                    time.sleep(delay)
                self.statusbar.SetStatusText(str(datetime.fromtimestamp(tl)), 4)
                while self.osm.getOpenRequests() > 20:
                    time.sleep(0.2)
                    self.Refresh()
                    wx.Yield()
                if self.esc:
                    break
            self.pt1LL = None
            if self.esc:
                break
            self.Refresh()
        self.timer.Start(self.timer_interval)
        self.autofollow_running = False

    # ###########################################################
    # Get all points of a straight line.
    # Quelle: http://stackoverflow.com/a/25913345/3588613
    def get_line(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        points = []
        issteep = abs(y2 - y1) > abs(x2 - x1)
        if issteep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        rev = False
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            rev = True
        deltax = x2 - x1
        deltay = abs(y2 - y1)
        error = int(deltax / 2)
        y = y1
        ystep = None
        if y1 < y2:
            ystep = 1
        else:
            ystep = -1
        for x in range(x1, x2 + 1):
            if issteep:
                points.append((y, x))
            else:
                points.append((x, y))
            error -= deltay
            if error < 0:
                y += ystep
                error += deltax
        # Reverse the list if the coordinates were reversed
        if rev:
            points.reverse()
        return points

    # ######################################################################
    # Quelle: https://pypi.python.org/pypi/haversine
    # AVG_EARTH_RADIUS = 6371  - in km
    def haversine(self, point1, point2, miles=False):
        # unpack latitude/longitude
        lat1, lng1 = point1
        lat2, lng2 = point2

        # convert all latitudes/longitudes from decimal degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))

        # calculate haversine
        lat = lat2 - lat1
        lng = lng2 - lng1
        d = math.sin(lat * 0.5) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(lng * 0.5) ** 2
        h = 2 * 6371 * math.asin(math.sqrt(d))
        if miles:
            return h * 0.621371  # in miles
        else:
            return h  # in kilometers


# ###########################################################
# Der Fenster-Rahmen für das Hauptfenster.
class MapFrame(wx.Frame):
    def __init__(self, parent, centerLL, zoom, border, title, pos=wx.DefaultPosition, size=wx.DefaultSize):
        style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, parent, wx.ID_ANY, title + " " + VERSION, pos=pos, size=size, style=style)
        win = MapWindow(self, centerLL, zoom, border, title, size)

    def MakeModal(self, modal=True):
        if modal and not hasattr(self, '_disabler'):
            self._disabler = wx.WindowDisabler(self)
        if not modal and hasattr(self, '_disabler'):
            del self._disabler


# ######################################################################
# main()
if __name__ == "__main__":
    pt = (50.751947, 10.468694)
    app = wx.App(False)
    frame = MapFrame(None, pt, 6, (2, 2), "OpenStreetMapTest", size=(1280, 768 + 25))  # 5x3 Tiles + 25 für Statusbar
    frame.Show()
    app.MainLoop()
