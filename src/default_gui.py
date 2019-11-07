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
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1366,768 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		self.m_menubar7 = wx.MenuBar( 0 )
		self.file = wx.Menu()
		self.open = wx.MenuItem( self.file, wx.ID_ANY, u"Open", wx.EmptyString, wx.ITEM_NORMAL )
		self.file.Append( self.open )
		
		self.Export = wx.Menu()
		self.export_citygml = wx.MenuItem( self.Export, wx.ID_ANY, u"CityGML", wx.EmptyString, wx.ITEM_NORMAL )
		self.Export.Append( self.export_citygml )
		
		self.file.AppendSubMenu( self.Export, u"Export" )
		
		self.m_menubar7.Append( self.file, u"File" ) 
		
		self.view = wx.Menu()
		self.col_properties = wx.MenuItem( self.view, wx.ID_ANY, u"Column Properties", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.col_properties )
		
		self.stats = wx.MenuItem( self.view, wx.ID_ANY, u"Statistics", wx.EmptyString, wx.ITEM_NORMAL )
		self.view.Append( self.stats )
		
		self.m_menubar7.Append( self.view, u"View" ) 
		
		self.SetMenuBar( self.m_menubar7 )
		
		self.m_statusBar3 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.OnClose )
		self.Bind( wx.EVT_MENU, self.on_menu_open, id = self.open.GetId() )
		self.Bind( wx.EVT_MENU, self.on_menu_export_citygml, id = self.export_citygml.GetId() )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnClose( self, event ):
		event.Skip()
	
	def on_menu_open( self, event ):
		event.Skip()
	
	def on_menu_export_citygml( self, event ):
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
		self.grid.CreateGrid( 1, 0 )
		self.grid.EnableEditing( False )
		self.grid.EnableGridLines( True )
		self.grid.EnableDragGridSize( False )
		self.grid.SetMargins( 0, 0 )
		
		# Columns
		self.grid.EnableDragColMove( False )
		self.grid.EnableDragColSize( True )
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
	

