#!/usr/bin/env python
# ####-*- coding: utf-8 -*-
#
# @file    Moccasin_GUI.py
# @brief   Graphical User Interface (GUI) for Moccasin
# @author  Harold Gomez
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
#

import wx
import wx.xrc
import os
import webbrowser 

#These imports will disappear when logic is made into a separate module
import requests
import sys
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile
sys.path.append('../converter/')
from converter import *
sys.path.append('../matlab_parser')
from matlab_parser import *


###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Welcome to Moccasin", pos = wx.DefaultPosition, size = wx.Size( 564,667 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
		
		#Construct a status bar
		self.statusBar = self.CreateStatusBar( 1, wx.ST_SIZEGRIP|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER, wx.ID_ANY )
		self.statusBar.SetToolTipString( u"Status" )
		self.statusBar.SetStatusText( u"Ready" )

		#Construct a menu bar
		self.menuBar = wx.MenuBar( 0 )

		self.fileMenu = wx.Menu()
		self.openFile = wx.MenuItem( self.fileMenu, wx.ID_OPEN, u"Open"+ u"\t" + u"Ctrl+O", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.openFile )		
		self.saveFile = wx.MenuItem( self.fileMenu, wx.ID_SAVE, u"Save"+ u"\t" + u"Ctrl+S", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.saveFile )
		self.fileMenu.AppendSeparator()
		self.exit = wx.MenuItem( self.fileMenu, wx.ID_EXIT, u"Exit"+ u"\t" + u"Alt+F4", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.exit )
		
		self.menuBar.Append( self.fileMenu, u"File" ) 
		
		self.editMenu = wx.Menu()
		self.clear = wx.MenuItem( self.editMenu, wx.ID_CLEAR, u"Clear"+ u"\t" + u"Ctrl+L", wx.EmptyString, wx.ITEM_NORMAL )
		self.editMenu.AppendItem( self.clear )
		
		self.menuBar.Append( self.editMenu, u"Edit" ) 
		
		self.runMenu = wx.Menu()
		self.convertFile = wx.MenuItem( self.runMenu, wx.ID_ANY, u"Convert"+ u"\t" + u"Ctrl+C", wx.EmptyString, wx.ITEM_NORMAL )
		self.runMenu.AppendItem( self.convertFile )
		self.seeOptions = wx.MenuItem( self.runMenu, wx.ID_ANY, u"Options", wx.EmptyString, wx.ITEM_NORMAL )
		self.runMenu.AppendItem( self.seeOptions )
		
		self.menuBar.Append( self.runMenu, u"Run" ) 
		
		self.windowMenu = wx.Menu()
		self.close = wx.MenuItem( self.windowMenu, wx.ID_CLOSE, u"CloseAll", wx.EmptyString, wx.ITEM_NORMAL )
		self.windowMenu.AppendItem( self.close )
		
		self.menuBar.Append( self.windowMenu, u"Window" ) 
		
		self.helpMenu = wx.Menu()
		self.helpItem = wx.MenuItem( self.helpMenu, wx.ID_HELP, u"Moccasin Help"+ u"\t" + u"F1", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.helpItem )
		
		self.helpMenu.AppendSeparator()
		
		self.license = wx.MenuItem( self.helpMenu, wx.ID_ANY, u"GNU General Public License", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.license )
		
		self.about = wx.MenuItem( self.helpMenu, wx.ID_ABOUT, u"About Moccasin", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.about )
		
		self.menuBar.Append( self.helpMenu, u"Help" ) 
		
		self.SetMenuBar( self.menuBar )

		#Add sizers(3) and elements for matlab and translated text
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.SetMinSize( wx.Size( 1,3 ) ) 
		mainSizer.AddSpacer( ( 0, 1), 0, wx.EXPAND|wx.TOP, 5 )
		
		topPanelSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		topPanelSizer.SetMinSize( wx.Size( 2,2 ) ) 
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u" Please choose a file for conversion", wx.Point( -1,-1 ), wx.Size( -1,-1 ), 0 )
		self.m_staticText7.Wrap( -1 )
		self.m_staticText7.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		self.m_staticText7.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )

		#Top sizer
		topPanelSizer.Add( self.m_staticText7, 0, wx.ALL|wx.EXPAND, 5 )	
		self.filePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Choose a file", u"*.m", wx.DefaultPosition, wx.Size( 225,-1 ), wx.FLP_DEFAULT_STYLE )
		
		topPanelSizer.Add( self.filePicker, 0, wx.ALL, 5 )
		self.staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 1,-1 ), wx.LI_VERTICAL|wx.DOUBLE_BORDER|wx.TRANSPARENT_WINDOW )
		self.staticline1.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 74, 90, 90, False, "Arial" ) )
		self.staticline1.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )
		self.staticline1.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )
		topPanelSizer.Add( self.staticline1, 0, wx.EXPAND |wx.ALL, 5 )		
		self.convertButton = wx.Button( self, wx.ID_ANY, u"Convert", wx.DefaultPosition, wx.DefaultSize, 0 )
		topPanelSizer.Add( self.convertButton, 0, wx.ALL|wx.EXPAND, 5 )
		mainSizer.Add( topPanelSizer, 0, wx.EXPAND, 5 )

		#Mid sizer
		midPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Matlab File" ), wx.VERTICAL )
		self.matlabTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
		self.matlabTextCtrl.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )
		self.matlabTextCtrl.SetToolTipString( u"Input Matlab file for conversion" )
		midPanelSizer.Add( self.matlabTextCtrl, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
		mainSizer.Add( midPanelSizer, 1, wx.EXPAND, 5 )

		#Bottom sizer
		bottomPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Converted File" ), wx.VERTICAL )		
		self.convertedTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
		self.convertedTextCtrl.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString ) )
		self.convertedTextCtrl.SetToolTipString( u"Output file after conversion" )
		bottomPanelSizer.Add( self.convertedTextCtrl, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
		mainSizer.Add( bottomPanelSizer, 1, wx.EXPAND, 5 )

		#Set frame sizer
		self.SetSizer( mainSizer )
		self.Layout()
		self.Centre( wx.BOTH )
		
		# Connect Events with GUI elements
		self.Bind( wx.EVT_MENU, self.onOpen, id = self.openFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onSave, id = self.saveFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onExit, id = self.exit.GetId() )
		self.Bind( wx.EVT_MENU, self.onClear, id = self.clear.GetId() )
		self.Bind( wx.EVT_MENU, self.onConvert, id = self.convertFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onOptions, id = self.seeOptions.GetId() )
		self.Bind( wx.EVT_MENU, self.onCloseAll, id = self.close.GetId() )
		self.Bind( wx.EVT_MENU, self.onHelp, id = self.helpItem.GetId() )
		self.Bind( wx.EVT_MENU, self.onLicense, id = self.license.GetId() )
		self.Bind( wx.EVT_MENU, self.onAbout, id = self.about.GetId() )
		self.Bind( wx.EVT_FILEPICKER_CHANGED, self.onFilePicker, id = self.filePicker.GetId())
		self.Bind( wx.EVT_BUTTON, self.onConvert, id = self.convertButton.GetId())

		def __del__( self ):
			pass
	    
	# Virtual event handlers, overide them in your derived class
	def onOpen(self, event):
		dirname=u""
		dlg = wx.FileDialog(self, u"Choose a file", dirname, u"", u"*.m", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetFilename()
			dirname = dlg.GetDirectory()
			f = open(os.path.join(dirname, filename), 'r')
			self.matlabTextCtrl.SetValue(f.read())
			f.close()
		dlg.Destroy()

	def onFilePicker(self, event):
		path=self.filePicker.GetPath()
		f = open(path, 'r')
		self.matlabTextCtrl.SetValue(f.read())
		f.close()		

	def onSave( self, event ):
		if(not self.convertedTextCtrl.IsEmpty()):
			dlg = wx.FileDialog(self, u"Save SBML file", u"", u"", u"SBML files (*.xml)|*.xml", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
			if dlg.ShowModal() == wx.ID_CANCEL:
				return
			print(dlg.GetPath())
			output = open(dlg.GetPath(), 'w')
			output.write(self.convertedTextCtrl.GetValue())
			output.close()			
		else:
			dlg = wx.MessageDialog(self, u"Please convert a matlab file before saving", u"Warning", wx.OK)
			dlg.ShowModal()
			dlg.Destroy()
	
	def onExit( self, event ):		
		self.Close(True)
	
	def onClear( self, event ):
		self.matlabTextCtrl.SetValue(u"")
		self.convertedTextCtrl.SetValue(u"")
	
	def onConvert( self, event ):
		event.Skip()
##		try:
##			parser = MatlabGrammar()
##			parse_results = parser.parse_string(self.matlabTextCtrl.GetValue())
##			#Create temp file storing XPP model version
##			parse_results=parse_results.replace("text:u","")
##			with NamedTemporaryFile(suffix= ".ode", delete=False) as xpp_file:
##				xpp_file.write(create_raterule_model(parse_results))
##			files = {'file':open(xpp_file.name)}                
##			#Access Biocham to curate and convert equations to reactions
##			url = 'http://lifeware.inria.fr/biocham/online/rest/export'
##			data = {'exportTo':'sbml', 'curate':'true'}
##			response = requests.post(url, files=files, data=data)
##			del files
##			self.convertedTextCtrl.SetValue(response.content)
##			os.unlink(xpp_file.name)
##
##		except IOError as err:
##			print("error: {0}".format(err))			

	
	def onOptions( self, event ):
		event.Skip()
	
	def onCloseAll( self, event ):
		self.Close(True)

	def onHelp( self, event ):
		href=u"https://github.com/sbmlteam/moccasin/blob/setupFix_branch/docs/quickstart.md"
		wx.BeginBusyCursor() 
		webbrowser.open(href) 
		wx.EndBusyCursor()
		
	def onLicense( self, event ):
		href=u"http://www.gnu.org/licenses/gpl-2.0.html"
		wx.BeginBusyCursor() 
		webbrowser.open(href) 
		wx.EndBusyCursor()
            
	def onAbout( self, event ):
		dlg = wx.MessageDialog(self, u"MOCCASIN stands for (Model ODE Converter for Creating Awesome SBML INteroperability). It is a project to develop a user-assisted converter that can take MATLAB or Octave ODE-based models in biology and translate them into SBML format.", u"About Moccasin", wx.OK)
		dlg.ShowModal() 
		dlg.Destroy()
	

		
app = wx.App(False)
frame = MainFrame(None)
frame.Show()
app.MainLoop()
