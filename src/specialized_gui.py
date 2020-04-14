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
import enrichment


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
        dialog = wx.MessageDialog(self, message="Are you sure you would like to close tree3d?",
                                  caption="Close Application", style=wx.YES_NO | wx.ICON_QUESTION,
                                  pos=wx.DefaultPosition)

        if dialog.ShowModal() == wx.ID_YES:
            self.on_exit_app()
        else:
            event.StopPropagation()
            dialog.Destroy()

    # defines actions to be taken when exiting the program
    def on_exit_app(self):
        self.aui_manager.UnInit()
        if self.db is not None:
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
                import_success = None
                text = ""
                try:
                    import_success = self.db.import_csv_file(filepath=pathname)
                    text = "CSV file imported successfully"
                except UnicodeDecodeError:
                    import_success = False
                    text = "CSV file import failed.\n" \
                           "File encoding not correct"
                except data.NotEnoughItemsException as e:
                    import_success = False
                    text = "Error in %s: Less items in line than table headers" % (str(e))
                except data.TooManyItemsException as e:
                    import_success = False
                    text = "Error in %s: More items in Line than table headers" % str(e)
                except:
                    import_success = False
                    text = "CSV file import failed for unknown reason\n" \
                           "Is the seperator set correctly?"
                finally:
                    icon = wx.OK
                    if not import_success:
                        icon = wx.ICON_WARNING
                    msg = wx.MessageDialog(self, text, style=icon | wx.CENTRE)
                    msg.ShowModal()
                    if not import_success:
                        return

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
                    text = "Cannot parse input file for unknown reason" \
                           "Is the seperator set correctly?"
                finally:
                    if not success:
                        msg = wx.MessageDialog(self, text, style=wx.OK | wx.CENTRE)
                        msg.ShowModal()
                        return

                self.db = data.DatabaseFromXml()
                dlg = OpenDialogXML(self, pathname, tree)
                dlg.Layout()
                dlg.DoLayoutAdaptation()
                dlg.ShowModal()
                treepath = dlg.treepath.GetValue()
                geompath = dlg.geompath.GetValue()
                ignore = dlg.ignorelist.GetValue()
                self.db.import_xml_file(pathname, treepath, geompath, ignore, tree)

        if not self.db.get_spatialite_status()[0]:
            text = "could not load sqlite extension SpatiaLite.\n" \
                   "Please download mod_spatialite Windows binaries from http://www.gaia-gis.it/gaia-sins/\n" \
                   "After Download, put DLLs into the same folder as executable.\n" \
                   "Some functionality of this program does not work.\n" \
                   "Exception message: "
            text += self.db.get_spatialite_status()[1]
            msg = wx.MessageDialog(self, str(text), style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()

        self.show_data_in_grid(self.db.get_number_of_columns(),
                               self.db.get_number_of_tablerecords(),
                               self.db.get_data())

        # Enable menu items
        self.export_citygml.Enable(True)
        self.reset_col_position.Enable(True)
        self.reset_col_visiblity.Enable(True)
        self.dublicates.Enable(True)
        self.duplicateGeom.Enable(True)
        self.validateGeom.Enable(True)
        self.add_geom_col.Enable(True)
        self.vegetation_code.Enable(True)
        self.add_height_dem.Enable(True)
        self.add_height_default.Enable(True)
        self.add_pointcloud_parameters.Enable(True)

    # method to be called when File > Export as CityGML is pressed
    def on_menu_export_citygml(self, event):
        export.ExportDialog(self)

    # method to reset program to a state similar to after startup
    # needed for example when a file was opened already and a new file will now be opened
    def reset_program(self):
        # Disable menu items
        self.export_citygml.Enable(False)
        self.reset_col_position.Enable(False)
        self.reset_col_visiblity.Enable(False)
        self.dublicates.Enable(False)
        self.duplicateGeom.Enable(False)
        self.validateGeom.Enable(False)
        self.add_geom_col.Enable(False)
        self.vegetation_code.Enable(False)
        self.add_height_dem.Enable(False)
        self.add_height_default.Enable(False)
        self.add_pointcloud_parameters.Enable(False)

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

                # yellow for ID columns (ROWID or IAI_TreeID)
                if ColIdx == 0 and self.db.get_create_id():
                    self.table_view_panel.grid.SetCellBackgroundColour(RowIdx, ColIdx, wx.Colour(255, 255, 128))
                if ColIdx == 0 and self.db.get_use_rowid():
                    self.table_view_panel.grid.SetCellBackgroundColour(RowIdx, ColIdx, wx.Colour(255, 255, 128))
                if ColIdx == 1 and self.db.get_create_id() and self.db.get_use_rowid():
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
        for col_idx in range(0, self.table_view_panel.grid.GetNumberCols() - 1):
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

    def on_geometry_validation(self, event):
        dlg = analysis.AnalyzeGeometryDialog(self)
        dlg.ShowModal()

    def on_add_geom(self, event):
        if self.db.get_spatialite_status()[0]:
            dlg = enrichment.AddGeometry(self)
            code = dlg.ShowModal()
            if code == 1:
                self.show_data_in_grid(self.db.get_number_of_columns(),
                                       self.db.get_number_of_tablerecords(),
                                       self.db.get_data())
        else:
            text = "Cannot perform this operation since SpatiaLite extension could not be loaded"
            msg = wx.MessageDialog(None, text, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()

    def on_add_citygml_vegetation_code(self, event):
        dlg = enrichment.AddCityGmlVegetationCodeGUI(self, self.db.get_db_filepath(), self.db.get_tree_table_name())
        code = dlg.ShowModal()
        if code == 1:
            self.show_data_in_grid(self.db.get_number_of_columns(),
                                   self.db.get_number_of_tablerecords(),
                                   self.db.get_data())

    def on_add_reference_height_dem(self, event):
        if not self.db.get_spatialite_status()[0]:
            text = "Cannot perform this operation since SpatiaLite extension could not be loaded"
            msg = wx.MessageDialog(None, text, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return

        if not self.db.get_contains_geom():
            msg = "No point geometry object has been created yet.\n" \
                  "Create point geometry object first (Data > Add geometry column)"
            dlg = wx.MessageDialog(self, msg, style=wx.ICON_WARNING | wx.CENTRE)
            dlg.ShowModal()
            return

        importgui = enrichment.ImportHeight(self, self.db.get_db_filepath(), "dem")
        if importgui.ShowModal() == 1234:
            derivegui = enrichment.GrabHeight(self, self.db.get_db_filepath())
            if derivegui.ShowModal() == 1:
                self.show_data_in_grid(self.db.get_number_of_columns(),
                                       self.db.get_number_of_tablerecords(),
                                       self.db.get_data())

    def on_add_default_reference_height(self, event):
        dlg = enrichment.DefaulHeight(self, self.db.get_db_filepath(), self.db.get_tree_table_name())
        code = dlg.ShowModal()
        if code == 1234:
            self.show_data_in_grid(self.db.get_number_of_columns(),
                                   self.db.get_number_of_tablerecords(),
                                   self.db.get_data())

    def on_derive_from_pointcloud(self, event):
        if not self.db.get_spatialite_status()[0]:
            text = "Cannot perform this operation since SpatiaLite extension could not be loaded"
            msg = wx.MessageDialog(None, text, style=wx.ICON_WARNING | wx.CENTRE)
            msg.ShowModal()
            return

        if not self.db.get_contains_geom():
            msg = "No point geometry object has been created yet.\n" \
                  "Create point geometry object first (Data > Add geometry column)"
            dlg = wx.MessageDialog(self, msg, style=wx.ICON_WARNING | wx.CENTRE)
            dlg.ShowModal()
            return

        importgui = enrichment.ImportHeight(self, self.db.get_db_filepath(), "pointcloud")
        if importgui.ShowModal() == 1234:
            derivegui = enrichment.DerivePointcloudGUI(self, self.db.get_db_filepath())
            if derivegui.ShowModal() == 1:
                self.show_data_in_grid(self.db.get_number_of_columns(),
                                       self.db.get_number_of_tablerecords(),
                                       self.db.get_data())

    # method to called when "? > License information (english)"
    def on_license_english(self, event):
        dialog = License(self)
        License.open_license(dialog, "english")

    # method to called when "? > License information (english)"
    def on_license_german(self, event):
        dialog = License(self)
        License.open_license(dialog, "german")

    def on_menu_about(self, event):
        dialog = License(self)
        License.open_license(dialog, "about")

    # method to be called when File > Exit
    def on_menu_exit(self, event):
        self.OnClose(event)


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

            if self.generate_rowid_checkbox.GetValue():
                self.GetParent().db.set_use_rowid(True)
            # set check rows number
            t_checknumber = self.inspect_rows.GetValue()
            self.GetParent().db.set_data_inspection_limit(int(t_checknumber))

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

        # checks if check-row-number can be cast to an integer
        try:
            int(self.inspect_rows.GetValue())
        except ValueError:
            valid = False
            warningtext = "Inspection rows must be integer"

        return valid, warningtext


class OpenDialogCSV(OpenDialog):
    def __init__(self, parent, path):
        super().__init__(parent, path)

        # Hide xml-related stuff
        self.m_staticText22.Show(False)
        self.treepath.Show(False)
        self.m_staticline1.Show(False)
        self.m_staticText23.Show(False)
        self.geompath.Show(False)
        self.m_staticline2.Show(False)
        self.m_staticText24.Show(False)
        self.ignorelist.Show(False)

    # method to populate columns of dropdown menus with column headers
    def populate_dropdown(self):
        # try to figure out file encoding: first try to open with utf-8, if that fails with cp1252
        # if neither file encoding works: show error message
        valid = True
        warningtext = ""
        header = ""
        try:
            with open(self._filepath, newline='', encoding=self.encoding.GetValue()) as file:
                for line in file:
                    if line == "\n" or line == "\r" or line == "\r\n":
                        continue
                    else:
                        header = line
                        break
        except LookupError:
            valid = False
            warningtext = "Error: Cannot open file. Unknown file encoding: %s.\n" \
                          "Please use python encoding codecs\n" \
                          "They can be found at https://docs.python.org/2.4/lib/standard-encodings.html" \
                          % self.encoding.GetValue()
        except UnicodeDecodeError:
            valid = False
            warningtext = "Cannot decode bytes in file.\n" \
                          "Is the file encoding set correctly?"
        except:
            valid = False
            warningtext = "Cannot open file for unknown reason"
        finally:
            if not valid:
                msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_ERROR)
                msg.ShowModal()
                return False

        header = header.strip("\r\n")
        sep = ""
        if self.seperator.GetString(self.seperator.GetSelection()) == "Semicolon":
            sep = ";"
        elif self.seperator.GetString(self.seperator.GetSelection()) == "Comma":
            sep = ","
        elif self.seperator.GetString(self.seperator.GetSelection()) == "Tabulator":
            sep = "\t"
        l_cols = header.split(sep)
        self.id_col1.SetItems(l_cols)
        self.id_col2.SetItems(l_cols)
        return True

    # method to be called when checkbox event for generate-id-checkbox is triggered
    # every time the checkbox is clicked
    # overrides method in parent class
    def id_checkbox_event(self, event):
        if self.encoding.GetValue() == "":
            self.generate_ID_box.SetValue(False)
            text = "Please specify file encoding first"
            msg = wx.MessageDialog(self, text, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
            msg.ShowModal()
            return
        if not self.populate_dropdown():
            self.generate_ID_box.SetValue(False)
            return
        self.id_col1.Enable(not self.id_col1.Enabled)
        self.id_col2.Enable(not self.id_col2.Enabled)
        self.IdText_Col1.Enable(not self.IdText_Col1.Enabled)
        self.IdText_Col2.Enable(not self.IdText_Col2.Enabled)

    def seperator_choice_event(self, event):
        if self.generate_ID_box.GetValue():
            self.populate_dropdown()

    # validates user input for everything that is csv-related
    # overrides parent class, but calls it in between
    def validate(self):
        valid, warningtext = super().validate()
        try:
            with open(self._filepath, newline='', encoding=self.encoding.GetValue()):
                pass
        except LookupError:
            # validates if user input for file encoding is valid
            valid = False
            warningtext = "Error: Cannot open file. Unknown file encoding: %s.\n" \
                          "Please use python encoding codecs\n" \
                          "They can be found at https://docs.python.org/2.4/lib/standard-encodings.html" \
                          % self.encoding.GetValue()
        except UnicodeDecodeError:
            # validates if file can be encoded using this user input
            valid = False
            warningtext = "Cannot decode bytes in file.\n" \
                          "Is the file encoding set correctly?"
        except:
            # catches anything als that could go wrong
            valid = False
            warningtext = "Cannot open file for unknown reason"
        return valid, warningtext

    # method is executed when OK is hit.
    # Overrides method in parent class
    def on_ok(self, event):
        super().on_ok(event)
        self.GetParent().db.set_file_encoding(self.encoding.GetValue())

        # sets seperator for input
        sep = ""
        if self.seperator.GetString(self.seperator.GetSelection()) == "Semicolon":
            sep = ";"
        elif self.seperator.GetString(self.seperator.GetSelection()) == "Comma":
            sep = ","
        elif self.seperator.GetString(self.seperator.GetSelection()) == "Tabulator":
            sep = "\t"
        self.GetParent().db.set_seperator(sep)


class OpenDialogXML(OpenDialog):
    def __init__(self, parent, path, tree):
        super().__init__(parent, path)

        # disable csv gui stuff
        self.m_staticText25.Show(False)
        self.m_staticText26.Show(False)
        self.m_staticText36.Show(False)
        self.seperator.Show(False)
        self.encoding.Show(False)

        self.SetTitle("XML import options")

        self.__Tree = tree
        self.__ns = dict([node for _, node in ET.iterparse(self._filepath, events=['start-ns'])])
        self.__Root = self.__Tree.getroot()

    # Populates dropdown menus after xml was opened
    def populate_dropdown(self):
        # fetch instpect_rows value from gui
        t_checknumber = self.inspect_rows.GetValue()
        check_number = int(t_checknumber)

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
        if self.generate_ID_box.GetValue():
            valid = True
            warningtext = ""

            # Validates if inspection_limit from gui can be cast to int
            try:
                int(self.inspect_rows.GetValue())
            except ValueError:
                valid = False
                warningtext = "Inspection rows must be integer"

            # dont create ID if xml pathes are not correct yet
            # validate_xml_geom_path() is used since it uses both pathes
            if not self.validate_xml_geom_path():
                valid = False
                warningtext = "XML path to tree coordinates is not correct.\n" \
                              "Must be a correct path to fetch column names.\n" \
                              "Please specify a correct path first."

            if not valid:
                self.generate_ID_box.SetValue(False)
                msg = wx.MessageDialog(self, warningtext, caption="Error", style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
                msg.ShowModal()
                return

            self.populate_dropdown()

        # enable/disable UI elements
        self.id_col1.Enable(not self.id_col1.Enabled)
        self.id_col2.Enable(not self.id_col2.Enabled)
        self.IdText_Col1.Enable(not self.IdText_Col1.Enabled)
        self.IdText_Col2.Enable(not self.IdText_Col2.Enabled)

    # Validates user input
    # Returns True, if User input is valid
    # Returns False, if User input is incorrect and prevents database import
    # Overrides method in parent class
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
    def on_xml_attribut_path_text_change(self, event):
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
    def on_xml_geom_path_text_change(self, event):
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


class License(default_gui.LicenseDialog):

    def __init__(self, parent):
        default_gui.LicenseDialog.__init__(self, parent)

    # Öffnet den Lizenzdialog und füllt den TextCtrl mit dem englischen oder deutschen Text
    def open_license(self, mode):

        if mode == "english":
            self.SetTitle("License Information")
            t_text = "0. PRELIMINARY NOTE\nThis is merely an informal translation of the German text " \
                     "\"Nutzungsbedingungen\" where the license conditions for this software have actually been " \
                     "established.\n\n1. EXCLUSION OF GUARANTEE\nKarlsruhe Institute of Technology does not " \
                     "guarantee the software, the data, or the documentation. It does not guarantee the correctness " \
                     "and usability of the contents or that they are not covered by any third party's rights, nor " \
                     "that access will be possible in a reliable way, free of viruses or errors.\n\n2. EXCLUSION " \
                     "OF LIABILITY\nKarlsruhe Institute of Technology is not liable for any damages, except those " \
                     "caused by a willful or grossly negligent violation of duties by either Karlsruhe Institute of " \
                     "Technology, its legal representatives, or its assistants in fulfillment. This holds also for " \
                     "damages caused by any violation of duties in contract negotiation or by carrying out " \
                     "unauthorised actions.\n\nIn the case of damages caused by a reckless violation of contractual " \
                     "or pre-contractual duties by Karlsruhe Institute of Technology, its legal representatives, or " \
                     "its assistants in fulfillment, liability for indirect damages and follow-up damages is " \
                     "excluded.\n\nThe cogent liability according to the Product Liability Act is not touched by the " \
                     "regulations stated above.\n\n3. CONFIDENTIALITY\nThe software, the data, and the documentation " \
                     "are confidential. Their commercial or scientific usage by the receiver or a third party, as " \
                     "well as the provision of access for third parties is only permitted after an agreement in " \
                     "writing by Karlsruhe Institute of Technology.\n\n4. PATENT AND TRADE-MARK RIGHTS\nKarlsruhe " \
                     "Institute of Technology reserves all rights on the software, the data, and the documentation " \
                     "in full extent, particuliarly the ownership, the copyrights as well as the procurement of " \
                     "domestic or foreign patent or trade-mark rights.\n"

        elif mode == "german":
            self.SetTitle("Nutzungsbedingungen")
            t_text = "1. GEWÄHRLEISTUNGSAUSSCHLUSS\nDas Karlsruhe Institute für Technologie übernimmt keine " \
                     "Gewährleistung für die Software, Daten und Dokumentationen, insbesondere nicht für Richtigkeit " \
                     "und Einsetzbarkeit des Inhalts oder die Freiheit von Rechten Dritter, sowie dafür, dass der " \
                     "Zugriff darauf verlässlich, virus- und fehlerfrei möglich ist.\n\n2. HAFTUNGSAUSSCHLUSS\n" \
                     "Das Karlsruhe Institute für Technologie haftet nur für Schäden, die auf einer vorsätzlichen " \
                     "oder grobfahrlässigen Pflichtverletzung durch das Karlsruhe Institute für Technologie, seine " \
                     "gesetzlichen Vertreter oder Erfüllungsgehilfen beruhen. Dies gilt auch für Schäden aus der " \
                     "Verletzung von Pflichten bei Vertragsverhandlungen sowie aus der Vornahme von unerlaubten " \
                     "Handlungen.\n\nFür Schäden, die auf einer fahrlässigen Verletzung von vertraglichen oder " \
                     "vorvertraglichen Pflichten durch das Karlsruhe Institute für Technologie, seine gesetzlichen " \
                     "Vertreter oder Erfüllungsgehilfen beruhen, ist die Haftung für mittelbare Schäden und " \
                     "Folgeschäden ausgeschlossen.\n\nDie zwingende Haftung nach dem Produkthaftungsgesetz bleibt " \
                     "von den vorstehenden Regelungen unberührt.\n\n3. VERTRAULICHKEIT\nDie Software, Daten und " \
                     "Dokumentationen sind vertraulich zu behandeln und dürfen nur mit vorheriger schriftlicher " \
                     "Zustimmung des Karlsruhe Institute für Technologie für eigene oder fremde gewerbliche oder " \
                     "wissenschaftliche Zwecke benutzt oder Dritten zugänglich gemacht werden.\n\n4. SCHUTZRECHTE\n" \
                     "Für die Software, Daten und Dokumentationen behält sich das Karlsruhe Institute für " \
                     "Technologie alle Rechte in vollem Umfange vor, insbesondere Eigentum, Urheberrecht sowie " \
                     "Erwirkung in- und ausländischer Schutzrechte.\n"

        elif mode == "about":
            self.SetTitle("About")
            t_text = "tree3d version: 1.0 (April 15, 2020)\n\n" \
                     "Bachelor thesis project by Jonas Hurst"

        self.license_text.write(t_text)
        self.ShowModal()


# create wxPython App
class MyApp(wx.App):
    def OnInit(self):
        # create instance of MainTableFrame
        frame = MainTableFrame(None)

        self.SetTopWindow(frame)
        frame.Show(True)
        return True
