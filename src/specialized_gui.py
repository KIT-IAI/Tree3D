# -*- coding: utf-8 -*-

# import python standard library classes
import uuid
import sys

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
    # overrides method in parent class
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
    # overrides method in parent class
    def on_menu_open(self, event):
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()

            self.reset_program()

            dlg = OpenDialog(self, path=pathname)
            dlg.ShowModal()

            self.db.import_csv_file(filepath=pathname)
        self.show_data_in_grid(self.db.get_number_of_columns(), self.db.get_number_of_tablerecords(), self.db.get_data())

    def reset_program(self):
        # Disable Grid visibility
        self.table_view_panel.grid.Show(False)

        # reset grid size to 0 cols and 0 rows
        self.reset_grid_size()

        # deletes database table (if exists) so new file can be imported
        self.db.reset_database_table()

        # resets row count in status bar
        self.m_statusBar3.SetStatusText("", 0)

        # resets options: By default, no ID is created
        self.db.set_create_id(False)
        self.db.set_id_columns([])

    # adjusts numbers of rows and columns to match data
    # populates grid with data afterwards
    def show_data_in_grid(self, col_number, row_number, data_table):
        self.reset_grid_size()

        # set number of rows and columns in grid
        self.table_view_panel.grid.InsertCols(pos=0, numCols=col_number)
        self.table_view_panel.grid.InsertRows(pos=0, numRows=row_number)

        # add column names to grid
        for idx, colname in enumerate(self.db.get_column_names()):
            self.table_view_panel.grid.SetColLabelValue(idx, colname)

        # fill grid with data
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

    # resets size of grid to 0 columns and 0 rows
    # Deletes all columns and rows of grid, so new data can be displayed properly
    # rows and columns can only be deleted if their number is not null (on program start)
    def reset_grid_size(self):
        try:
            self.table_view_panel.grid.DeleteRows(pos=0, numRows=self.table_view_panel.grid.GetNumberRows())
        except wx._core.wxAssertionError:
            pass
        try:
            self.table_view_panel.grid.DeleteCols(pos=0, numCols=self.table_view_panel.grid.GetNumberCols())
        except wx._core.wxAssertionError:
            pass

    # method resets order of columns back to default
    # overrides method in parent class
    def on_reset_column_position(self, event):
        self.table_view_panel.grid.ResetColPos()

    # method to be called when clicking View > Show all columns: restores visibility of all columns
    # overrides method in parent class
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

    # method to be called when right-clicking a column label and clicking "hide column"
    def on_hide_column(self, col):
        self.table_view_panel.grid.HideCol(col)

    # method to be called when clicking File > Test
    # overrides method in parent class
    def on_menu_test(self, event):
        print("Test")

    def on_check_for_duplicates_ID(self, event):
        dlg = CheckDuplicateId(self)
        dlg.ShowModal()


# DialogBox with options to open file
class OpenDialog(default_gui.OnOpenDialog):
    def __init__(self, parent, path):
        default_gui.OnOpenDialog.__init__(self, parent)
        self.__filepath = path

        self.populate_dropdown()

    # method to populate columns of dropdown menus with column headers
    def populate_dropdown(self):
        # try to figure out file encoding: first try to open with utf-8, if that fails with cp1252
        # if neither file encoding works: show error message
        warningtext = ""
        try:
            with open(self.__filepath, newline='', encoding='utf-8') as file:
                header = file.readline()
                self.GetParent().db.set_file_encoding("utf-8")
        except UnicodeDecodeError:
            try:
                with open(self.__filepath, newline='', encoding='cp1252') as file:
                    header = file.readline()
                    self.GetParent().db.set_file_encoding("cp1252")
            except:
                warningtext = "Unknown Error: Cannot open file!\n" \
                              "Maybe file encoding is not supported\n" \
                              "File encoding must be either utf-8 or cp1252!"
                msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_ERROR)
                msg.ShowModal()
                self.Destroy()
                return
        except:
            warningtext = "Unknown Error: Cannot open file!\n" \
                          "Maybe file encoding is not supported\n" \
                          "File encoding must be either utf-8 or cp1252!"
            msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_ERROR)
            msg.ShowModal()
            self.Destroy()
            return

        header = header.strip("\r\n")
        l_cols = header.split(";")
        self.id_col1.SetItems(l_cols)
        self.id_col2.SetItems(l_cols)

    # method to be called when checkbox event for generate-id-checkbox is triggered
    # every time the checkbox is clicked
    # overrides method in parent class
    def id_checkbox_event(self, event):
        self.id_col1.Enable(not self.id_col1.Enabled)
        self.id_col2.Enable(not self.id_col2.Enabled)
        self.IdText_Col1.Enable(not self.IdText_Col1.Enabled)
        self.IdText_Col2.Enable(not self.IdText_Col2.Enabled)

    # method to be called when clicking OK in dialog
    # overrides method in parent dialog
    def on_ok(self, event):
        valid = True  # variable to determine if user input is correct
        warningtext = ""  # Text to display in error window if user input is incorrect

        # checks if input to generate IDs is correct, if generate-id-checkbox is activated
        if self.generate_ID_box.GetValue():
            # checks if both ID column dropdowns have values
            if self.id_col1.GetSelection() == wx.NOT_FOUND or self.id_col2.GetSelection() == wx.NOT_FOUND:
                valid = False
                warningtext = "Cannot generate IDs. Please select two different table columns for ID generation"
            # checks if both ID column dropdowns have the same value
            if self.id_col1.GetSelection() == self.id_col2.GetSelection():
                valid = False
                warningtext = "Cannot generate IDs. Please select two different table columns for ID generation"

        # if input is valid, do stuff
        if valid:
            # change settings in data module to generate IDs if generate-id-checkbox is activated
            if self.generate_ID_box.GetValue():
                self.GetParent().db.set_create_id(True)
                self.GetParent().db.set_id_columns([self.id_col1.GetSelection(), self.id_col2.GetSelection()])
            self.Destroy()
        # show error message, if input is not valid
        else:
            msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()


# DialogBox to check for duplicate elements in data by ID
class CheckDuplicateId(default_gui.OnCheckDuplicateIdDialog):
    def __init__(self, parent):
        default_gui.OnCheckDuplicateIdDialog.__init__(self, parent)
        self.populate_dropdown()

    # method to populate dropdown with (id) columns in dialogbox
    def populate_dropdown(self):
        colitemlist = self.GetParent().db.get_column_names()
        self.IdColumns.SetItems(colitemlist)

    # method to be executed when hitting Analyze Button in DialogBox
    # Checks if data contains duplicate IDs, validates UUIDs
    # overrides method in parent class
    def on_analyze(self, event):
        # exit method if no selection has been made in dropdown
        if self.IdColumns.GetSelection() == wx.NOT_FOUND:
            warningtext = "Please select ID column to analyze for duplicates"
            msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()
            return

        # hide result text and result grid
        self.InfoTextUUID.Hide()
        self.UUIDGrid.Hide()
        self.InfoTextDuplicate.Hide()
        self.DuplicateGrid.Hide()

        # Delete rows from grid to reset to 0
        try:
            self.DuplicateGrid.DeleteRows(pos=0, numRows=self.DuplicateGrid.GetNumberRows())
        except:
            pass
        try:
            self.UUIDGrid.DeleteRows(pos=0, numRows=self.UUIDGrid.GetNumberRows())
        except:
            pass

        itemindex = self.IdColumns.GetSelection()  # index of selected column
        itemcolname = self.IdColumns.GetString(itemindex)  # name of selected column
        collist = [itemcolname]  # name of column but in a list

        # displays selected column name in column labels of grids
        self.DuplicateGrid.SetColLabelValue(0, itemcolname)
        self.DuplicateGrid.SetColLabelValue(1, "#")
        self.UUIDGrid.SetColLabelValue(0, itemcolname)

        # performs a selection for every value to be checkt with WHERE clause
        # check_value: all distinct values of one column
        duplicate_counter = 0
        uuid_counter = 0
        for check_value in self.GetParent().db.get_data_by_collist_distinct(collist):
            dat = self.GetParent().db.get_data_with_condition('WHERE "%s" = "%s"' % (itemcolname, check_value[0]))

            # if query returns >1 rows (e.g. two entries with one ID), add values to grid
            if len(dat) > 1:
                self.DuplicateGrid.AppendRows(1)
                self.DuplicateGrid.SetCellValue(duplicate_counter, 0, str(check_value[0]))
                self.DuplicateGrid.SetCellValue(duplicate_counter, 1, str(len(dat)))
                duplicate_counter += 1
            # perform uuid validation if uuid-checkbox was activated
            if self.UUIDCheck.GetValue():
                try:
                    uuid.UUID('{%s}' % check_value[0])
                except ValueError:
                    # add UUID to grid if invalid
                    self.UUIDGrid.AppendRows(1)
                    self.UUIDGrid.SetCellValue(uuid_counter, 0, str(check_value[0]))
                    uuid_counter += 1

        # change info message if no duplicates have been found
        # otherwise: show grid with duplicates
        if duplicate_counter == 0:
            self.InfoTextDuplicate.SetLabel("Check for duplicates completed.\nNo duplicates have been found")
        else:
            self.DuplicateGrid.Show(True)
        self.InfoTextDuplicate.Show(True)

        # change info message if no invalid uuid was found
        # otherwise: show grid with invalid uuids
        if self.UUIDCheck.GetValue():
            if uuid_counter == 0:
                self.InfoTextUUID.SetLabel("UUID-Validation completed.\nNo invalid UUIDs found")
            else:
                self.UUIDGrid.Show(True)
            self.InfoTextUUID.Show(True)

        self.Layout()


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
