#!/usr/bin/env python
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

import os
import webbrowser
import requests
import sys
import wx
import wx.xrc
import wx.lib.agw.genericmessagedialog as GMD

from pkg_resources import get_distribution, DistributionNotFound

#Some of these imports will disappear when logic is made into a separate module
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile

sys.path.append('../matlab_parser')
sys.path.append('../converter')
from converter import *
from matlab_parser import *


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def network_available():
	'''Try to connect somewhere to test if a network is available.'''
	try:
		_ = requests.get('http://www.google.com', timeout=5)
		return True
	except requests.ConnectionError:
		return False
	
def getPackageVersion():
	project = "MOCCASIN"
	version = None  # required for initialization of globals
	try:
		version = get_distribution(project).version
	except DistributionNotFound:
		version = '(local)'
	return version

#Used for manually posts an event
def postSaveEvent( self, event):
	evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,self.saveFile.GetId())
	wx.PostEvent(self, evt)

#Checks that output is saved before it's lost
def saveOutput( self, event ):
	msg = "MOCCASIN output may be lost. Do you want to save?"
	dlg = GMD.GenericMessageDialog(self, msg, "Warning",agwStyle=wx.ICON_INFORMATION | wx.YES_NO)               
	if (not _IS_OUTPUT_SAVED and not self.convertedTextCtrl.IsEmpty()):
		if dlg.ShowModal() == wx.ID_YES:			
			postSaveEvent( self, event)
		return True
	dlg.Destroy()
	return False

# -----------------------------------------------------------------------------
# Global configuration constants
# -----------------------------------------------------------------------------

_BIOCHAM_URL = 'http://lifeware.inria.fr/biocham/online/rest/export'
_HELP_URL = "https://github.com/sbmlteam/moccasin/blob/setupFix_branch/docs/quickstart.md"
_LICENSE_URL = "https://www.gnu.org/licenses/lgpl.html"
_VERSION = "Version:  "+ getPackageVersion()
_IS_OUTPUT_SAVED = False
_SAVEAS_ODE = False #Used to save the right file format

# -----------------------------------------------------------------------------
# Graphical User Interface (GUI) definition
# -----------------------------------------------------------------------------
class MainFrame ( wx.Frame ):
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = "Welcome to MOCCASIN", pos = wx.DefaultPosition, size = wx.Size( 785,691 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		self.SetSizeHintsSz( wx.Size( 721,-1 ), wx.DefaultSize )
		self.SetExtraStyle( wx.FRAME_EX_METAL )		
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
		
		#Construct a status bar
		self.statusBar = self.CreateStatusBar(5, wx.ST_SIZEGRIP|wx.ALWAYS_SHOW_SB|wx.RAISED_BORDER, wx.ID_ANY )
		self.statusBar.SetFieldsCount(5)
		self.statusBar.SetToolTipString( "Status" )
		self.statusBar.SetStatusText("Ready",0)
		self.statusBar.SetStatusText(_VERSION ,4)
		
		#Construct a menu bar
		self.menuBar = wx.MenuBar( 0 )

		self.fileMenu = wx.Menu()
		self.openFile = wx.MenuItem( self.fileMenu, wx.ID_OPEN, "Open"+ "\t" + "Ctrl+O", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.openFile )		
		self.saveFile = wx.MenuItem( self.fileMenu, wx.ID_SAVE, "Save"+ "\t" + "Ctrl+S", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.saveFile )
		self.fileMenu.AppendSeparator()
		self.exit = wx.MenuItem( self.fileMenu, wx.ID_EXIT, "Exit"+ "\t" + "Alt+F4", wx.EmptyString, wx.ITEM_NORMAL )
		self.fileMenu.AppendItem( self.exit )
		
		self.menuBar.Append( self.fileMenu, "File" ) 
		
		self.editMenu = wx.Menu()
		self.clear = wx.MenuItem( self.editMenu, wx.ID_CLEAR, "Clear"+ "\t" + "Ctrl+L", wx.EmptyString, wx.ITEM_NORMAL )
		self.editMenu.AppendItem( self.clear )
		
		self.menuBar.Append( self.editMenu, "Edit" ) 
		
		self.runMenu = wx.Menu()
		self.convertFile = wx.MenuItem( self.runMenu, wx.ID_ANY, "Convert"+ "\t" + "Ctrl+C", wx.EmptyString, wx.ITEM_NORMAL )
		self.convertFile.Enable(0)
		self.runMenu.AppendItem( self.convertFile )		
		
		self.menuBar.Append( self.runMenu, "Run" ) 
		
		self.windowMenu = wx.Menu()
		self.close = wx.MenuItem( self.windowMenu, wx.ID_CLOSE, "CloseAll", wx.EmptyString, wx.ITEM_NORMAL )
		self.windowMenu.AppendItem( self.close )
		
		self.menuBar.Append( self.windowMenu, "Window" ) 
		
		self.helpMenu = wx.Menu()
		self.helpItem = wx.MenuItem( self.helpMenu, wx.ID_HELP, "MOCCASIN Help"+ "\t" + "F1", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.helpItem )
		
		self.helpMenu.AppendSeparator()
		
		self.license = wx.MenuItem( self.helpMenu, wx.ID_ANY, "GNU Lesser General Public License", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.license )
		
		self.about = wx.MenuItem( self.helpMenu, wx.ID_ABOUT, "About MOCCASIN", wx.EmptyString, wx.ITEM_NORMAL )
		self.helpMenu.AppendItem( self.about )
		
		self.menuBar.Append( self.helpMenu, "Help" ) 
		
		self.SetMenuBar( self.menuBar )

		#Add sizers(3) and elements for matlab and translated text
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.SetMinSize( wx.Size( 1,3 ) ) 
		mainSizer.AddSpacer( ( 0, 1), 0, wx.EXPAND|wx.TOP, 5 )

		#Top sizer
		topPanelSizer = wx.GridSizer( 1, 2, 0, 0 )

		fileConvSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "File conversion" ), wx.VERTICAL )
		gSizer3 = wx.GridSizer( 1, 2, 0, 0 )
		self.staticTextConv = wx.StaticText( self, wx.ID_ANY, "Choose a file for conversion", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticTextConv.Wrap( -1 )
		self.staticTextConv.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		gSizer3.Add( self.staticTextConv, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		self.convertButton = wx.Button( self, wx.ID_ANY, "Convert", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.convertButton.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial" ) )
		self.convertButton.Disable()
		gSizer3.Add( self.convertButton, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		fileConvSizer.Add( gSizer3, 2, wx.ALL|wx.EXPAND, 0 )
		bSizer2 = wx.BoxSizer( wx.VERTICAL )	
		bSizer2.SetMinSize( wx.Size( 1,1 ) ) 
		self.filePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", u"*.m", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer2.Add( self.filePicker, 0, wx.EXPAND, 2 )	
		fileConvSizer.Add( bSizer2, 2, wx.ALL|wx.EXPAND, 5 )
		topPanelSizer.Add( fileConvSizer, 0, wx.ALL|wx.EXPAND, 5 )
		
		sbSizer9 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Options" ), wx.VERTICAL )
		
		optionLayoutSizer = wx.GridSizer( 4, 3, 0, 0)
		self.staticTextOpt = wx.StaticText( self, wx.ID_ANY, "Variable encoding", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticTextOpt.Wrap( -1 )
		self.staticTextOpt.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		optionLayoutSizer.Add( self.staticTextOpt, 0, wx.ALL, 5 )
		self.varsAsSpecies = wx.RadioButton( self, wx.ID_ANY, "SBML Species", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		self.varsAsSpecies.SetToolTipString( "Represent model variables as species" )
		self.varsAsSpecies.SetValue( True ) 
		optionLayoutSizer.Add( self.varsAsSpecies, 0, wx.ALL, 5 )
		
		self.varsAsParams = wx.RadioButton( self, wx.ID_ANY, "SBML Parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.varsAsParams.SetToolTipString( "Represent model variables as parameters" )
		optionLayoutSizer.Add( self.varsAsParams, 0, wx.ALL, 5 )
		optionLayoutSizer.AddSpacer( ( 0, 1), 1, 0, 5 )
		optionLayoutSizer.AddSpacer( ( 0, 1), 1, 0, 5 )
		optionLayoutSizer.AddSpacer( ( 0, 1), 1, 0, 5 )
		self.modeType = wx.StaticText( self, wx.ID_ANY, "Output format", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.modeType.Wrap( -1 )
		self.modeType.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		optionLayoutSizer.Add( self.modeType, 0, wx.ALL, 5 )
		
		self.reactionBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML (reactions)", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		self.reactionBasedModel.SetToolTipString( "Convert into SBML (kinetics as reactions)" )
		self.reactionBasedModel.SetValue( True ) 
		optionLayoutSizer.Add( self.reactionBasedModel, 0, wx.ALL, 5 )
		
		self.xppModel = wx.RadioButton( self, wx.ID_ANY, "ODE", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.xppModel.SetToolTipString( "Convert into ODE file format (XPP)" )
		optionLayoutSizer.Add( self.xppModel, 0, wx.ALL, 5 )
		optionLayoutSizer.AddSpacer( ( 0, 1), 1, wx.EXPAND, 5 )
		
		self.equationBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML(equations)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.equationBasedModel.SetToolTipString( "Convert into SBML (kinetics as rate rules)" )
		optionLayoutSizer.Add( self.equationBasedModel, 0, wx.ALL, 5 )
		sbSizer9.Add( optionLayoutSizer, 0, wx.EXPAND, 5 )
		topPanelSizer.Add( sbSizer9, 0, wx.ALL|wx.EXPAND, 5 )
		
		mainSizer.Add( topPanelSizer, 0, wx.ALL|wx.EXPAND, 5 )
		
		#Mid sizer
		midPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Matlab File" ), wx.VERTICAL )
		self.matlabTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
		self.matlabTextCtrl.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )
		self.matlabTextCtrl.SetToolTipString( "Input file for conversion" )
		midPanelSizer.Add( self.matlabTextCtrl, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
		mainSizer.Add( midPanelSizer, 2, wx.EXPAND, 5 )
	
		#Bottom sizer
		bottomPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Converted File" ), wx.VERTICAL )		
		self.convertedTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
		self.convertedTextCtrl.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString ) )
		self.convertedTextCtrl.SetToolTipString( "Output file after conversion" )
		bottomPanelSizer.Add( self.convertedTextCtrl, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
		mainSizer.Add( bottomPanelSizer, 2, wx.EXPAND, 5 )

		#Set frame sizer
		self.SetSizer( mainSizer )
		self.Layout()
		self.Centre( wx.BOTH )
		
		# Bind GUI elements to specific events
		self.Bind( wx.EVT_MENU, self.onOpen, id = self.openFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onSaveAs, id = self.saveFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onExit, id = self.exit.GetId() )
		self.Bind( wx.EVT_MENU, self.onClear, id = self.clear.GetId() )
		self.Bind( wx.EVT_MENU, self.onConvert, id = self.convertFile.GetId() )
		self.Bind( wx.EVT_MENU, self.onCloseAll, id = self.close.GetId() )
		self.Bind( wx.EVT_MENU, self.onHelp, id = self.helpItem.GetId() )
		self.Bind( wx.EVT_MENU, self.onLicense, id = self.license.GetId() )
		self.Bind( wx.EVT_MENU, self.onAbout, id = self.about.GetId() )
		self.Bind( wx.EVT_FILEPICKER_CHANGED, self.onFilePicker, id = self.filePicker.GetId() )
		self.Bind( wx.EVT_BUTTON, self.onConvert, id = self.convertButton.GetId() )
		self.Bind( wx.EVT_CLOSE, self.onClose ) 

		def __del__( self ):
			pass
	    
# -----------------------------------------------------------------------------
# Virtual Event Handlers
# -----------------------------------------------------------------------------		
	def onOpen(self, event):
		global _IS_OUTPUT_SAVED		
		dirname=""
		dlg = wx.FileDialog(self, "Choose a file", dirname, "", "*.m", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetFilename()
			dirname = dlg.GetDirectory()
			path=os.path.join(dirname, filename)
			f = open(path, 'r')
			self.matlabTextCtrl.SetValue(f.read())
			self.filePicker.SetPath(path)
			f.close()
			#Only reset values when file was loaded
			self.convertButton.Enable()
			self.convertFile.Enable(1)
			self.convertedTextCtrl.SetValue("")
		dlg.Destroy()
		_IS_OUTPUT_SAVED = False

	def onFilePicker(self, event):
		self.convertedTextCtrl.SetValue("")
		self.convertButton.Enable()
		self.convertFile.Enable(1)
		path=self.filePicker.GetPath()
		f = open(path, 'r')
		self.matlabTextCtrl.SetValue(f.read())		
		f.close()		

	def onSaveAs( self, event ):
		global _IS_OUTPUT_SAVED
		msg = None
		fileFormat = None
		if _SAVEAS_ODE:
			msg = "Save ODE File"
			fileFormat = "ODE files (*.ODE)|*.ode"			

		elif self.convertedTextCtrl.IsEmpty():
			msg = "Save File As"
			fileFormat = "All files (*.*)|*.*"	
		else:
			msg = "Save SBML File"
			fileFormat = "SBML files (*.xml)|*.xml"                        
		
		dlg = wx.FileDialog(self, msg, "", "", fileFormat, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_CANCEL:
			return
		else:
			output = open(dlg.GetPath(), 'w')
			output.write(self.convertedTextCtrl.GetValue())
			output.close()
			_IS_OUTPUT_SAVED = True
			

	def onExit( self, event ):
		self.Close(True)
	
	def onClear( self, event ):
		global _IS_OUTPUT_SAVED
		self.matlabTextCtrl.SetValue("")
		self.convertedTextCtrl.SetValue("")
		self.filePicker.SetPath("")
		self.statusBar.SetStatusText( "Ready",0 )
		self.statusBar.SetStatusText( "",2 )
		self.convertButton.Disable()
		self.convertFile.Enable(0)
		self.reactionBasedModel.SetValue( True )
		self.varsAsSpecies.SetValue( True )
		_IS_OUTPUT_SAVED = False
		
	
	def onConvert( self, event ):
		global _IS_OUTPUT_SAVED
		global _SAVEAS_ODE
		saveOutput( self, event )

		self.statusBar.SetStatusText( "Generating output ..." ,0)
		try:
			parser = MatlabGrammar()
			parse_results = parser.parse_string(self.matlabTextCtrl.GetValue())
			
			#output XPP files
			if self.xppModel.GetValue():
				output = create_raterule_model(parse_results, self.varsAsSpecies.GetValue(),not self.xppModel.GetValue())
				self.convertedTextCtrl.SetValue(output)
				self.statusBar.SetStatusText("ODE format",2)				
				
				#output equation-based SBML					
			elif self.equationBasedModel.GetValue():
				output = create_raterule_model(parse_results, self.varsAsSpecies.GetValue(), self.equationBasedModel.GetValue())
				self.convertedTextCtrl.SetValue(output)
				self.statusBar.SetStatusText("SBML format - equations",2)
				#output equation-based SBML										
			else:
				if not network_available():
					msg = "A network connection is needed for this feature" 
					dlg = GMD.GenericMessageDialog(self, msg, "Warning!",agwStyle=wx.ICON_EXCLAMATION | wx.OK)               
					dlg.ShowModal()
					dlg.Destroy()
				else:
					#Create temp file storing XPP model version				
					with NamedTemporaryFile(suffix= ".ode", delete=False) as xpp_file:
						xpp_file.write(create_raterule_model(parse_results, self.varsAsSpecies.GetValue() , self.reactionBasedModel.GetValue()))
					files = {'file':open(xpp_file.name)}
					#Access Biocham to curate and convert equations to reactions
					data = {'exportTo':'sbml', 'curate':'true'}
					response = requests.post(_BIOCHAM_URL, files=files, data=data, timeout=1)
					self.convertedTextCtrl.SetValue(response.content)
					del files
					os.unlink(xpp_file.name)
					self.statusBar.SetStatusText("SBML format - reactions",2)
			
		except IOError as err:
			print("IOError: {0}".format(err))
		except Exception as exc:
			print("Exception: {0}".format(exc))
		finally:
			self.statusBar.SetStatusText( "Done!",0 )
			_IS_OUTPUT_SAVED = False
			_SAVEAS_ODE= self.xppModel.GetValue()

	
	def onCloseAll( self, event ):
		self.Close(True)

	def onHelp( self, event ):
		wx.BeginBusyCursor() 
		webbrowser.open(_HELP_URL) 
		wx.EndBusyCursor()
		
	def onLicense( self, event ):
		wx.BeginBusyCursor() 
		webbrowser.open(_LICENSE_URL) 
		wx.EndBusyCursor()
            
	def onAbout( self, event ):
		msg = "MOCCASIN \n\n" + \
		      "A user-assisted converter that can take MATLAB or Octave ODE-based \n" + \
                      "models in biology and translate them into SBML format.\n\n" + \
		      "Please report any bugs or requests of improvements\n" + \
                      "to us at the following address:\n" + \
                      "email@sbml.com\n\n"+ \
		      "Current version:   " + _VERSION + " !!" 
		dlg = GMD.GenericMessageDialog(self, msg, "About MOCCASIN",agwStyle=wx.ICON_INFORMATION | wx.OK)               
		dlg.ShowModal()
		dlg.Destroy()

	def onClose( self, event ):
		saveOutput( self,event )
		self.Destroy()

# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------	
app = wx.App(False)
frame = MainFrame(None)
frame.Show()
app.MainLoop()
