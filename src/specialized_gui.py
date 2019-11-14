# -*- coding: utf-8 -*-

# import wxPython classes
import wx
import wx.aui
import wx.lib.agw.aui as aui
import wx.grid

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

        # Binding further events
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_grid_lable_right_click)

    # method to be called when close button (x) is pushed
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

            # Disable Grid visibility
            self.table_view_panel.grid.Show(False)

            # Deletes all columns and rows of grid, so a new file can be displayed properly
            # rows and columns can only be deleted if their number is null (on program start)
            try:
                self.table_view_panel.grid.DeleteRows(pos=0, numRows=self.db.get_number_of_tablerecords())
            except:
                pass
            try:
                self.table_view_panel.grid.DeleteCols(pos=0, numCols=self.db.get_number_of_columns())
            except:
                pass

            # deletes database table (if exists) so new file can be imported
            self.db.reset_database_table()

            # resets options: By default, no ID is created
            self.db.set_create_id(False)
            self.db.set_id_columns([])

            dlg = OpenDialog(self, path=pathname)
            dlg.ShowModal()

            self.db.import_csv_file(filepath=pathname)
        self.show_data_in_grid()

    # adjusts numbers of rows and columns to match data
    # populates grid with data afterwards
    def show_data_in_grid(self):
        # set number of rows and columns in grid
        col_number = self.db.get_number_of_columns()
        row_number = self.db.get_number_of_tablerecords()
        self.table_view_panel.grid.InsertCols(pos=0, numCols=col_number)
        self.table_view_panel.grid.InsertRows(pos=0, numRows=row_number)

        # add column names to grid
        for idx, colname in enumerate(self.db.get_column_names()):
            self.table_view_panel.grid.SetColLabelValue(idx, colname)

        # fill grid with data
        data_table = self.db.get_data()
        for RowIdx, row in enumerate(data_table):
            for ColIdx, val in enumerate(row):
                if ColIdx == 0:
                    if self.db.get_create_id():
                        self.table_view_panel.grid.SetCellBackgroundColour(RowIdx, ColIdx, wx.Colour(255, 255, 128))
                self.table_view_panel.grid.SetCellValue(RowIdx, ColIdx, str(val))

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

    # method to be called when clicking View > Show all columns: restores visibility of all columns
    def on_show_all_columns(self, event):
        for i in range(0, self.db.get_number_of_columns(), 1):
            self.table_view_panel.grid.ShowCol(i)

    # method to be called when right clicking a grid label
    def on_grid_lable_right_click(self, event):
        # ignore events by row labels, only consider column labels
        col_pos = event.GetCol()
        if col_pos < 0:
            return

        # create context menu
        contextmenu = wx.Menu()
        hide_col = wx.MenuItem(contextmenu, wx.ID_ANY, "Hide Column")
        contextmenu.Append(hide_col)

        # add event to context menu item "hide column"
        self.Bind(wx.EVT_MENU, lambda _: self.on_hide_column(col_pos), id=hide_col.GetId())
        self.PopupMenu(contextmenu)
        contextmenu.Destroy()

    def on_hide_column(self, col):
        self.table_view_panel.grid.HideCol(col)

    def on_menu_test(self, event):
        print("Test")


class OpenDialog(default_gui.OnOpenDialog):
    def __init__(self, parent, path):
        default_gui.OnOpenDialog.__init__(self, parent)
        self.__filepath = path

        self.fill_dropdowns()

    def fill_dropdowns(self):
        with open(self.__filepath, newline='', encoding='utf-8-sig') as file:
            header = file.readline()
        header = header.strip("\r\n")
        l_cols = header.split(";")
        self.id_col1.SetItems(l_cols)
        self.id_col2.SetItems(l_cols)
        self.guid_col.SetItems(l_cols)

    def id_checkbox_event(self, event):
        self.id_col1.Enable(not self.id_col1.Enabled)
        self.id_col2.Enable(not self.id_col2.Enabled)
        self.IdText_Col1.Enable(not self.IdText_Col1.Enabled)
        self.IdText_Col2.Enable(not self.IdText_Col2.Enabled)

    def guid_checkbox_event(self, event):
        self.guid_text.Enable(not self.guid_text.Enabled)
        self.guid_col.Enable(not self.guid_col.Enabled)

    def on_ok(self, event):
        if self.generate_ID_box.GetValue():
            self.GetParent().db.set_create_id(True)
            self.GetParent().db.set_id_columns([self.id_col1.GetSelection(), self.id_col2.GetSelection()])
        self.Destroy()


# create wxPython App
class MyApp(wx.App):
    def OnInit(self):
        # create instance of MainTableFrame
        frame = MainTableFrame(None)

        self.SetTopWindow(frame)
        frame.Show(True)
        return True


if __name__ == "__main__":
    app = MyApp(redirect=False)  # do not redirect stdout to the gui
    app.MainLoop()  # render gui continuously
