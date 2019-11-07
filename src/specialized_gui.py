# -*- coding: utf-8 -*-

# import wxPython classes
import wx

# import project classes
import default_gui
import data


class MainTableFrame(default_gui.MainWindow):

    def __init__(self, parent):
        default_gui.MainWindow.__init__(self, parent)

    def on_menu_open(self, event):
        print("selected open")
        db = data.Database()
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            db.import_csv_file(filepath=pathname)
            print("import completed")
        db.close_db_connection()


# wxPython App erzeugen
class MyApp(wx.App):
    def OnInit(self):
        # create instance of MainTableFrame
        self.frame = MainTableFrame(None)

        self.SetTopWindow(self.frame)
        self.frame.Show(True)
        return True


if __name__ == "__main__":
    app = MyApp(redirect=False)  # do not redirect stdout to the gui
    app.MainLoop()  # render gui continuously
