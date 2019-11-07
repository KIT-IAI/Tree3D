# -*- coding: utf-8 -*-

# import wxPython classes
import wx

# import project classes
import default_gui
import data


class MainTableFrame(default_gui.MainWindow):

    def __init__(self, parent):
        default_gui.MainWindow.__init__(self, parent)

        # initialize database:
        self.db = data.Database()

    def OnClose(self, event):
        dialog = wx.MessageDialog(self, message="Are you sure you would like to close ArbokaTransformer?",
                                  caption="Close Application", style=wx.YES_NO | wx.ICON_QUESTION,
                                  pos=wx.DefaultPosition)

        if dialog.ShowModal() == wx.ID_YES:
            self.on_exit_app()
        else:
            event.StopPropagation()
            dialog.Destroy()

    def on_exit_app(self):
        print("x gedrückt")
        self.db.close_db_connection()
        self.db.delete_db()
        self.Destroy()

    def on_menu_open(self, event):
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.db.reset_database_table()
            self.db.import_csv_file(filepath=pathname)


# create wxPython App
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
