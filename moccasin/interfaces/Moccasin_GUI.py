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
import textwrap
import sys
import wx
import wx.xrc
import wx.lib.dialogs
import wx.lib.agw.genericmessagedialog as GMD

from pkg_resources import get_distribution, DistributionNotFound

#Some of these imports will disappear when logic is made into a separate module
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile

sys.path.append('moccasin')
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

#Used for saving an file
def saveFile( self, event):
        global _IS_OUTPUT_SAVED
        global _SAVEAS_ODE
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


#Checks that output is saved before it's lost
def checkSaveOutput( self, event ):
        msg = "MOCCASIN output may be lost. Do you want to save the file first?"
        dlg = wx.MessageDialog(self, msg, "Warning", wx.YES_NO | wx.ICON_WARNING)

        if ( not _IS_OUTPUT_SAVED and not self.convertedTextCtrl.IsEmpty()):
                if dlg.ShowModal() == wx.ID_YES:
                        saveFile( self, event )
        dlg.Destroy()


#Serves to give feedback to the user in case of failure
def report( self, event, msg ):
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, "Houston, we have a problem!")
        dlg.ShowModal()

#Saves opened files to the recent list menu
def modifyHistory( self, event, path ):
        self.fileHistory.AddFileToHistory(path)
        self.fileHistory.Save(self.config)
        self.config.Flush() # Only necessary for Linux systems
        

#Deals with importing matlab files
def openFile( self, event, path):
        try:
                f = open(path, 'r')
                self.file_contents = f.read()
                self.matlabTextCtrl.SetValue(self.file_contents)
                f.close()
        except IOError as err:
                report( self, event, "IOError: {0}".format(err))

#Resets components when opening a new file     
def resetOnOpen( self, event ):
        self.convertButton.Enable()
        self.convertFile.Enable(1)
        self.convertedTextCtrl.SetValue("")

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
                wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = "Welcome to MOCCASIN", pos = wx.DefaultPosition, size = wx.Size( 718,691 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
                self.SetSizeHintsSz( wx.Size( 718,-1 ), wx.Size( 718,-1 ) )
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

                self.fileHistory = wx.FileHistory(8)
                self.config = wx.Config("Moccasin_local", style=wx.CONFIG_USE_LOCAL_FILE)
                self.fileHistory.Load(self.config)

                recent = wx.Menu()
                self.fileHistory.UseMenu(recent)
                self.fileHistory.AddFilesToMenu()
                self.fileMenu.AppendMenu(wx.ID_ANY, "&Recent Files", recent)
                self.fileMenu.AppendSeparator()

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
                mainSizer.SetMinSize( wx.Size( 1,5 ) ) 
                mainSizer.AddSpacer( ( 0, 1), 0, wx.EXPAND|wx.TOP, 5 )

                #Top sizer
####
                labelFont = wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString )

                # topPanelSizer = wx.GridSizer( 2, 1, 0, 0 )

                fileConvSizer1 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "File selection" ), wx.VERTICAL )

                gbSizer1 = wx.GridBagSizer( 0, 0 )
                gbSizer1.SetFlexibleDirection( wx.HORIZONTAL )
                gbSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_ALL )

                self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, "Choose a file for conversion:", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_staticText6.Wrap( -1 )
                self.m_staticText6.SetFont( labelFont )
                gbSizer1.Add( self.m_staticText6, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0 )

                self.filePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", "*.m", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
                self.filePicker.SetMinSize( wx.Size( 495, -1 ) )
                gbSizer1.Add( self.filePicker, wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.ALL|wx.EXPAND|wx.ALIGN_RIGHT, 0 )

                fileConvSizer1.Add( gbSizer1, 0, wx.ALL|wx.EXPAND, 0 )

                # topPanelSizer.Add( fileConvSizer1, 0, wx.ALL|wx.EXPAND, 0 )
                mainSizer.Add( fileConvSizer1, 0, wx.ALL|wx.EXPAND, 0 )

                sbSizer9 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "File conversion" ), wx.VERTICAL )

                optionLayoutSizer = wx.GridSizer( 1, 5, 0, 0 )

                self.staticTextOpt = wx.StaticText( self, wx.ID_ANY, "Variable encoding:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT )
                self.staticTextOpt.Wrap( -1 )
                self.staticTextOpt.SetFont( labelFont )

                optionLayoutSizer.Add( self.staticTextOpt, 0, wx.ALL, 5 )

                self.varsAsSpecies = wx.RadioButton( self, wx.ID_ANY, "SBML Species", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
                self.varsAsSpecies.SetValue( True ) 
                optionLayoutSizer.Add( self.varsAsSpecies, 0, wx.ALL, 5 )

                self.varsAsParams = wx.RadioButton( self, wx.ID_ANY, "SBML Parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
                optionLayoutSizer.Add( self.varsAsParams, 0, wx.ALL, 5 )

                optionLayoutSizer.AddSpacer( ( 0, 0), 1, wx.ALL|wx.EXPAND, 2 )

                self.convertButton = wx.Button( self, wx.ID_ANY, "Convert", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.convertButton.Disable()

                optionLayoutSizer.Add( self.convertButton, 1, wx.ALIGN_LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 6 )

                sbSizer9.Add( optionLayoutSizer, 0, wx.EXPAND, 5 )

                gSizer7 = wx.GridSizer( 0, 5, 0, 0 )

                self.modeType = wx.StaticText( self, wx.ID_ANY, "Output format:", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.modeType.Wrap( -1 )
                self.modeType.SetFont( labelFont )

                gSizer7.Add( self.modeType, 0, wx.ALL, 5 )

                self.reactionBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML (reactions)", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
                self.reactionBasedModel.SetValue( True ) 
                gSizer7.Add( self.reactionBasedModel, 0, wx.ALL, 5 )

                self.equationBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML (equations)", wx.DefaultPosition, wx.DefaultSize, 0 )
                gSizer7.Add( self.equationBasedModel, 0, wx.ALL, 5 )

                self.xppModel = wx.RadioButton( self, wx.ID_ANY, "XPP/XPPAUT", wx.DefaultPosition, wx.DefaultSize, 0 )
                gSizer7.Add( self.xppModel, 0, wx.ALL, 5 )


                sbSizer9.Add( gSizer7, 0, wx.EXPAND, 5 )


                # topPanelSizer.Add( sbSizer9, 2, wx.ALL|wx.EXPAND, 1 )
                mainSizer.Add( sbSizer9, 2, wx.ALL|wx.EXPAND, 1 )

                # mainSizer.Add( topPanelSizer, 0, wx.ALL|wx.EXPAND, 5 )
                #################


                #Mid sizer
                panelTextFont = wx.Font( wx.NORMAL_FONT.GetPointSize() -1, 70, 90, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString )

                midPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "MATLAB File" ), wx.VERTICAL )
                self.matlabTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
                self.matlabTextCtrl.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )
                self.matlabTextCtrl.SetToolTipString( "Input file for conversion" )
                self.matlabTextCtrl.SetFont( panelTextFont )
                midPanelSizer.Add( self.matlabTextCtrl, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
                mainSizer.Add( midPanelSizer, 2, wx.EXPAND, 5 )

                #Bottom sizer
                bottomPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Converted File" ), wx.VERTICAL )
                self.convertedTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,200 ), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.ALWAYS_SHOW_SB|wx.FULL_REPAINT_ON_RESIZE|wx.RAISED_BORDER )
                self.convertedTextCtrl.SetFont( panelTextFont )
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
                self.Bind(wx.EVT_MENU_RANGE, self.onFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
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
                        openFile(self, event, path)
                        self.filePicker.SetPath(path)
                        #Only reset values when file was loaded
                        resetOnOpen(self, event)
                        modifyHistory(self, event , path)
                dlg.Destroy()
                _IS_OUTPUT_SAVED = False

        def onFilePicker(self, event):
                resetOnOpen(self, event)               
                path=self.filePicker.GetPath()
                openFile(self, event, path)
                modifyHistory(self, event, path)

        def onSaveAs( self, event ):
                saveFile(self, event)
                
        def onFileHistory(self, event):
                fileNum = event.GetId() - wx.ID_FILE1
                path = self.fileHistory.GetHistoryFile(fileNum)
                self.fileHistory.AddFileToHistory(path)
                self.filePicker.SetPath(path)
                openFile(self, event, path)
                resetOnOpen(self, event)

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

                checkSaveOutput( self, event )

                self.statusBar.SetStatusText( "Generating output ..." ,0)
                try:

                        parser = MatlabGrammar()
                        parse_results = parser.parse_string(self.file_contents)
                        #output XPP files
                        if self.xppModel.GetValue():
                                [output, extra] = create_raterule_model(parse_results,
                                                                        use_species=self.varsAsSpecies.GetValue(),
                                                                        produce_sbml=False)
                                self.convertedTextCtrl.SetValue(output)
                                self.statusBar.SetStatusText("XPP/XPPAUT ODE format",2)

                        #output equation-based SBML
                        elif self.equationBasedModel.GetValue():
                                [output, extra] = create_raterule_model(parse_results,
                                                                        use_species=self.varsAsSpecies.GetValue(),
                                                                        produce_sbml=True)
                                self.convertedTextCtrl.SetValue(output)
                                self.statusBar.SetStatusText("SBML format - equations",2)
                        #output reaction-based SBML
                        else:
                                if not network_available():
                                        msg = "A network connection is needed for this feature, but the network appears to be unavailable." 
                                        dlg = wx.MessageDialog(self, msg, "Warning", wx.OK | wx.ICON_WARNING)
                                        dlg.ShowModal()
                                        dlg.Destroy()
                                else:
                                        #Create temp file storing XPP model version
                                        with NamedTemporaryFile(suffix= ".ode", delete=False) as xpp_file:
                                                [output, extra] = create_raterule_model(parse_results,
                                                                                        use_species=self.varsAsSpecies.GetValue(),
                                                                                        produce_sbml=False,
                                                                                        add_comments=False)
                                                xpp_file.write(output)
                                        files = {'file': open(xpp_file.name)}
                                        #Access Biocham to curate and convert equations to reactions
                                        data = {'exportTo':'sbml', 'curate':'true'}
                                        response = requests.post(_BIOCHAM_URL, files=files, data=data)
                                        # We need to post-process the output to deal with
                                        # limitations in BIOCHAM's translation service.
                                        sbml = process_biocham_output(response.content, parse_results, extra)
                                        self.convertedTextCtrl.SetValue(sbml)
                                        del files
                                        os.unlink(xpp_file.name)
                                        self.statusBar.SetStatusText("SBML format - reactions", 2)

                except IOError as err:
                        report( self, event, "IOError: {0}".format(err))
                except Exception as exc:
                        report( self, event, "Exception: {0}".format(exc))
                else:
                        self.statusBar.SetStatusText( "Done!",0 )
                        _IS_OUTPUT_SAVED = False
                        _SAVEAS_ODE = self.xppModel.GetValue()


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
                # msg = "MOCCASIN \n\n" + \
                #       "A user-assisted converter that can take MATLAB or Octave ODE-based \n" + \
                #       "models in biology and translate them into SBML format.\n\n" + \
                #       "Please report any bugs or requests of improvements\n" + \
                #       "to us at the following address:\n" + \
                #       "email@sbml.com\n\n"+ \
                #       "Current version:   " + _VERSION + " !!" 

                dlg = wx.AboutDialogInfo()
                dlg.SetName("MOCCASIN")
                dlg.SetVersion("1.0.0")
                dlg.SetLicense("GNU Lesser GPL version 2.1")
                dlg.SetDescription('\n'.join(textwrap.wrap(
                        "MOCCASIN is the Model ODE Converter for Creating Awesome "
                        "SBML INteroperability.  It is a user-assisted converter "
                        "that can take MATLAB or Octave ODE-based models in "
                        "biology and translate them into the SBML format.", 81)))
                dlg.SetWebSite("http://github.com/sbmlteam/moccasin")
                dlg.SetDevelopers([
                        "Michael Hucka (California Institute of Technology)",
                        "Sarah Keating (European Bioinformatics Institute)",
                        "Harold Gomez (Boston University)"
                ])

                wx.AboutBox(dlg)

        def onClose( self, event ):
                checkSaveOutput( self,event )
                self.Destroy()

# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------
app = wx.App(False)
frame = MainFrame(None)
frame.Show()
app.MainLoop()
