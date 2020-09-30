#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ###########################################################
# Eine Klasse zum Laden und cachen von OpenStreetMap-Tiles.
#
# Detlev Ahlgrimm, 2017
#
# Eine Erweiterungsmöglichkeit wäre die Abfrage des Erstellungsdatums von
# jedem Tile im Cache und Neuanforderung bei einem Alter >1 Jahr.
#
#
# 08.04.2017  erste Version
# 10.04.2017  Umstellung auf asynchrones Laden der Tiles
# 14.04.2017  self.status eingebaut, damit eine Unterscheidung zwischen
#             "laden unmöglich" und "laden fehlgeschlagen" erfolgen kann.


import wx  # python-wxWidgets-2.8.12.1-10.4.1.x86_64
from PIL import Image, ImageFile  # python-Pillow-2.8.1-3.6.1.x86_64
# leider taugen die Image-Funktionen von wxPython nix bzw. melden Bild-Fehler per Popup
import requests  # python-requests-2.4.1-3.1.noarch
from io import BytesIO
import os
import threading
from queue import Queue

DEBUG = False


class TileCache():
    def __init__(self, cache_base_dir, tile_url):
        self.cache_base_dir = cache_base_dir
        self.tile_url = tile_url
        self.queue = Queue()
        self.num_worker_threads = 35  # Anzahl Worker-Threads
        self.request_timeout = 3  # Maximal Wartezeit in Sekunden, bevor Ladevorgang abgebrochen wird
        self.already_requested = list()
        self.status = {"GOOD": 0, "WAIT": 1, "FAILED": 2, "INVALID": 3}
        for i in range(self.num_worker_threads):
            worker = threading.Thread(target=self.__getTileAsyncFromWeb, name="getTile(" + str(i) + ")")
            worker.setDaemon(True)
            worker.start()

    # ######################################################################
    # Liefert das OSM-Tile(x, y, z) mit Status als Bitmap oder None.
    def getTile(self, x, y, z):
        if self.queue.empty():  # wenn queue leer ist
            self.already_requested = list()  # ...können die alten Merker weg
        fldr = os.path.join(self.cache_base_dir, str(z), str(x))  # Pfad
        fl = os.path.join(fldr, "%d.png" % (y,))  # Tile-Name samt Pfad
        if os.path.exists(fl):  # wenn Tile schon im Cache existiert
            try:
                img = Image.open(fl)  # Tile aus Cache liefern
            except:
                return ((self.status["FAILED"], None))  # bei Fehler später nochmal probieren
        else:
            if (x, y, z) not in self.already_requested:  # wenn Anfrage für Tile noch nicht offen ist
                if x < 0 or x >= 2 ** z or y < 0 or y >= 2 ** z:  # wenn Tile nicht existiert bzw. illegal ist
                    # http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Zoom_levels
                    return ((self.status["INVALID"], None))  # als ungültiges Tile markieren
                self.queue.put((x, y, z))  # asynchrones Laden des Tiles beauftragen
                self.already_requested.append((x, y, z))  # und Auftrag merken, um ihn nur einmal abzusetzen
            return ((self.status["WAIT"], None))  # Nachlieferungs-Meldung
        try:
            image = img.convert('RGB')  # den convert() braucht der wx.BitmapFromBuffer()
        except:
            return ((self.status["FAILED"], None))  # wenn Fehlschlag - später nochmal probieren
        w, h = image.size  # Tile-Größe bestimmen
        bitmap = wx.Bitmap.FromBuffer(w, h, image.tobytes())  # nach Bitmap wandeln
        return ((self.status["GOOD"], bitmap))  # und zurückliefern

    # ######################################################################
    # Löscht alle anstehenden Requests, die nicht schon von einem
    # Worker-Thread angenommen wurden.
    def flushQueue(self):
        while not self.queue.empty():
            self.queue.get()
        self.already_requested = list()

    # ######################################################################
    # Liefert die Anzahl der noch anstehenden Requests, die nicht schon von
    # einem Worker-Thread angenommen wurden.
    def getQueueLength(self):
        return (self.queue.qsize())

    # ######################################################################
    # Liefert die Textstrings und Fehlernummern, die bei Fehler statt
    # Bitmaps geliefert werden können als Dictionary.
    def getStatusDict(self):
        return (self.status)

    # ######################################################################
    # Worker-Thread, um ein OSM-Tile zu laden und lokal zu speichern.
    def __getTileAsyncFromWeb(self):
        while True:
            job = self.queue.get()
            x, y, z = job
            s, img = self.__getTileFromWeb(x, y, z)
            if s == self.status["GOOD"]:
                fldr = os.path.join(self.cache_base_dir, str(z), str(x))
                fl = os.path.join(fldr, "%d.png" % (y,))
                try:
                    os.makedirs(fldr)
                except:
                    pass  # war wohl schon existent == macht nix
                try:
                    img.save(fl)
                except:
                    if DEBUG: print("Error img.save()\n")
                    pass
            self.queue.task_done()

    # ######################################################################
    # Das OSM-Tile(x, y, z) aus dem Web laden und samt Status zurückliefern.
    def __getTileFromWeb(self, x, y, z):
        if DEBUG: print("Web-request(%d,%d%d)\n" % (x, y, z))
        url = self.tile_url.format(z=z, x=x, y=y)

        try:
            response = requests.get(url, timeout=self.request_timeout)
        except:
            if DEBUG: print("Timeout(%d,%d%d)\n" % (x, y, z))
            return ((self.status["FAILED"], None))

        ImageFile.LOAD_TRUNCATED_IMAGES = True
        try:
            img = Image.open(BytesIO(response.content))
        except NameError:
            if DEBUG: print("Error in Image.open()\n")
            return ((self.status["FAILED"], None))
        return ((self.status["GOOD"], img))
