# -*- coding: utf-8 -*-

# import python libraries
import xml.etree.ElementTree as ET

# import wxPython classes
import wx
import wx.aui
import wx.lib.agw.aui as aui
import wx.grid

# import project classes
import default_gui
import data
import analysis
import export


class MainTableFrame(default_gui.MainWindow):

    def __init__(self, parent):
        default_gui.MainWindow.__init__(self, parent)

        # create aui manager
        self.aui_manager = aui.AuiManager(self, wx.aui.AUI_MGR_DEFAULT)

        # initialize database
        self.db = None

        # Adding table view panel to Main Window
        self.table_view_panel = default_gui.data_panel(self)
        self.aui_manager.AddPane(self.table_view_panel, aui.AuiPaneInfo().CenterPane())
        self.table_view_panel.grid.Show(False)

        # Binding further events
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_grid_lable_right_click)  # event: r-clicking grid label
        self.table_view_panel.grid.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel_in_grid)  # event: scrol-wheel in grid

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
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv|XML files (*.xml)|*.xml",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()

            self.reset_program()

            # opening procedure when a csv file is detected
            if pathname[-4:] == ".csv":
                self.db = data.DatabaseFromCsv()
                dlg = OpenDialogCSV(self, path=pathname)
                dlg.Layout()
                dlg.DoLayoutAdaptation()
                dlg.ShowModal()
                import_success, warntext = self.db.import_csv_file(filepath=pathname)

            # opening procedure when xml file is detected
            elif pathname[-4:] == ".xml":
                tree = None
                text = "XML File will be parsed now.\n" \
                       "This might take some time for larger files."
                msg = wx.MessageDialog(self, text, style=wx.OK | wx.CENTRE)
                msg.ShowModal()

                # parse xml Tree. Show warning and abort if file cant be parsed
                success = True
                try:
                    tree = ET.parse(pathname)
                    text = "XML file parsed successfully"
                except ET.ParseError:
                    success = False
                    text = "Cannot parse input file.\nIt is most likely not a valid xml file."
                except FileNotFoundError:
                    success = False
                    text = "Cannot parse input file.\nCannot find file or directory."
                except:
                    success = False
                    text = "Cannot parse input file for unknown reason"
                finally:
                    if not success:
                        msg = wx.MessageDialog(self, text, style=wx.OK | wx.CENTRE)
                        msg.ShowModal()
                        return

                self.db = data.DatabaseFromXml()
                dlg = OpenDialogXML(self, pathname, tree)
                dlg.ShowModal()
                treepath = dlg.treepath.GetValue()
                geompath = dlg.geompath.GetValue()
                ignore = dlg.ignorelist.GetValue()
                self.db.import_xml_file(pathname, treepath, geompath, ignore, tree)

        self.show_data_in_grid(self.db.get_number_of_columns(), self.db.get_number_of_tablerecords(), self.db.get_data())

        # Enable menu items
        self.export_citygml.Enable(True)
        self.col_properties.Enable(True)
        self.reset_col_position.Enable(True)
        self.reset_col_visiblity.Enable(True)
        self.stats.Enable(True)
        self.dublicates.Enable(True)
        self.duplicateGeom.Enable(True)

    # method to be called when File > Export as CityGML is pressed
    def on_menu_export_citygml(self, event):
        exp = export.ExportDialog(self)

    # method to reset program to a state similar to after startup
    # needed for example when a file was opened already and a new file will now be opened
    def reset_program(self):
        # Disable menu items
        self.export_citygml.Enable(False)
        self.col_properties.Enable(False)
        self.reset_col_position.Enable(False)
        self.reset_col_visiblity.Enable(False)
        self.stats.Enable(False)
        self.dublicates.Enable(False)
        self.duplicateGeom.Enable(False)

        # Disable Grid visibility
        self.table_view_panel.grid.Show(False)

        # reset grid size to 0 cols and 0 rows
        self.reset_grid_size()

        # deletes database table (if exists) so new file can be imported
        if self.db is not None:
            self.db.reset_database_table()
            self.db.close_db_connection()

            # resets options: By default, no ID is created
            self.db.set_create_id(False)
            self.db.set_id_columns([])

        # resets row count in status bar
        self.m_statusBar3.SetStatusText("", 0)

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
                # show empty cell if database delivers None object
                if val is None:
                    val = ''

                # yellow for first col if it is generated
                if ColIdx == 0 and self.db.get_create_id():
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

    # returns a list of integers, showing the order of grid columns
    # list is ordered by column ID
    def get_all_col_position(self):
        pos_list = []
        for idx in range(0, self.table_view_panel.grid.GetNumberCols()):
            pos_list.append(self.table_view_panel.grid.GetColAt(idx))
        return pos_list

    # returns a list indicating which grid columns are visible and which are not
    # True, if column is visible, False, if column is not hidden
    # List ordered by column ID
    def get_all_col_visiblity(self):
        visibility_list = []
        for idx in range(0, self.table_view_panel.grid.GetNumberCols()):
            visibility_list.append(self.table_view_panel.grid.IsColShown(idx))
        return visibility_list

    # method to be called when right clicking a grid label
    def on_grid_lable_right_click(self, event):
        # ignore events by row labels, only consider column labels
        col_pos = event.GetCol()
        if col_pos < 0:
            return

        # create context menu for column label right-click
        contextmenu = wx.Menu()
        hide_col = wx.MenuItem(contextmenu, wx.ID_ANY, "Hide Column")
        sort_col_asc = wx.MenuItem(contextmenu, wx.ID_ANY, "Sort grid by column ascending")
        sort_col_desc = wx.MenuItem(contextmenu, wx.ID_ANY, "Sort grid by column descending")
        contextmenu.Append(hide_col)
        contextmenu.AppendSeparator()
        contextmenu.Append(sort_col_asc)
        contextmenu.Append(sort_col_desc)

        # add event to context menu item "hide column"
        self.Bind(wx.EVT_MENU, lambda _: self.on_hide_column(col_pos), id=hide_col.GetId())
        self.Bind(wx.EVT_MENU, lambda _: self.on_sort_col_asc(col_pos), id=sort_col_asc.GetId())
        self.Bind(wx.EVT_MENU, lambda _: self.on_sort_col_desc(col_pos), id=sort_col_desc.GetId())
        self.PopupMenu(contextmenu)
        contextmenu.Destroy()

    # method to be called when mouse wheel is used within grid.
    # enables scrolling with mouse wheel
    def on_mouse_wheel_in_grid(self, event):
        # scroll either up or down, depending on mouse wheel direction
        if event.GetWheelRotation() < 0:
            self.table_view_panel.grid.ScrollLines(2)
        else:
            self.table_view_panel.grid.ScrollLines(-2)

    # method is called when right-clicking a column label > "hide column"
    def on_hide_column(self, col):
        self.table_view_panel.grid.HideCol(col)

    # method is called when right-clicking a column label > "sort grid by column ascending"
    def on_sort_col_asc(self, col):

        # if the list is already sorted ascending by this column, dont do anything
        if self.table_view_panel.grid.GetColLabelValue(col)[-1:] == "▲":
            return

        # BUG IN wxPython LIBRARY:
        # when position of first column was altered, program crashes during restoration of position later
        # workaround: manually reset position of this column now, manually restore this position later
        first_col_moved = False
        first_col_position = self.table_view_panel.grid.GetColPos(0)
        if self.table_view_panel.grid.GetColPos(0) != 0:
            self.table_view_panel.grid.SetColPos(0, 0)
            first_col_moved = True

        # get current order and visibility of columns
        col_order = self.get_all_col_position()
        col_visiblity = self.get_all_col_visiblity()

        # remove possible column sort indicators from column header
        self.remove_col_sort_indicator()

        # get column label from right-column
        col_label = self.table_view_panel.grid.GetColLabelValue(col)

        # query database, sorts result by column
        sorted_data = self.db.get_data_with_sorting('ORDER BY "%s" ASC' % col_label)

        # display fetched data in grid
        number_of_cols = self.table_view_panel.grid.GetNumberCols()
        number_of_rows = self.table_view_panel.grid.GetNumberRows()
        self.show_data_in_grid(number_of_cols, number_of_rows, sorted_data)

        # update column label: append sorting indicator
        col_label_new = col_label + " ▲"
        self.table_view_panel.grid.SetColLabelValue(col, col_label_new)
        self.table_view_panel.grid.AutoSizeColumns(setAsMin=True)

        # restores order of grid columns (was lost while adding newly fetched data to grid)
        self.table_view_panel.grid.SetColumnsOrder(col_order)

        # due to library bug mentioned above: reset column position for first column manually
        if first_col_moved:
            self.table_view_panel.grid.SetColPos(0, first_col_position)

        # restores visibility for grid columns (was lost while adding newly fetched data to grid)
        for idx, value in enumerate(col_visiblity):
            if not value:
                self.table_view_panel.grid.HideCol(idx)

    # method is called when right-clicking a column label > "sort grid by column descending
    def on_sort_col_desc(self, col):
        # method is very similar to method "on_sort_col_asc".
        # see "on_sort_col_asc" for documentation
        if self.table_view_panel.grid.GetColLabelValue(col)[-1:] == "▼":
            return

        first_col_moved = False
        first_col_position = self.table_view_panel.grid.GetColPos(0)
        if self.table_view_panel.grid.GetColPos(0) != 0:
            self.table_view_panel.grid.SetColPos(0, 0)
            first_col_moved = True

        col_order = self.get_all_col_position()
        col_visiblity = self.get_all_col_visiblity()

        self.remove_col_sort_indicator()

        col_label = self.table_view_panel.grid.GetColLabelValue(col)

        sorted_data = self.db.get_data_with_sorting('ORDER BY "%s" DESC' % col_label)

        number_of_cols = self.table_view_panel.grid.GetNumberCols()
        number_of_rows = self.table_view_panel.grid.GetNumberRows()
        self.show_data_in_grid(number_of_cols, number_of_rows, sorted_data)

        col_label_new = col_label + " ▼"
        self.table_view_panel.grid.SetColLabelValue(col, col_label_new)
        self.table_view_panel.grid.AutoSizeColumns(setAsMin=True)

        self.table_view_panel.grid.SetColumnsOrder(col_order)

        if first_col_moved:
            self.table_view_panel.grid.SetColPos(0, first_col_position)

        for idx, value in enumerate(col_visiblity):
            if not value:
                self.table_view_panel.grid.HideCol(idx)

    # method is used to remove column sort indicators (little triangles) from grid
    def remove_col_sort_indicator(self):
        for col_idx in range(0, self.table_view_panel.grid.GetNumberCols()-1):
            col_label = self.table_view_panel.grid.GetColLabelValue(col_idx)
            if col_label[-1:] == "▲" or col_label[-1:] == "▼":
                self.table_view_panel.grid.SetColLabelValue(col_idx, col_label[:-2])

    # method is called when hitting Analyze > Check for duplicate IDs
    def on_check_for_duplicates_ID(self, event):
        dlg = analysis.CheckDuplicateId(self)
        dlg.ShowModal()

    # Method to be called when Analyze > Check for duplicates by Geom is pressed
    def on_check_for_duplicates_geom(self, event):
        dlg = analysis.CheckDuplicateGeom(self)
        dlg.ShowModal()

    # method to be called when clicking File > Test
    # overrides method in parent class
    # LOESCHEN VOR ABGABE
    def on_menu_test(self, event):
        print("Test")


# DialogBox with options to open file
class OpenDialog(default_gui.OnOpenDialog):
    def __init__(self, parent, path):
        default_gui.OnOpenDialog.__init__(self, parent)
        self._filepath = path

    # method to be called when clicking OK in dialog
    # overrides method in parent dialog
    def on_ok(self, event):
        valid, warningtext = self.validate()

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

    # Method to validate user input in this window
    # returns True if user input is valid
    # Returns False if user input is invalid and prevents database import
    def validate(self):
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

        return valid, warningtext


class OpenDialogCSV(OpenDialog):
    def __init__(self, parent, path):
        super().__init__(parent, path)
        self.populate_dropdown()

        # Hide xml-related stuff
        self.m_staticText22.Show(False)
        self.treepath.Show(False)
        self.m_staticline1.Show(False)
        self.m_staticText23.Show(False)
        self.geompath.Show(False)
        self.m_staticline2.Show(False)
        self.m_staticText24.Show(False)
        self.ignorelist.Show(False)
        self.m_staticline3.Show(False)

    # method to populate columns of dropdown menus with column headers
    def populate_dropdown(self):
        # try to figure out file encoding: first try to open with utf-8, if that fails with cp1252
        # if neither file encoding works: show error message
        warningtext = ""
        try:
            with open(self._filepath, newline='', encoding='utf-8') as file:
                header = file.readline()
                self.GetParent().db.set_file_encoding("utf-8")
        except UnicodeDecodeError:
            try:
                with open(self._filepath, newline='', encoding='cp1252') as file:
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


class OpenDialogXML(OpenDialog):
    def __init__(self, parent, path, tree):
        super().__init__(parent, path)
        self.SetTitle("XML import options")
        self.__Tree = tree
        self.__ns = dict([node for _, node in ET.iterparse(self._filepath, events=['start-ns'])])
        self.__Root = self.__Tree.getroot()

    # Populates dropdown menus after xml was opened
    def populate_dropdown(self):
        check_number = 100

        # Create list with elements to ignore from string.
        # Format list: Remove leading and tailing whitespaces
        ignorelist = self.ignorelist.GetValue().split(";")
        for idx, element in enumerate(ignorelist):
            ignorelist[idx] = element.strip()

        # Inspect data: Find Columns to add to database table
        # Find data type of each column
        inspected_cols = []
        for count, element in enumerate(self.__Root.findall(self.treepath.GetValue(), self.__ns)):
            if count > check_number:
                break
            for subelement in element:
                tag = subelement.tag
                tag_no_pref = tag.split("}")[1]
                if (tag_no_pref not in ignorelist) and (tag_no_pref not in inspected_cols):
                    inspected_cols.append(tag_no_pref)

        self.id_col1.SetItems(inspected_cols)
        self.id_col2.SetItems(inspected_cols)

    # method is called when checkbox is triggered
    def id_checkbox_event(self, event):
        super().id_checkbox_event(event)
        if self.generate_ID_box.GetValue():

            # dont create ID if xml pathes are not correct yet
            if not self.validate_xml_geom_path():
                # Un-Check checkbox
                self.generate_ID_box.SetValue(False)

                # disable UI elements again
                self.id_col1.Enable(not self.id_col1.Enabled)
                self.id_col2.Enable(not self.id_col2.Enabled)
                self.IdText_Col1.Enable(not self.IdText_Col1.Enabled)
                self.IdText_Col2.Enable(not self.IdText_Col2.Enabled)

                warningtext = "XML path to tree coordinates is not correct.\n" \
                              "Must be a correct path to fetch column names.\n" \
                              "Please specify a correct path first."
                msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
                msg.ShowModal()
                return
            self.populate_dropdown()

    # Validates user input
    # Returns True, if User input is valid
    # Returns False, if User input is incorrect and prevents database import
    def validate(self):
        valid, warningtext = super().validate()
        if not self.validate_xml_geom_path():
            valid = False
            warningtext = "XML path to tree coordinates is not correct."
        if not self.validate_xml_attribute_path():
            valid = False
            warningtext = "XML path to tree attributes is not correct."
        return valid, warningtext

    # method to be called when text in treepath changes
    def on_xml_attribut_path_text_change( self, event ):
        attribute_path_isvalid = self.validate_xml_attribute_path()

        # Set background color to a light green if input is a valid xml path
        if attribute_path_isvalid:
            self.treepath.SetBackgroundColour(wx.Colour(113, 218, 113))
            self.treepath.Refresh(False)
        # Set background color to a light red if input is not a valid xml path
        else:
            self.treepath.SetBackgroundColour(wx.Colour(255, 128, 128))
            self.treepath.Refresh(False)

    # method to be called when text in geompath changes
    def on_xml_geom_path_text_change( self, event ):
        attribute_path_isvalid = self.validate_xml_geom_path()

        # Set background color to a light green if input is a valid xml path
        if attribute_path_isvalid:
            self.geompath.SetBackgroundColour(wx.Colour(113, 218, 113))
            self.geompath.Refresh(False)
        # Set background color to a light red if input is not a valid xml path
        else:
            self.geompath.SetBackgroundColour(wx.Colour(255, 128, 128))
            self.geompath.Refresh(False)

    # validates treepath, returns True if valid / False if invalid
    def validate_xml_attribute_path(self):
        valid = False
        if self.__Root.findall(self.treepath.GetValue(), self.__ns):
            valid = True
        return valid

    # validates geompath, returns True if valid / False if invalid
    def validate_xml_geom_path(self):
        valid = False
        if self.__Root.findall(self.treepath.GetValue() + self.geompath.GetValue()[1:], self.__ns):
            valid = True
        return valid


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
