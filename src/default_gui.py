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
		
		self.Export = wx.Menu()
		self.export_citygml = wx.MenuItem( self.Export, wx.ID_ANY, u"CityGML", wx.EmptyString, wx.ITEM_NORMAL )
		self.Export.Append( self.export_citygml )
		
		self.file.AppendSubMenu( self.Export, u"Export" )
		
		self.test = wx.MenuItem( self.file, wx.ID_ANY, u"Test", wx.EmptyString, wx.ITEM_NORMAL )
		self.file.Append( self.test )
		
		self.m_menubar7.Append( self.file, u"File" ) 
		
		self.view = wx.Menu()
		self.col_properties = wx.MenuItem( self.view, wx.ID_ANY, u"Column Properties", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.col_properties )
		
		self.reset_col_position = wx.MenuItem( self.view, wx.ID_ANY, u"Reset Column Position", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.reset_col_position )
		
		self.reset_col_visiblity = wx.MenuItem( self.view, wx.ID_ANY, u"Show All Columns", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.reset_col_visiblity )
		
		self.stats = wx.MenuItem( self.view, wx.ID_ANY, u"Statistics", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.stats )
		
		self.m_menubar7.Append( self.view, u"View" ) 
		
		self.analyze = wx.Menu()
		self.dublicates = wx.MenuItem( self.analyze, wx.ID_ANY, u"Check for Duplicates by ID", wx.EmptyString, wx.ITEM_NORMAL )
		self.analyze.Append( self.dublicates )
		
		self.m_menubar7.Append( self.analyze, u"Analyze" ) 
		
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
	

###########################################################################
## Class MyDialog1
###########################################################################

class MyDialog1 ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_gauge1 = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.m_gauge1.SetValue( 0 ) 
		bSizer2.Add( self.m_gauge1, 0, wx.ALL, 5 )
		
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"50/100 eingelesen", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		
		bSizer2.Add( self.m_staticText1, 0, wx.ALL, 5 )
		
		
		self.SetSizer( bSizer2 )
		self.Layout()
		bSizer2.Fit( self )
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

###########################################################################
## Class OnOpenDialog
###########################################################################

class OnOpenDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"CSV import options", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.STAY_ON_TOP )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		fgSizer4 = wx.FlexGridSizer( 3, 1, 0, 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"unique tree IDs" ), wx.VERTICAL )
		
		self.generate_ID_box = wx.CheckBox( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Generate unique tree IDs from CSV file columns", wx.DefaultPosition, wx.DefaultSize, 0 )
		sbSizer1.Add( self.generate_ID_box, 0, wx.ALL, 5 )
		
		self.m_staticText4 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"ArbokaTransformer can create an ID out of two\ncolumns in the CSV table for each entry. \nGenerated ID column will be highlighted  in table.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		
		sbSizer1.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )
		
		self.IdText_Col1 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Column 1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.IdText_Col1.Wrap( -1 )
		
		self.IdText_Col1.Enable( False )
		
		gSizer2.Add( self.IdText_Col1, 0, wx.ALL, 5 )
		
		id_col1Choices = []
		self.id_col1 = wx.Choice( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, id_col1Choices, 0 )
		self.id_col1.SetSelection( 0 )
		self.id_col1.Enable( False )
		
		gSizer2.Add( self.id_col1, 0, wx.ALL, 5 )
		
		self.IdText_Col2 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Column 2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.IdText_Col2.Wrap( -1 )
		
		self.IdText_Col2.Enable( False )
		
		gSizer2.Add( self.IdText_Col2, 0, wx.ALL, 5 )
		
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
		self.generate_ID_box.Bind( wx.EVT_CHECKBOX, self.id_checkbox_event )
		self.ok_button.Bind( wx.EVT_BUTTON, self.on_ok )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def id_checkbox_event( self, event ):
		event.Skip()
	
	def on_ok( self, event ):
		event.Skip()
	

###########################################################################
## Class OnCheckDuplicateIdDialog
###########################################################################

class OnCheckDuplicateIdDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 353,304 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.Size( 353,304 ), wx.Size( 353,304 ) )
		
		fgSizer2 = wx.FlexGridSizer( 5, 1, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"This analysis tool allows to check all data loaded for duplicates.\nPlease select a column that contains ID values for each tree", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		
		fgSizer2.Add( self.m_staticText7, 0, wx.ALL, 5 )
		
		gSizer3 = wx.GridSizer( 1, 2, 0, 0 )
		
		self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"Select ID field", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )
		
		gSizer3.Add( self.m_staticText8, 0, wx.ALL, 5 )
		
		IdColumnsChoices = []
		self.IdColumns = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, IdColumnsChoices, 0 )
		self.IdColumns.SetSelection( 0 )
		gSizer3.Add( self.IdColumns, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( gSizer3, 1, wx.EXPAND, 5 )
		
		self.analyze = wx.Button( self, wx.ID_ANY, u"Analyze", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.analyze, 0, wx.ALL, 5 )
		
		self.InfoText = wx.StaticText( self, wx.ID_ANY, u"The following Duplicate values have been found:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.InfoText.Wrap( -1 )
		
		self.InfoText.Hide()
		
		fgSizer2.Add( self.InfoText, 0, wx.ALL, 5 )
		
		self.DuplicateGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		
		# Grid
		self.DuplicateGrid.CreateGrid( 0, 2 )
		self.DuplicateGrid.EnableEditing( False )
		self.DuplicateGrid.EnableGridLines( True )
		self.DuplicateGrid.EnableDragGridSize( False )
		self.DuplicateGrid.SetMargins( 0, 0 )
		
		# Columns
		self.DuplicateGrid.SetColSize( 0, 224 )
		self.DuplicateGrid.SetColSize( 1, 25 )
		self.DuplicateGrid.EnableDragColMove( False )
		self.DuplicateGrid.EnableDragColSize( True )
		self.DuplicateGrid.SetColLabelSize( 30 )
		self.DuplicateGrid.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.DuplicateGrid.EnableDragRowSize( False )
		self.DuplicateGrid.SetRowLabelSize( 80 )
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
## Class data_panel
###########################################################################

class data_panel ( wx.Panel ):
	
	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 1000,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
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
	
	def __del__( self ):
		pass
	

