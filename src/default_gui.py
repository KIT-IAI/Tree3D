# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Aug  8 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.grid

###########################################################################
## Class MainWindow
###########################################################################

class MainWindow ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"ArbokaTransformer", pos = wx.DefaultPosition, size = wx.Size( 1366,768 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		self.m_menubar7 = wx.MenuBar( 0 )
		self.file = wx.Menu()
		self.open = wx.MenuItem( self.file, wx.ID_ANY, u"Open", wx.EmptyString, wx.ITEM_NORMAL )
		self.file.Append( self.open )
		
		self.export_citygml = wx.MenuItem( self.file, wx.ID_ANY, u"Export as CityGML", wx.EmptyString, wx.ITEM_NORMAL )
		self.file.Append( self.export_citygml )
		self.export_citygml.Enable( False )
		
		self.test = wx.MenuItem( self.file, wx.ID_ANY, u"Test", wx.EmptyString, wx.ITEM_NORMAL )
		self.file.Append( self.test )
		
		self.m_menubar7.Append( self.file, u"File" ) 
		
		self.view = wx.Menu()
		self.col_properties = wx.MenuItem( self.view, wx.ID_ANY, u"Column Properties", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.col_properties )
		self.col_properties.Enable( False )
		
		self.reset_col_position = wx.MenuItem( self.view, wx.ID_ANY, u"Reset Column Position", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.reset_col_position )
		self.reset_col_position.Enable( False )
		
		self.reset_col_visiblity = wx.MenuItem( self.view, wx.ID_ANY, u"Show All Columns", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.reset_col_visiblity )
		self.reset_col_visiblity.Enable( False )
		
		self.stats = wx.MenuItem( self.view, wx.ID_ANY, u"Statistics", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.stats )
		self.stats.Enable( False )
		
		self.m_menubar7.Append( self.view, u"View" ) 
		
		self.analyze = wx.Menu()
		self.dublicates = wx.MenuItem( self.analyze, wx.ID_ANY, u"Check for Duplicates by ID", wx.EmptyString, wx.ITEM_NORMAL )
		self.analyze.Append( self.dublicates )
		self.dublicates.Enable( False )
		
		self.duplicateGeom = wx.MenuItem( self.analyze, wx.ID_ANY, u"Check for duplicates by geometry", wx.EmptyString, wx.ITEM_NORMAL )
		self.analyze.Append( self.duplicateGeom )
		self.duplicateGeom.Enable( False )
		
		self.analyze.AppendSeparator()
		
		self.validateGeom = wx.MenuItem( self.analyze, wx.ID_ANY, u"Geometry validation", wx.EmptyString, wx.ITEM_NORMAL )
		self.analyze.Append( self.validateGeom )
		self.validateGeom.Enable( False )
		
		self.m_menubar7.Append( self.analyze, u"Analyze" ) 
		
		self.data = wx.Menu()
		self.add_geom_col = wx.MenuItem( self.data, wx.ID_ANY, u"Add Geometry Column", wx.EmptyString, wx.ITEM_NORMAL )
		self.data.Append( self.add_geom_col )
		self.add_geom_col.Enable( False )
		
		self.vegetation_code = wx.MenuItem( self.data, wx.ID_ANY, u"Add CityGML vegetation code", wx.EmptyString, wx.ITEM_NORMAL )
		self.data.Append( self.vegetation_code )
		self.vegetation_code.Enable( False )
		
		self.m_menu2 = wx.Menu()
		self.add_height_dem = wx.MenuItem( self.m_menu2, wx.ID_ANY, u"Add reference height from DEM", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu2.Append( self.add_height_dem )
		self.add_height_dem.Enable( False )
		
		self.add_height_default = wx.MenuItem( self.m_menu2, wx.ID_ANY, u"Add default reference height", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu2.Append( self.add_height_default )
		self.add_height_default.Enable( False )
		
		self.data.AppendSubMenu( self.m_menu2, u"Add reference height" )
		
		self.m_menubar7.Append( self.data, u"Data" ) 
		
		self.SetMenuBar( self.m_menubar7 )
		
		self.m_statusBar3 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.OnClose )
		self.Bind( wx.EVT_MENU, self.on_menu_open, id = self.open.GetId() )
		self.Bind( wx.EVT_MENU, self.on_menu_export_citygml, id = self.export_citygml.GetId() )
		self.Bind( wx.EVT_MENU, self.on_menu_test, id = self.test.GetId() )
		self.Bind( wx.EVT_MENU, self.on_reset_column_position, id = self.reset_col_position.GetId() )
		self.Bind( wx.EVT_MENU, self.on_show_all_columns, id = self.reset_col_visiblity.GetId() )
		self.Bind( wx.EVT_MENU, self.on_check_for_duplicates_ID, id = self.dublicates.GetId() )
		self.Bind( wx.EVT_MENU, self.on_check_for_duplicates_geom, id = self.duplicateGeom.GetId() )
		self.Bind( wx.EVT_MENU, self.on_geometry_validation, id = self.validateGeom.GetId() )
		self.Bind( wx.EVT_MENU, self.on_add_geom, id = self.add_geom_col.GetId() )
		self.Bind( wx.EVT_MENU, self.on_add_citygml_vegetation_code, id = self.vegetation_code.GetId() )
		self.Bind( wx.EVT_MENU, self.on_add_reference_height_dem, id = self.add_height_dem.GetId() )
		self.Bind( wx.EVT_MENU, self.on_add_default_reference_height, id = self.add_height_default.GetId() )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnClose( self, event ):
		event.Skip()
	
	def on_menu_open( self, event ):
		event.Skip()
	
	def on_menu_export_citygml( self, event ):
		event.Skip()
	
	def on_menu_test( self, event ):
		event.Skip()
	
	def on_reset_column_position( self, event ):
		event.Skip()
	
	def on_show_all_columns( self, event ):
		event.Skip()
	
	def on_check_for_duplicates_ID( self, event ):
		event.Skip()
	
	def on_check_for_duplicates_geom( self, event ):
		event.Skip()
	
	def on_geometry_validation( self, event ):
		event.Skip()
	
	def on_add_geom( self, event ):
		event.Skip()
	
	def on_add_citygml_vegetation_code( self, event ):
		event.Skip()
	
	def on_add_reference_height_dem( self, event ):
		event.Skip()
	
	def on_add_default_reference_height( self, event ):
		event.Skip()
	

###########################################################################
## Class OnOpenDialog
###########################################################################

class OnOpenDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"CSV import options", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.STAY_ON_TOP )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer4 = wx.FlexGridSizer( 17, 1, 0, 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText22 = wx.StaticText( self, wx.ID_ANY, u"Specify XML path from root element to tree attribute elements.\nInclude element prefixes in path.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )
		
		fgSizer4.Add( self.m_staticText22, 0, wx.ALL, 5 )
		
		self.treepath = wx.TextCtrl( self, wx.ID_ANY, u"./wfs:member/fis:s_wfs_baumbestand", wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		fgSizer4.Add( self.treepath, 0, wx.ALL, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer4.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText23 = wx.StaticText( self, wx.ID_ANY, u"Specify path from this elemnt to tree coordinates\n(if coordinates are not specified as tree attributes)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )
		
		fgSizer4.Add( self.m_staticText23, 0, wx.ALL, 5 )
		
		self.geompath = wx.TextCtrl( self, wx.ID_ANY, u"./fis:ORA_GEOMETRY/gml:Point/gml:pos", wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		fgSizer4.Add( self.geompath, 0, wx.ALL, 5 )
		
		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer4.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText24 = wx.StaticText( self, wx.ID_ANY, u"Specify attributes within this element to ignore during import.\nDO NOT include element prefixes\nseperate elements with Semicolon.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )
		
		fgSizer4.Add( self.m_staticText24, 0, wx.ALL, 5 )
		
		self.ignorelist = wx.TextCtrl( self, wx.ID_ANY, u"ORA_GEOMETRY", wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		fgSizer4.Add( self.ignorelist, 0, wx.ALL, 5 )
		
		fgSizer8 = wx.FlexGridSizer( 2, 3, 0, 0 )
		fgSizer8.SetFlexibleDirection( wx.BOTH )
		fgSizer8.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText25 = wx.StaticText( self, wx.ID_ANY, u"Separator", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )
		
		fgSizer8.Add( self.m_staticText25, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		seperatorChoices = [ u"Semicolon", u"Comma", u"Tabulator" ]
		self.seperator = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, seperatorChoices, 0 )
		self.seperator.SetSelection( 0 )
		fgSizer8.Add( self.seperator, 0, wx.ALL, 5 )
		
		
		fgSizer8.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText26 = wx.StaticText( self, wx.ID_ANY, u"Encoding", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )
		
		fgSizer8.Add( self.m_staticText26, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.encoding = wx.TextCtrl( self, wx.ID_ANY, u"utf-8-sig", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer8.Add( self.encoding, 0, wx.ALL, 5 )
		
		self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"write \"utf-8-sig\"\nif encoding is UTF8-BOM", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )
		
		fgSizer8.Add( self.m_staticText36, 0, wx.ALL, 5 )
		
		
		fgSizer4.Add( fgSizer8, 1, wx.EXPAND, 5 )
		
		self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer4.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText28 = wx.StaticText( self, wx.ID_ANY, u"Set the number of rows to be inspected before input here.\nRows are expected to figure out the data type for example", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )
		
		fgSizer4.Add( self.m_staticText28, 0, wx.ALL, 5 )
		
		fgSizer9 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer9.SetFlexibleDirection( wx.BOTH )
		fgSizer9.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText27 = wx.StaticText( self, wx.ID_ANY, u"Rows to inspect", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )
		
		fgSizer9.Add( self.m_staticText27, 0, wx.ALL, 5 )
		
		self.inspect_rows = wx.TextCtrl( self, wx.ID_ANY, u"500", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer9.Add( self.inspect_rows, 0, wx.ALL, 5 )
		
		
		fgSizer4.Add( fgSizer9, 1, wx.EXPAND, 5 )
		
		self.m_staticline7 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer4.Add( self.m_staticline7, 0, wx.EXPAND |wx.ALL, 5 )
		
		sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"unique tree IDs" ), wx.VERTICAL )
		
		self.generate_rowid_checkbox = wx.CheckBox( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Generate incrementing IDs", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.generate_rowid_checkbox.SetToolTip( u"use this, if there is no ID associated with data" )
		
		sbSizer1.Add( self.generate_rowid_checkbox, 0, wx.ALL, 5 )
		
		self.generate_ID_box = wx.CheckBox( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Generate tree IDs from CSV file columns", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.generate_ID_box.SetToolTip( u"use this, if an ID can be created by combining two columns" )
		
		sbSizer1.Add( self.generate_ID_box, 0, wx.ALL, 5 )
		
		self.m_staticText4 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"ArbokaTransformer can create an ID out of two\ncolumns in the CSV table for each entry. \nGenerated ID column will be highlighted  in table.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		
		sbSizer1.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )
		
		self.IdText_Col1 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Column 1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.IdText_Col1.Wrap( -1 )
		
		self.IdText_Col1.Enable( False )
		
		gSizer2.Add( self.IdText_Col1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		id_col1Choices = []
		self.id_col1 = wx.Choice( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, id_col1Choices, 0 )
		self.id_col1.SetSelection( 0 )
		self.id_col1.Enable( False )
		
		gSizer2.Add( self.id_col1, 0, wx.ALL, 5 )
		
		self.IdText_Col2 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Column 2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.IdText_Col2.Wrap( -1 )
		
		self.IdText_Col2.Enable( False )
		
		gSizer2.Add( self.IdText_Col2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		id_col2Choices = []
		self.id_col2 = wx.Choice( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, id_col2Choices, 0 )
		self.id_col2.SetSelection( 0 )
		self.id_col2.Enable( False )
		
		gSizer2.Add( self.id_col2, 0, wx.ALL, 5 )
		
		
		sbSizer1.Add( gSizer2, 1, wx.EXPAND, 5 )
		
		
		fgSizer4.Add( sbSizer1, 1, wx.EXPAND, 5 )
		
		self.ok_button = wx.Button( self, wx.ID_ANY, u"OK", wx.Point( -1,-1 ), wx.DefaultSize, 0 )
		
		self.ok_button.SetBitmapPosition( wx.RIGHT )
		fgSizer4.Add( self.ok_button, 0, wx.ALL, 5 )
		
		
		self.SetSizer( fgSizer4 )
		self.Layout()
		fgSizer4.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.treepath.Bind( wx.EVT_TEXT, self.on_xml_attribut_path_text_change )
		self.geompath.Bind( wx.EVT_TEXT, self.on_xml_geom_path_text_change )
		self.seperator.Bind( wx.EVT_CHOICE, self.seperator_choice_event )
		self.generate_rowid_checkbox.Bind( wx.EVT_CHECKBOX, self.id_increment_checkbox_event )
		self.generate_ID_box.Bind( wx.EVT_CHECKBOX, self.id_checkbox_event )
		self.ok_button.Bind( wx.EVT_BUTTON, self.on_ok )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_xml_attribut_path_text_change( self, event ):
		event.Skip()
	
	def on_xml_geom_path_text_change( self, event ):
		event.Skip()
	
	def seperator_choice_event( self, event ):
		event.Skip()
	
	def id_increment_checkbox_event( self, event ):
		event.Skip()
	
	def id_checkbox_event( self, event ):
		event.Skip()
	
	def on_ok( self, event ):
		event.Skip()
	

###########################################################################
## Class OnCheckDuplicateIdDialog
###########################################################################

class OnCheckDuplicateIdDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Check for duplicates by ID", pos = wx.DefaultPosition, size = wx.Size( 353,519 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.Size( -1,-1 ), wx.Size( -1,-1 ) )
		
		fgSizer2 = wx.FlexGridSizer( 9, 1, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"This analysis tool allows to check all data loaded for duplicates.\nPlease select a column that contains ID values for each tree", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		
		fgSizer2.Add( self.m_staticText7, 0, wx.ALL, 5 )
		
		gSizer3 = wx.GridSizer( 1, 3, 0, 0 )
		
		self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"Select ID field", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )
		
		gSizer3.Add( self.m_staticText8, 0, wx.ALL, 5 )
		
		IdColumnsChoices = []
		self.IdColumns = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, IdColumnsChoices, 0 )
		self.IdColumns.SetSelection( 0 )
		gSizer3.Add( self.IdColumns, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( gSizer3, 1, wx.EXPAND, 5 )
		
		self.UUIDCheck = wx.CheckBox( self, wx.ID_ANY, u"Is UUID", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.UUIDCheck, 0, wx.ALL, 5 )
		
		self.analyze = wx.Button( self, wx.ID_ANY, u"Analyze", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.analyze, 0, wx.ALL, 5 )
		
		self.m_staticline11 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline11, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.InfoTextDuplicate = wx.StaticText( self, wx.ID_ANY, u"Check for duplicates completed:\nThe following Duplicate values have been found:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.InfoTextDuplicate.Wrap( -1 )
		
		self.InfoTextDuplicate.Hide()
		
		fgSizer2.Add( self.InfoTextDuplicate, 0, wx.ALL, 5 )
		
		self.DuplicateGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.DuplicateGrid.CreateGrid( 0, 2 )
		self.DuplicateGrid.EnableEditing( False )
		self.DuplicateGrid.EnableGridLines( True )
		self.DuplicateGrid.EnableDragGridSize( False )
		self.DuplicateGrid.SetMargins( 0, 0 )
		
		# Columns
		self.DuplicateGrid.SetColSize( 0, 278 )
		self.DuplicateGrid.SetColSize( 1, 28 )
		self.DuplicateGrid.EnableDragColMove( False )
		self.DuplicateGrid.EnableDragColSize( True )
		self.DuplicateGrid.SetColLabelSize( 30 )
		self.DuplicateGrid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.DuplicateGrid.EnableDragRowSize( False )
		self.DuplicateGrid.SetRowLabelSize( 1 )
		self.DuplicateGrid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.DuplicateGrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.DuplicateGrid.Hide()
		self.DuplicateGrid.SetMinSize( wx.Size( 330,120 ) )
		self.DuplicateGrid.SetMaxSize( wx.Size( 330,120 ) )
		
		fgSizer2.Add( self.DuplicateGrid, 0, wx.ALL, 5 )
		
		self.InfoTextUUID = wx.StaticText( self, wx.ID_ANY, u"UUID-Validation completed:\nThe following UUIDs are invalid:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.InfoTextUUID.Wrap( -1 )
		
		self.InfoTextUUID.Hide()
		
		fgSizer2.Add( self.InfoTextUUID, 0, wx.ALL, 5 )
		
		self.UUIDGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.UUIDGrid.CreateGrid( 0, 1 )
		self.UUIDGrid.EnableEditing( False )
		self.UUIDGrid.EnableGridLines( True )
		self.UUIDGrid.EnableDragGridSize( False )
		self.UUIDGrid.SetMargins( 0, 0 )
		
		# Columns
		self.UUIDGrid.SetColSize( 0, 303 )
		self.UUIDGrid.EnableDragColMove( False )
		self.UUIDGrid.EnableDragColSize( True )
		self.UUIDGrid.SetColLabelSize( 30 )
		self.UUIDGrid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.UUIDGrid.EnableDragRowSize( False )
		self.UUIDGrid.SetRowLabelSize( 1 )
		self.UUIDGrid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.UUIDGrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.UUIDGrid.Hide()
		self.UUIDGrid.SetMinSize( wx.Size( 330,120 ) )
		self.UUIDGrid.SetMaxSize( wx.Size( 330,120 ) )
		
		fgSizer2.Add( self.UUIDGrid, 0, wx.ALL, 5 )
		
		
		self.SetSizer( fgSizer2 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.analyze.Bind( wx.EVT_BUTTON, self.on_analyze )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_analyze( self, event ):
		event.Skip()
	

###########################################################################
## Class OnCheckDuplicateGeomDialog
###########################################################################

class OnCheckDuplicateGeomDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Check for duplicates by Geom", pos = wx.DefaultPosition, size = wx.Size( 353,448 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.Size( -1,-1 ), wx.Size( -1,-1 ) )
		
		fgSizer2 = wx.FlexGridSizer( 6, 1, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"This analysis tool allows to check all data loaded for duplicates\nby their geometric position. All trees closer together than the\nselected threshold are marked as duplicates.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		
		fgSizer2.Add( self.m_staticText7, 0, wx.ALL, 5 )
		
		gSizer3 = wx.GridSizer( 4, 2, 0, 0 )
		
		self.m_staticText82 = wx.StaticText( self, wx.ID_ANY, u"Select ID field", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText82.Wrap( -1 )
		
		gSizer3.Add( self.m_staticText82, 0, wx.ALL, 5 )
		
		IdColumnsChoices = []
		self.IdColumns = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, IdColumnsChoices, 0 )
		self.IdColumns.SetSelection( 0 )
		gSizer3.Add( self.IdColumns, 0, wx.ALL, 5 )
		
		self.m_staticText81 = wx.StaticText( self, wx.ID_ANY, u"X-Value", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText81.Wrap( -1 )
		
		gSizer3.Add( self.m_staticText81, 0, wx.ALL, 5 )
		
		xvalueChoices = []
		self.xvalue = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, xvalueChoices, 0 )
		self.xvalue.SetSelection( 0 )
		gSizer3.Add( self.xvalue, 0, wx.ALL, 5 )
		
		self.yvalue1 = wx.StaticText( self, wx.ID_ANY, u"Y-Value", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.yvalue1.Wrap( -1 )
		
		gSizer3.Add( self.yvalue1, 0, wx.ALL, 5 )
		
		yvalueChoices = []
		self.yvalue = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, yvalueChoices, 0 )
		self.yvalue.SetSelection( 0 )
		gSizer3.Add( self.yvalue, 0, wx.ALL, 5 )
		
		self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"Threshold (m)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )
		
		gSizer3.Add( self.m_staticText8, 0, wx.ALL, 5 )
		
		self.threshold = wx.TextCtrl( self, wx.ID_ANY, u"0.35", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.threshold.SetMaxLength( 6 ) 
		gSizer3.Add( self.threshold, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( gSizer3, 1, wx.EXPAND, 5 )
		
		fgSizer15 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer15.SetFlexibleDirection( wx.BOTH )
		fgSizer15.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.analyze = wx.Button( self, wx.ID_ANY, u"Analyze", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer15.Add( self.analyze, 0, wx.ALL, 5 )
		
		self.gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 231,26 ), wx.GA_HORIZONTAL )
		self.gauge.SetValue( 0 ) 
		fgSizer15.Add( self.gauge, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( fgSizer15, 1, wx.EXPAND, 5 )
		
		self.m_staticline12 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline12, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.InfoTextDuplicate = wx.StaticText( self, wx.ID_ANY, u"Check for duplicates completed:\nThe following Duplicate values have been found:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.InfoTextDuplicate.Wrap( -1 )
		
		self.InfoTextDuplicate.Hide()
		
		fgSizer2.Add( self.InfoTextDuplicate, 0, wx.ALL, 5 )
		
		self.DuplicateGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.DuplicateGrid.CreateGrid( 0, 3 )
		self.DuplicateGrid.EnableEditing( False )
		self.DuplicateGrid.EnableGridLines( True )
		self.DuplicateGrid.EnableDragGridSize( False )
		self.DuplicateGrid.SetMargins( 0, 0 )
		
		# Columns
		self.DuplicateGrid.SetColSize( 0, 119 )
		self.DuplicateGrid.SetColSize( 1, 119 )
		self.DuplicateGrid.SetColSize( 2, 67 )
		self.DuplicateGrid.EnableDragColMove( False )
		self.DuplicateGrid.EnableDragColSize( True )
		self.DuplicateGrid.SetColLabelSize( 30 )
		self.DuplicateGrid.SetColLabelValue( 0, u"ID 1" )
		self.DuplicateGrid.SetColLabelValue( 1, u"ID 2" )
		self.DuplicateGrid.SetColLabelValue( 2, u"Distance" )
		self.DuplicateGrid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.DuplicateGrid.EnableDragRowSize( False )
		self.DuplicateGrid.SetRowLabelSize( 1 )
		self.DuplicateGrid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.DuplicateGrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.DuplicateGrid.Hide()
		self.DuplicateGrid.SetMinSize( wx.Size( 330,120 ) )
		self.DuplicateGrid.SetMaxSize( wx.Size( 330,120 ) )
		
		fgSizer2.Add( self.DuplicateGrid, 0, wx.ALL, 5 )
		
		
		self.SetSizer( fgSizer2 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.analyze.Bind( wx.EVT_BUTTON, self.on_analyze )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_analyze( self, event ):
		event.Skip()
	

###########################################################################
## Class OnCheckGeometryDialog
###########################################################################

class OnCheckGeometryDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Analyze geometry attributes", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.Size( 453,-1 ), wx.DefaultSize )
		
		fgSizer10 = wx.FlexGridSizer( 9, 1, 0, 0 )
		fgSizer10.SetFlexibleDirection( wx.BOTH )
		fgSizer10.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText29 = wx.StaticText( self, wx.ID_ANY, u"This tool allows to analyze geometric parameters needed to create 3D tree objects.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText29.Wrap( -1 )
		
		fgSizer10.Add( self.m_staticText29, 0, wx.ALL, 5 )
		
		sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Coordinate Columns" ), wx.VERTICAL )
		
		fgSizer13 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer13.SetFlexibleDirection( wx.BOTH )
		fgSizer13.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText33 = wx.StaticText( sbSizer7.GetStaticBox(), wx.ID_ANY, u"ID Column", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText33.Wrap( -1 )
		
		fgSizer13.Add( self.m_staticText33, 0, wx.ALL, 5 )
		
		choiceIDChoices = []
		self.choiceID = wx.Choice( sbSizer7.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceIDChoices, 0 )
		self.choiceID.SetSelection( 0 )
		fgSizer13.Add( self.choiceID, 0, wx.ALL, 5 )
		
		
		sbSizer7.Add( fgSizer13, 1, wx.EXPAND, 5 )
		
		
		fgSizer10.Add( sbSizer7, 1, wx.EXPAND, 5 )
		
		sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"CityGML attribute mapping" ), wx.VERTICAL )
		
		fgSizer6 = wx.FlexGridSizer( 3, 4, 0, 0 )
		fgSizer6.SetFlexibleDirection( wx.BOTH )
		fgSizer6.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText15 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Tree height", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText15, 0, wx.ALL, 5 )
		
		choiceHeightChoices = []
		self.choiceHeight = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceHeightChoices, 0 )
		self.choiceHeight.SetSelection( 0 )
		fgSizer6.Add( self.choiceHeight, 0, wx.ALL, 5 )
		
		choiceHeightUnitChoices = [ u"m", u"cm" ]
		self.choiceHeightUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceHeightUnitChoices, 0 )
		self.choiceHeightUnit.SetSelection( 0 )
		fgSizer6.Add( self.choiceHeightUnit, 0, wx.ALL, 5 )
		
		
		fgSizer6.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText17 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Trunk diameter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText17, 0, wx.ALL, 5 )
		
		choiceTrunkChoices = []
		self.choiceTrunk = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceTrunkChoices, 0 )
		self.choiceTrunk.SetSelection( 0 )
		fgSizer6.Add( self.choiceTrunk, 0, wx.ALL, 5 )
		
		choiceTrunkUnitChoices = [ u"m", u"cm" ]
		self.choiceTrunkUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceTrunkUnitChoices, 0 )
		self.choiceTrunkUnit.SetSelection( 0 )
		fgSizer6.Add( self.choiceTrunkUnit, 0, wx.ALL, 5 )
		
		trunk_circChoices = [ u"is diameter", u"is circumference" ]
		self.trunk_circ = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, trunk_circChoices, 0 )
		self.trunk_circ.SetSelection( 0 )
		fgSizer6.Add( self.trunk_circ, 0, wx.ALL, 5 )
		
		self.m_staticText16 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Crown diameter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText16, 0, wx.ALL, 5 )
		
		choiceCrownChoices = []
		self.choiceCrown = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceCrownChoices, 0 )
		self.choiceCrown.SetSelection( 0 )
		fgSizer6.Add( self.choiceCrown, 0, wx.ALL, 5 )
		
		choiceCrownUnitChoices = [ u"m", u"cm" ]
		self.choiceCrownUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceCrownUnitChoices, 0 )
		self.choiceCrownUnit.SetSelection( 0 )
		fgSizer6.Add( self.choiceCrownUnit, 0, wx.ALL, 5 )
		
		crown_circChoices = [ u"is diameter", u"is circumference" ]
		self.crown_circ = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, crown_circChoices, 0 )
		self.crown_circ.SetSelection( 0 )
		fgSizer6.Add( self.crown_circ, 0, wx.ALL, 5 )
		
		
		sbSizer3.Add( fgSizer6, 1, wx.EXPAND, 5 )
		
		
		fgSizer10.Add( sbSizer3, 1, wx.EXPAND, 5 )
		
		self.m_staticline10 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer10.Add( self.m_staticline10, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_button9 = wx.Button( self, wx.ID_ANY, u"Analyze", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer10.Add( self.m_button9, 0, wx.ALL, 5 )
		
		self.m_staticline13 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.m_staticline13.Hide()
		
		fgSizer10.Add( self.m_staticline13, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.analysis_valid = wx.StaticText( self, wx.ID_ANY, u"Analysis completed.\nAll trees have valid geometric parameters.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.analysis_valid.Wrap( -1 )
		
		self.analysis_valid.Hide()
		
		fgSizer10.Add( self.analysis_valid, 0, wx.ALL, 5 )
		
		self.analysis_invalid = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.analysis_invalid.Wrap( -1 )
		
		self.analysis_invalid.Hide()
		
		fgSizer10.Add( self.analysis_invalid, 0, wx.ALL, 5 )
		
		self.result_grid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 440,-1 ), 0 )
		
		# Grid
		self.result_grid.CreateGrid( 0, 2 )
		self.result_grid.EnableEditing( False )
		self.result_grid.EnableGridLines( True )
		self.result_grid.EnableDragGridSize( False )
		self.result_grid.SetMargins( 0, 0 )
		
		# Columns
		self.result_grid.AutoSizeColumns()
		self.result_grid.EnableDragColMove( False )
		self.result_grid.EnableDragColSize( True )
		self.result_grid.SetColLabelSize( 30 )
		self.result_grid.SetColLabelValue( 0, u"ID" )
		self.result_grid.SetColLabelValue( 1, u"Detail" )
		self.result_grid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.result_grid.EnableDragRowSize( True )
		self.result_grid.SetRowLabelSize( 1 )
		self.result_grid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.result_grid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.result_grid.Hide()
		self.result_grid.SetMaxSize( wx.Size( 440,200 ) )
		
		fgSizer10.Add( self.result_grid, 0, wx.ALL, 5 )
		
		
		self.SetSizer( fgSizer10 )
		self.Layout()
		fgSizer10.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.m_button9.Bind( wx.EVT_BUTTON, self.on_analyze )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_analyze( self, event ):
		event.Skip()
	

###########################################################################
## Class CityGmlExport
###########################################################################

class CityGmlExport ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Export as CityGML", pos = wx.DefaultPosition, size = wx.Size( 447,695 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer4 = wx.FlexGridSizer( 9, 1, 0, 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		fgSizer71 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer71.SetFlexibleDirection( wx.BOTH )
		fgSizer71.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.filepat_textbox = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), wx.TE_READONLY )
		fgSizer71.Add( self.filepat_textbox, 0, wx.ALL, 5 )
		
		self.buttonBrowse = wx.Button( self, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.Size( 90,-1 ), 0 )
		fgSizer71.Add( self.buttonBrowse, 0, wx.ALL, 5 )
		
		
		fgSizer4.Add( fgSizer71, 1, wx.EXPAND, 5 )
		
		self.box_prettyprint = wx.CheckBox( self, wx.ID_ANY, u"Create pretty-printed xml output (may be slow for large datasets)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.box_prettyprint.SetValue(True) 
		fgSizer4.Add( self.box_prettyprint, 0, wx.ALL, 5 )
		
		sbSizer4 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Coordinate Columns" ), wx.VERTICAL )
		
		fgSizer7 = wx.FlexGridSizer( 4, 4, 0, 0 )
		fgSizer7.SetFlexibleDirection( wx.BOTH )
		fgSizer7.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText171 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Easting", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText171.Wrap( -1 )
		
		fgSizer7.Add( self.m_staticText171, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceXvalueChoices = []
		self.choiceXvalue = wx.Choice( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceXvalueChoices, 0 )
		self.choiceXvalue.SetSelection( 0 )
		self.choiceXvalue.SetToolTip( u"Select value for easting" )
		
		fgSizer7.Add( self.choiceXvalue, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText18 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Northing", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )
		
		fgSizer7.Add( self.m_staticText18, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceYvalueChoices = []
		self.choiceYvalue = wx.Choice( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceYvalueChoices, 0 )
		self.choiceYvalue.SetSelection( 0 )
		self.choiceYvalue.SetToolTip( u"Select value for northing" )
		
		fgSizer7.Add( self.choiceYvalue, 0, wx.ALL, 5 )
		
		self.m_staticText53 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Reference Height", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText53.Wrap( -1 )
		
		fgSizer7.Add( self.m_staticText53, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceRefheightChoices = []
		self.choiceRefheight = wx.Choice( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceRefheightChoices, 0 )
		self.choiceRefheight.SetSelection( 0 )
		self.choiceRefheight.SetToolTip( u"select column that contains the tree's reference height" )
		
		fgSizer7.Add( self.choiceRefheight, 0, wx.ALL, 5 )
		
		self.m_staticText20 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"EPSG-Code", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( -1 )
		
		fgSizer7.Add( self.m_staticText20, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.epsg = wx.TextCtrl( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.epsg.SetMaxLength( 6 ) 
		self.epsg.SetToolTip( u"enter epsg code of coordinate reference system" )
		
		fgSizer7.Add( self.epsg, 0, wx.ALL, 5 )
		
		
		sbSizer4.Add( fgSizer7, 1, wx.EXPAND, 5 )
		
		
		fgSizer4.Add( sbSizer4, 1, wx.EXPAND, 5 )
		
		sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"CityGML SolitaryVegetationObject attributes" ), wx.VERTICAL )
		
		fgSizer6 = wx.FlexGridSizer( 5, 4, 0, 0 )
		fgSizer6.SetFlexibleDirection( wx.BOTH )
		fgSizer6.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText15 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Tree Height", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText15, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceHeightChoices = []
		self.choiceHeight = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceHeightChoices, 0 )
		self.choiceHeight.SetSelection( 0 )
		self.choiceHeight.SetToolTip( u"select column that contains tree height" )
		
		fgSizer6.Add( self.choiceHeight, 0, wx.ALL, 5 )
		
		choiceHeightUnitChoices = [ u"m", u"cm" ]
		self.choiceHeightUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceHeightUnitChoices, 0 )
		self.choiceHeightUnit.SetSelection( 0 )
		fgSizer6.Add( self.choiceHeightUnit, 0, wx.ALL, 5 )
		
		
		fgSizer6.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText17 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Trunk diameter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText17, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceTrunkChoices = []
		self.choiceTrunk = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceTrunkChoices, 0 )
		self.choiceTrunk.SetSelection( 0 )
		self.choiceTrunk.SetToolTip( u"select column that contains values to calculate trunk diameter from" )
		
		fgSizer6.Add( self.choiceTrunk, 0, wx.ALL, 5 )
		
		choiceTrunkUnitChoices = [ u"m", u"cm" ]
		self.choiceTrunkUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceTrunkUnitChoices, 0 )
		self.choiceTrunkUnit.SetSelection( 0 )
		self.choiceTrunkUnit.SetToolTip( u"select unit of meassurement used in data" )
		
		fgSizer6.Add( self.choiceTrunkUnit, 0, wx.ALL, 5 )
		
		trunk_circChoices = [ u"is diameter", u"is circumference" ]
		self.trunk_circ = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, trunk_circChoices, 0 )
		self.trunk_circ.SetSelection( 0 )
		self.trunk_circ.SetToolTip( u"select if data for trunk diameter is diameter or circumference" )
		
		fgSizer6.Add( self.trunk_circ, 0, wx.ALL, 5 )
		
		self.m_staticText16 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Crown diameter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText16, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceCrownChoices = []
		self.choiceCrown = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceCrownChoices, 0 )
		self.choiceCrown.SetSelection( 0 )
		self.choiceCrown.SetToolTip( u"select column that contains values to calculate crown diameter from" )
		
		fgSizer6.Add( self.choiceCrown, 0, wx.ALL, 5 )
		
		choiceCrownUnitChoices = [ u"m", u"cm" ]
		self.choiceCrownUnit = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceCrownUnitChoices, 0 )
		self.choiceCrownUnit.SetSelection( 0 )
		self.choiceCrownUnit.SetToolTip( u"select unit of meassurement used in data" )
		
		fgSizer6.Add( self.choiceCrownUnit, 0, wx.ALL, 5 )
		
		crown_circChoices = [ u"is diameter", u"is circumference" ]
		self.crown_circ = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, crown_circChoices, 0 )
		self.crown_circ.SetSelection( 0 )
		self.crown_circ.SetToolTip( u"select if data for trunk diameter is diameter or circumference" )
		
		fgSizer6.Add( self.crown_circ, 0, wx.ALL, 5 )
		
		self.m_staticText19 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"CityGML Species Code", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText19, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceSpeciesChoices = []
		self.choiceSpecies = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceSpeciesChoices, 0 )
		self.choiceSpecies.SetSelection( 0 )
		self.choiceSpecies.SetToolTip( u"select column that contains CityGML species code" )
		
		fgSizer6.Add( self.choiceSpecies, 0, wx.ALL, 5 )
		
		
		fgSizer6.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer6.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText52 = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"CityGML Class Code", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText52.Wrap( -1 )
		
		fgSizer6.Add( self.m_staticText52, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		choiceClassChoices = []
		self.choiceClass = wx.Choice( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceClassChoices, 0 )
		self.choiceClass.SetSelection( 0 )
		self.choiceClass.SetToolTip( u"select column that contains CityGML SolitaryVegetationObject class code. Determines what kind of tree is created (coniferous or deciduous)" )
		
		fgSizer6.Add( self.choiceClass, 0, wx.ALL, 5 )
		
		
		sbSizer3.Add( fgSizer6, 1, wx.EXPAND, 5 )
		
		
		fgSizer4.Add( sbSizer3, 1, wx.EXPAND, 5 )
		
		sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"CityGML geometric modelling options" ), wx.VERTICAL )
		
		fgSizer29 = wx.FlexGridSizer( 3, 2, 0, 0 )
		fgSizer29.SetFlexibleDirection( wx.BOTH )
		fgSizer29.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText62 = wx.StaticText( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Geometry Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText62.Wrap( -1 )
		
		fgSizer29.Add( self.m_staticText62, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		gSizer5 = wx.GridSizer( 1, 2, 0, 0 )
		
		self.explicit_geom = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Explicit", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.explicit_geom.SetValue( True ) 
		self.explicit_geom.SetToolTip( u"select if explicit geometries should be created" )
		
		gSizer5.Add( self.explicit_geom, 0, wx.ALL, 5 )
		
		self.implicit_geom = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Implicit", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.implicit_geom.SetToolTip( u"select if implicit geometries should be created" )
		
		gSizer5.Add( self.implicit_geom, 0, wx.ALL, 5 )
		
		
		fgSizer29.Add( gSizer5, 1, wx.EXPAND, 5 )
		
		self.m_staticText63 = wx.StaticText( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Crown height", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText63.Wrap( -1 )
		
		fgSizer29.Add( self.m_staticText63, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		crown_height_choiceChoices = [ u"same as crown diameter", u"1/2 the tree height", u"2/3 the tree height", u"3/4 the tree height", u"4/5 the tree height" ]
		self.crown_height_choice = wx.Choice( sbSizer2.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, crown_height_choiceChoices, 0 )
		self.crown_height_choice.SetSelection( 0 )
		self.crown_height_choice.SetToolTip( u"select, how crown height should be calculated" )
		
		fgSizer29.Add( self.crown_height_choice, 0, wx.ALL, 5 )
		
		self.m_staticText54 = wx.StaticText( sbSizer2.GetStaticBox(), wx.ID_ANY, u"default", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText54.Wrap( -1 )
		
		fgSizer29.Add( self.m_staticText54, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		default_choiceChoices = [ u"none", u"deciduous tree", u"coniferous tree" ]
		self.default_choice = wx.Choice( sbSizer2.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, default_choiceChoices, 0 )
		self.default_choice.SetSelection( 0 )
		self.default_choice.SetToolTip( u"select, what kind of tree should be generated if vegetation class is not set or vegetation class is unknown" )
		
		fgSizer29.Add( self.default_choice, 0, wx.ALL, 5 )
		
		
		sbSizer2.Add( fgSizer29, 1, wx.EXPAND, 5 )
		
		
		fgSizer4.Add( sbSizer2, 1, wx.EXPAND, 5 )
		
		sbSizer11 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"CityGML Level-Of-Detail options" ), wx.VERTICAL )
		
		fgSizer28 = wx.FlexGridSizer( 4, 4, 0, 0 )
		fgSizer28.SetFlexibleDirection( wx.BOTH )
		fgSizer28.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.lod1 = wx.CheckBox( sbSizer11.GetStaticBox(), wx.ID_ANY, u"LOD1", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer28.Add( self.lod1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod1_geomtypeChoices = []
		self.lod1_geomtype = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod1_geomtypeChoices, 0 )
		self.lod1_geomtype.SetSelection( 0 )
		self.lod1_geomtype.Enable( False )
		
		fgSizer28.Add( self.lod1_geomtype, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod1_segments_text = wx.StaticText( sbSizer11.GetStaticBox(), wx.ID_ANY, u"segments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lod1_segments_text.Wrap( -1 )
		
		self.lod1_segments_text.Hide()
		
		fgSizer28.Add( self.lod1_segments_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod1_segmentsChoices = []
		self.lod1_segments = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod1_segmentsChoices, 0 )
		self.lod1_segments.SetSelection( 0 )
		self.lod1_segments.Hide()
		
		fgSizer28.Add( self.lod1_segments, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod2 = wx.CheckBox( sbSizer11.GetStaticBox(), wx.ID_ANY, u"LOD2", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer28.Add( self.lod2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod2_geomtypeChoices = []
		self.lod2_geomtype = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod2_geomtypeChoices, 0 )
		self.lod2_geomtype.SetSelection( 0 )
		self.lod2_geomtype.Enable( False )
		
		fgSizer28.Add( self.lod2_geomtype, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod2_segments_text = wx.StaticText( sbSizer11.GetStaticBox(), wx.ID_ANY, u"segments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lod2_segments_text.Wrap( -1 )
		
		self.lod2_segments_text.Hide()
		
		fgSizer28.Add( self.lod2_segments_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod2_segmentsChoices = []
		self.lod2_segments = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod2_segmentsChoices, 0 )
		self.lod2_segments.SetSelection( 0 )
		self.lod2_segments.Hide()
		
		fgSizer28.Add( self.lod2_segments, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod3 = wx.CheckBox( sbSizer11.GetStaticBox(), wx.ID_ANY, u"LOD3", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer28.Add( self.lod3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod3_geomtypeChoices = []
		self.lod3_geomtype = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod3_geomtypeChoices, 0 )
		self.lod3_geomtype.SetSelection( 0 )
		self.lod3_geomtype.Enable( False )
		
		fgSizer28.Add( self.lod3_geomtype, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod3_segments_text = wx.StaticText( sbSizer11.GetStaticBox(), wx.ID_ANY, u"segments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lod3_segments_text.Wrap( -1 )
		
		self.lod3_segments_text.Hide()
		
		fgSizer28.Add( self.lod3_segments_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod3_segmentsChoices = []
		self.lod3_segments = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod3_segmentsChoices, 0 )
		self.lod3_segments.SetSelection( 0 )
		self.lod3_segments.Hide()
		
		fgSizer28.Add( self.lod3_segments, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod4 = wx.CheckBox( sbSizer11.GetStaticBox(), wx.ID_ANY, u"LOD4", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer28.Add( self.lod4, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod4_geomtypeChoices = []
		self.lod4_geomtype = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod4_geomtypeChoices, 0 )
		self.lod4_geomtype.SetSelection( 0 )
		self.lod4_geomtype.Enable( False )
		
		fgSizer28.Add( self.lod4_geomtype, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.lod4_segments_text = wx.StaticText( sbSizer11.GetStaticBox(), wx.ID_ANY, u"segments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lod4_segments_text.Wrap( -1 )
		
		self.lod4_segments_text.Hide()
		
		fgSizer28.Add( self.lod4_segments_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		lod4_segmentsChoices = []
		self.lod4_segments = wx.Choice( sbSizer11.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lod4_segmentsChoices, 0 )
		self.lod4_segments.SetSelection( 0 )
		self.lod4_segments.Hide()
		
		fgSizer28.Add( self.lod4_segments, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		sbSizer11.Add( fgSizer28, 1, wx.EXPAND, 5 )
		
		
		fgSizer4.Add( sbSizer11, 1, wx.EXPAND, 5 )
		
		self.m_staticline10 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer4.Add( self.m_staticline10, 0, wx.EXPAND |wx.ALL, 5 )
		
		fgSizer13 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer13.SetFlexibleDirection( wx.BOTH )
		fgSizer13.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.progress = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 320,26 ), wx.GA_HORIZONTAL )
		self.progress.SetValue( 0 ) 
		fgSizer13.Add( self.progress, 0, wx.ALL, 5 )
		
		self.buttonExport = wx.Button( self, wx.ID_ANY, u"Export", wx.DefaultPosition, wx.Size( 90,-1 ), 0 )
		self.buttonExport.SetToolTip( u"Start CityGML Export" )
		
		fgSizer13.Add( self.buttonExport, 0, wx.ALL, 5 )
		
		
		fgSizer4.Add( fgSizer13, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( fgSizer4 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.buttonBrowse.Bind( wx.EVT_BUTTON, self.on_browse )
		self.choiceHeight.Bind( wx.EVT_CHOICE, self.check_geometries_to_generate )
		self.choiceTrunk.Bind( wx.EVT_CHOICE, self.check_geometries_to_generate )
		self.choiceCrown.Bind( wx.EVT_CHOICE, self.check_geometries_to_generate )
		self.lod1.Bind( wx.EVT_CHECKBOX, self.on_lod1_checkbox )
		self.lod1_geomtype.Bind( wx.EVT_CHOICE, self.on_lod1_choice )
		self.lod2.Bind( wx.EVT_CHECKBOX, self.on_lod2_checkbox )
		self.lod2_geomtype.Bind( wx.EVT_CHOICE, self.on_lod2_choice )
		self.lod3.Bind( wx.EVT_CHECKBOX, self.on_lod3_checkbox )
		self.lod3_geomtype.Bind( wx.EVT_CHOICE, self.on_lod3_choice )
		self.lod4.Bind( wx.EVT_CHECKBOX, self.on_lod4_checkbox )
		self.lod4_geomtype.Bind( wx.EVT_CHOICE, self.on_lod4_choice )
		self.buttonExport.Bind( wx.EVT_BUTTON, self.on_export )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_browse( self, event ):
		event.Skip()
	
	def check_geometries_to_generate( self, event ):
		event.Skip()
	
	
	
	def on_lod1_checkbox( self, event ):
		event.Skip()
	
	def on_lod1_choice( self, event ):
		event.Skip()
	
	def on_lod2_checkbox( self, event ):
		event.Skip()
	
	def on_lod2_choice( self, event ):
		event.Skip()
	
	def on_lod3_checkbox( self, event ):
		event.Skip()
	
	def on_lod3_choice( self, event ):
		event.Skip()
	
	def on_lod4_checkbox( self, event ):
		event.Skip()
	
	def on_lod4_choice( self, event ):
		event.Skip()
	
	def on_export( self, event ):
		event.Skip()
	

###########################################################################
## Class data_panel
###########################################################################

class data_panel ( wx.Panel ):
	
	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )
		
		bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		self.grid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.grid.CreateGrid( 0, 0 )
		self.grid.EnableEditing( False )
		self.grid.EnableGridLines( True )
		self.grid.EnableDragGridSize( False )
		self.grid.SetMargins( 0, 0 )
		
		# Columns
		self.grid.EnableDragColMove( True )
		self.grid.EnableDragColSize( False )
		self.grid.SetColLabelSize( 30 )
		self.grid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.grid.EnableDragRowSize( True )
		self.grid.SetRowLabelSize( 80 )
		self.grid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.grid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		bSizer2.Add( self.grid, 0, wx.ALL, 5 )
		
		
		self.SetSizer( bSizer2 )
		self.Layout()
		bSizer2.Fit( self )
	
	def __del__( self ):
		pass
	

###########################################################################
## Class import_dem
###########################################################################

class import_dem ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Import DEM", pos = wx.DefaultPosition, size = wx.Size( 441,443 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer18 = wx.FlexGridSizer( 5, 1, 0, 0 )
		fgSizer18.SetFlexibleDirection( wx.BOTH )
		fgSizer18.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		fgSizer71 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer71.SetFlexibleDirection( wx.BOTH )
		fgSizer71.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.filepat_textbox = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), wx.TE_READONLY )
		fgSizer71.Add( self.filepat_textbox, 0, wx.ALL, 5 )
		
		self.buttonBrowse = wx.Button( self, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.Size( 90,-1 ), 0 )
		self.buttonBrowse.SetToolTip( u"Browse to select DEM text file" )
		
		fgSizer71.Add( self.buttonBrowse, 0, wx.ALL, 5 )
		
		
		fgSizer18.Add( fgSizer71, 1, wx.EXPAND, 5 )
		
		sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"File Properties" ), wx.VERTICAL )
		
		fgSizer20 = wx.FlexGridSizer( 1, 4, 0, 0 )
		fgSizer20.SetFlexibleDirection( wx.BOTH )
		fgSizer20.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText37 = wx.StaticText( sbSizer7.GetStaticBox(), wx.ID_ANY, u"Encoding:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText37.Wrap( -1 )
		
		fgSizer20.Add( self.m_staticText37, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.encoding = wx.TextCtrl( sbSizer7.GetStaticBox(), wx.ID_ANY, u"utf-8", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.encoding.SetToolTip( u"enter encoding of file" )
		
		fgSizer20.Add( self.encoding, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText38 = wx.StaticText( sbSizer7.GetStaticBox(), wx.ID_ANY, u"Delimiter:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText38.Wrap( -1 )
		
		fgSizer20.Add( self.m_staticText38, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		delimChoices = [ u"Space", u"Comma", u"Tabulator", u"Semicolon" ]
		self.delim = wx.Choice( sbSizer7.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, delimChoices, 0 )
		self.delim.SetSelection( 0 )
		self.delim.SetToolTip( u"select file delimiter" )
		
		fgSizer20.Add( self.delim, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		sbSizer7.Add( fgSizer20, 1, wx.EXPAND, 5 )
		
		self.contains_columns = wx.CheckBox( sbSizer7.GetStaticBox(), wx.ID_ANY, u"First line in file contains column names", wx.DefaultPosition, wx.DefaultSize, 0 )
		sbSizer7.Add( self.contains_columns, 0, wx.ALL, 5 )
		
		
		fgSizer18.Add( sbSizer7, 1, wx.EXPAND, 5 )
		
		sbSizer8 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Geometry Properties" ), wx.VERTICAL )
		
		fgSizer181 = wx.FlexGridSizer( 2, 4, 0, 0 )
		fgSizer181.SetFlexibleDirection( wx.BOTH )
		fgSizer181.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText39 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Easting", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText39, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		xvalueChoices = []
		self.xvalue = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, xvalueChoices, 0 )
		self.xvalue.SetSelection( 0 )
		self.xvalue.SetToolTip( u"Select easting column" )
		
		fgSizer181.Add( self.xvalue, 0, wx.ALL, 5 )
		
		self.m_staticText40 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Northing", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText40.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText40, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		yvalueChoices = []
		self.yvalue = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, yvalueChoices, 0 )
		self.yvalue.SetSelection( 0 )
		self.yvalue.SetToolTip( u"Select northing column" )
		
		fgSizer181.Add( self.yvalue, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText41 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Height", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText41.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText41, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		heightvalueChoices = []
		self.heightvalue = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, heightvalueChoices, 0 )
		self.heightvalue.SetSelection( 0 )
		self.heightvalue.SetToolTip( u"select height column" )
		
		fgSizer181.Add( self.heightvalue, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText42 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"EPSG", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText42.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText42, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.epsg = wx.TextCtrl( sbSizer8.GetStaticBox(), wx.ID_ANY, u"5677", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.epsg.SetToolTip( u"select epsg code of DEM" )
		
		fgSizer181.Add( self.epsg, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		sbSizer8.Add( fgSizer181, 1, wx.EXPAND, 5 )
		
		
		fgSizer18.Add( sbSizer8, 1, wx.EXPAND, 5 )
		
		sbSizer9 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"File Preview" ), wx.VERTICAL )
		
		self.previewgrid = wx.grid.Grid( sbSizer9.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.previewgrid.CreateGrid( 0, 0 )
		self.previewgrid.EnableEditing( True )
		self.previewgrid.EnableGridLines( True )
		self.previewgrid.EnableDragGridSize( False )
		self.previewgrid.SetMargins( 0, 0 )
		
		# Columns
		self.previewgrid.EnableDragColMove( False )
		self.previewgrid.EnableDragColSize( True )
		self.previewgrid.SetColLabelSize( 30 )
		self.previewgrid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.previewgrid.EnableDragRowSize( True )
		self.previewgrid.SetRowLabelSize( 1 )
		self.previewgrid.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.previewgrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		sbSizer9.Add( self.previewgrid, 0, wx.ALL, 5 )
		
		
		fgSizer18.Add( sbSizer9, 1, wx.EXPAND, 5 )
		
		fgSizer21 = wx.FlexGridSizer( 0, 3, 0, 0 )
		fgSizer21.SetFlexibleDirection( wx.BOTH )
		fgSizer21.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.text_rowcount = wx.StaticText( self, wx.ID_ANY, u"0 elevation points imported          ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.text_rowcount.Wrap( -1 )
		
		self.text_rowcount.Enable( False )
		
		fgSizer21.Add( self.text_rowcount, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.importbutton = wx.Button( self, wx.ID_ANY, u"Import DEM", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.importbutton.Enable( False )
		self.importbutton.SetToolTip( u"Push button to start DEM Import" )
		
		fgSizer21.Add( self.importbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.next = wx.Button( self, wx.ID_ANY, u"Next", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.next.Enable( False )
		self.next.SetToolTip( u"When all DEM files are imported, push button to go to next step" )
		
		fgSizer21.Add( self.next, 0, wx.ALL, 5 )
		
		
		fgSizer18.Add( fgSizer21, 1, wx.ALIGN_RIGHT, 5 )
		
		
		self.SetSizer( fgSizer18 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.buttonBrowse.Bind( wx.EVT_BUTTON, self.on_browse )
		self.encoding.Bind( wx.EVT_TEXT_ENTER, self.refresh_preview )
		self.delim.Bind( wx.EVT_CHOICE, self.refresh_preview )
		self.contains_columns.Bind( wx.EVT_CHECKBOX, self.refresh_preview )
		self.importbutton.Bind( wx.EVT_BUTTON, self.on_import_dem )
		self.next.Bind( wx.EVT_BUTTON, self.on_next )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_browse( self, event ):
		event.Skip()
	
	def refresh_preview( self, event ):
		event.Skip()
	
	
	
	def on_import_dem( self, event ):
		event.Skip()
	
	def on_next( self, event ):
		event.Skip()
	

###########################################################################
## Class geom_props
###########################################################################

class geom_props ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Geometric Properties", pos = wx.DefaultPosition, size = wx.Size( 462,157 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer18 = wx.FlexGridSizer( 5, 1, 0, 0 )
		fgSizer18.SetFlexibleDirection( wx.BOTH )
		fgSizer18.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		sbSizer8 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Tree Geometry Properties" ), wx.VERTICAL )
		
		fgSizer181 = wx.FlexGridSizer( 2, 4, 0, 0 )
		fgSizer181.SetFlexibleDirection( wx.BOTH )
		fgSizer181.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText39 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Easting", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText39, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		xvalueChoices = []
		self.xvalue = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, xvalueChoices, 0 )
		self.xvalue.SetSelection( 0 )
		self.xvalue.SetToolTip( u"select easting column" )
		
		fgSizer181.Add( self.xvalue, 0, wx.ALL, 5 )
		
		self.m_staticText40 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Northing", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText40.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText40, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		yvalueChoices = []
		self.yvalue = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, yvalueChoices, 0 )
		self.yvalue.SetSelection( 0 )
		self.yvalue.SetToolTip( u"select northing column" )
		
		fgSizer181.Add( self.yvalue, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText62 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"ID", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText62.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText62, 0, wx.ALL, 5 )
		
		idChoices = []
		self.id = wx.Choice( sbSizer8.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, idChoices, 0 )
		self.id.SetSelection( 0 )
		self.id.SetToolTip( u"select ID column" )
		
		fgSizer181.Add( self.id, 0, wx.ALL, 5 )
		
		self.m_staticText42 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"EPSG", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText42.Wrap( -1 )
		
		fgSizer181.Add( self.m_staticText42, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.epsg = wx.TextCtrl( sbSizer8.GetStaticBox(), wx.ID_ANY, u"5677", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer181.Add( self.epsg, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		sbSizer8.Add( fgSizer181, 1, wx.EXPAND, 5 )
		
		
		fgSizer18.Add( sbSizer8, 1, wx.EXPAND, 5 )
		
		fgSizer21 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer21.SetFlexibleDirection( wx.BOTH )
		fgSizer21.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.text_rowcount = wx.StaticText( self, wx.ID_ANY, u"0 elevation points imported          ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.text_rowcount.Wrap( -1 )
		
		self.text_rowcount.Enable( False )
		
		fgSizer21.Add( self.text_rowcount, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.add = wx.Button( self, wx.ID_ANY, u"Add Geoms", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.add.Enable( False )
		
		fgSizer21.Add( self.add, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		
		fgSizer18.Add( fgSizer21, 1, wx.ALIGN_RIGHT, 5 )
		
		
		self.SetSizer( fgSizer18 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.xvalue.Bind( wx.EVT_CHOICE, self.validate )
		self.yvalue.Bind( wx.EVT_CHOICE, self.validate )
		self.id.Bind( wx.EVT_CHOICE, self.validate )
		self.epsg.Bind( wx.EVT_TEXT, self.validate )
		self.add.Bind( wx.EVT_BUTTON, self.on_add )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def validate( self, event ):
		event.Skip()
	
	
	
	
	def on_add( self, event ):
		event.Skip()
	

###########################################################################
## Class GrabHeight
###########################################################################

class GrabHeight ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Assign Height values", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer36 = wx.FlexGridSizer( 4, 1, 0, 0 )
		fgSizer36.SetFlexibleDirection( wx.BOTH )
		fgSizer36.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		fgSizer33 = wx.FlexGridSizer( 1, 4, 0, 0 )
		fgSizer33.SetFlexibleDirection( wx.BOTH )
		fgSizer33.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText63 = wx.StaticText( self, wx.ID_ANY, u"ID", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText63.Wrap( -1 )
		
		fgSizer33.Add( self.m_staticText63, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		idChoices = []
		self.id = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, idChoices, 0 )
		self.id.SetSelection( 0 )
		self.id.SetToolTip( u"select ID column" )
		
		fgSizer33.Add( self.id, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText64 = wx.StaticText( self, wx.ID_ANY, u"Geometry", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText64.Wrap( -1 )
		
		fgSizer33.Add( self.m_staticText64, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		geomChoices = []
		self.geom = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, geomChoices, 0 )
		self.geom.SetSelection( 0 )
		self.geom.SetToolTip( u"select geometry column" )
		
		fgSizer33.Add( self.geom, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		fgSizer36.Add( fgSizer33, 1, wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		fgSizer27 = wx.FlexGridSizer( 2, 2, 0, 0 )
		fgSizer27.SetFlexibleDirection( wx.BOTH )
		fgSizer27.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.use_defaultheight = wx.CheckBox( self, wx.ID_ANY, u"Default height (if tree is out of DEM range)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.use_defaultheight.SetToolTip( u"assign a default height to all trees that are not within DEM range" )
		
		fgSizer27.Add( self.use_defaultheight, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		self.default_height = wx.TextCtrl( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.default_height.Enable( False )
		
		fgSizer27.Add( self.default_height, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.use_radius = wx.CheckBox( self, wx.ID_ANY, u"Use search radius (m) (faster)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.use_radius.SetToolTip( u"use a search radius to speed things up. At least four DEM points must be within this radius." )
		
		fgSizer27.Add( self.use_radius, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.radius = wx.TextCtrl( self, wx.ID_ANY, u"5", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.radius.SetMaxLength( 4 ) 
		self.radius.Enable( False )
		
		fgSizer27.Add( self.radius, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		
		fgSizer36.Add( fgSizer27, 1, wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		self.m_staticline10 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer36.Add( self.m_staticline10, 0, wx.EXPAND |wx.ALL, 5 )
		
		fgSizer34 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer34.SetFlexibleDirection( wx.BOTH )
		fgSizer34.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 250,-1 ), wx.GA_HORIZONTAL )
		self.gauge.SetValue( 0 ) 
		fgSizer34.Add( self.gauge, 0, wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, 5 )
		
		self.assign = wx.Button( self, wx.ID_ANY, u"Assign", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.assign.Enable( False )
		self.assign.SetToolTip( u"Start assigning process" )
		
		fgSizer34.Add( self.assign, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )
		
		
		fgSizer36.Add( fgSizer34, 1, wx.ALIGN_RIGHT, 5 )
		
		
		self.SetSizer( fgSizer36 )
		self.Layout()
		fgSizer36.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.id.Bind( wx.EVT_CHOICE, self.validate )
		self.geom.Bind( wx.EVT_CHOICE, self.validate )
		self.use_defaultheight.Bind( wx.EVT_CHECKBOX, self.on_checkbox_defaultheight_hit )
		self.use_radius.Bind( wx.EVT_CHECKBOX, self.on_checkbox_radius_hit )
		self.assign.Bind( wx.EVT_BUTTON, self.on_assign )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def validate( self, event ):
		event.Skip()
	
	
	def on_checkbox_defaultheight_hit( self, event ):
		event.Skip()
	
	def on_checkbox_radius_hit( self, event ):
		event.Skip()
	
	def on_assign( self, event ):
		event.Skip()
	

###########################################################################
## Class add_vegetation_code
###########################################################################

class add_vegetation_code ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Add CityGML Vegetation Code", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer26 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer26.SetFlexibleDirection( wx.BOTH )
		fgSizer26.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		choice_vegetation_colChoices = []
		self.choice_vegetation_col = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), choice_vegetation_colChoices, 0 )
		self.choice_vegetation_col.SetSelection( 0 )
		self.choice_vegetation_col.SetToolTip( u"select column that contains biological tree species names" )
		
		fgSizer26.Add( self.choice_vegetation_col, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.add_code = wx.Button( self, wx.ID_ANY, u"Add Code", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.add_code.Enable( False )
		
		fgSizer26.Add( self.add_code, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		
		self.SetSizer( fgSizer26 )
		self.Layout()
		fgSizer26.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.choice_vegetation_col.Bind( wx.EVT_CHOICE, self.on_choice )
		self.add_code.Bind( wx.EVT_BUTTON, self.on_add_code )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_choice( self, event ):
		event.Skip()
	
	def on_add_code( self, event ):
		event.Skip()
	

###########################################################################
## Class MyDialog10
###########################################################################

class MyDialog10 ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Add default reference height", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer30 = wx.FlexGridSizer( 2, 2, 0, 0 )
		fgSizer30.SetFlexibleDirection( wx.BOTH )
		fgSizer30.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText59 = wx.StaticText( self, wx.ID_ANY, u"default reference height (m)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText59.Wrap( -1 )
		
		fgSizer30.Add( self.m_staticText59, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_textCtrl15 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_textCtrl15.SetMaxLength( 6 ) 
		fgSizer30.Add( self.m_textCtrl15, 0, wx.ALL, 5 )
		
		
		fgSizer30.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_button13 = wx.Button( self, wx.ID_ANY, u"Assign", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer30.Add( self.m_button13, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )
		
		
		self.SetSizer( fgSizer30 )
		self.Layout()
		fgSizer30.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.m_button13.Bind( wx.EVT_BUTTON, self.on_assign )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_assign( self, event ):
		event.Skip()
	

