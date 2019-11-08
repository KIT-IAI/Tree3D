# -*- coding: utf-8 -*-

# import wxPython classes
import wx
import wx.aui
import wx.lib.agw.aui as aui

# import project classes
import default_gui
import data


class MainTableFrame(default_gui.MainWindow):

    def __init__(self, parent):
        default_gui.MainWindow.__init__(self, parent)

        # create aui manager
        self.aui_manager = aui.AuiManager(self, wx.aui.AUI_MGR_DEFAULT)

        # initialize database
        self.db = data.Database()

        # Adding table view panel to Main Window
        self.table_view_panel = default_gui.data_panel(self)
        self.aui_manager.AddPane(self.table_view_panel, aui.AuiPaneInfo().CenterPane())
        self.table_view_panel.grid.Show(False)

    # method to be called when close buttn (x) is pushed
    def OnClose(self, event):
        dialog = wx.MessageDialog(self, message="Are you sure you would like to close ArbokaTransformer?",
                                  caption="Close Application", style=wx.YES_NO | wx.ICON_QUESTION,
                                  pos=wx.DefaultPosition)

        if dialog.ShowModal() == wx.ID_YES:
            self.on_exit_app()
        else:
            event.StopPropagation()
            dialog.Destroy()

    # defines actions to be taken when exiting the program
    def on_exit_app(self):
        self.db.close_db_connection()
        self.db.delete_db()
        self.Destroy()

    # method to be called when clicking File > Open
    def on_menu_open(self, event):
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.db.reset_database_table()
            self.db.import_csv_file(filepath=pathname)
        self.show_data_in_grid()

    # adjusts numbers of rows and columns to match data
    # populates grid with data afterwards
    def show_data_in_grid(self):
        # set number of rows and columns in grid
        col_number = self.db.get_column_number()
        row_number = self.db.get_number_of_tablerecords()
        self.table_view_panel.grid.InsertCols(pos=0, numCols=col_number)
        self.table_view_panel.grid.InsertRows(pos=0, numRows=row_number-1)

        # add column names to grid
        for idx, colname in enumerate(self.db.get_column_names()):
            self.table_view_panel.grid.SetColLabelValue(idx, colname)

        # fill grid with data
        data_table = self.db.get_data()
        for RowIdx, row in enumerate(data_table):
            for ColIdx, val in enumerate(row):
                self.table_view_panel.grid.SetCellValue(RowIdx, ColIdx, val)

        # Layout for the grid
        self.table_view_panel.grid.AutoSizeColumns(setAsMin=True)
        self.table_view_panel.grid.AutoSizeRows(setAsMin=True)

        # Make grid visible
        self.table_view_panel.grid.Show(True)

        # Update panel layout to fit new grid size
        self.table_view_panel.Layout()

        # write number of rows in statusbar
        self.m_statusBar3.SetStatusText("%s rows displayed in table" % row_number, 0)

    # method resets order of columns back to default
    def on_reset_column_position(self, event):
        self.table_view_panel.grid.ResetColPos()


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
