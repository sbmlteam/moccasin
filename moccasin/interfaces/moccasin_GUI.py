#!/usr/bin/env python
#
# @file    Moccasin_GUI.py
# @brief   Graphical User Interface (GUI) for Moccasin
# @author  Harold Gomez
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
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
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from printDialog import PrintDialog
from controller import Controller
from version import __title__, __version__, __url__, __author__, __help_url__, \
    __license__, __license_url__

# We need wx.html2, which was introduced in wxPython 2.9.
from distutils.version import LooseVersion
if LooseVersion(wx.__version__) < LooseVersion('2.9'):
    raise Exception('The ' + __title__ + ' GUI requires wxPython version 2.9 or higher')

# Imports for tokenizing, formatting and displaying .m or .xml files
import wx.html2
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import wx.lib.dialogs
from pkg_resources import get_distribution, DistributionNotFound


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def getPackageVersion():
        project = __title__
        version = None  # required for initialization of globals
        try:
                version = 'Version ' + __version__
        except DistributionNotFound:
                version = '(local)'
        return version


#Cleans up the converted text stored in convertedWebView and checks if empty
def isOuputEmpty( self ):
        outputText=(re.sub(r"\s+", "", self.convertedWebView.GetPageSource(), flags=re.UNICODE)).encode('utf8')
        initText=(re.sub(r"\s+", "", _EMPTY_PAGE))
        if outputText == initText:
               return True
        return False


def saveFile( self, event):
        '''Saves converted output to file'''
        global _IS_OUTPUT_SAVED
        global _SAVEAS_ODE
        msg = None
        fileFormat = None

        if _SAVEAS_ODE:
                msg = "Save ODE File"
                fileFormat = "ODE files (*.ODE)|*.ode"
        elif isOuputEmpty (self):
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
                output.write(self.convertedWebView.GetPageText().replace("\n",""))
                output.close()
                _IS_OUTPUT_SAVED = True


def checkSaveOutput( self, event ):
        '''Checks that converted output is saved'''
        msg = __title__ + " output may be lost. Do you want to save the file first?"
        dlg = wx.MessageDialog(self, msg, "Warning", wx.YES_NO | wx.ICON_WARNING)

        if ( not _IS_OUTPUT_SAVED and not isOuputEmpty (self)):
                if dlg.ShowModal() == wx.ID_YES:
                        saveFile( self, event )
        dlg.Destroy()


def report( self, event, msg ):
        '''Serves to give feedback to the user in case of failure'''
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, "Error")
        dlg.ShowModal()


def modifyHistory( self, event, path ):
        '''Saves opened files to the recent list menu'''
        self.fileHistory.AddFileToHistory(path)
        self.fileHistory.Save(self.config)
        self.config.Flush() # Only necessary for Linux systems


def openFile( self, event, path):
        '''Deals with importing matlab files'''
        try:
                f = open(path, 'r')
                self.file_contents = f.read()
                self.matlabWebView.SetPage(tokenize(self.file_contents, "matlab", "igor"),"")
                f.close()
        except IOError as err:
                report( self, event, "IOError: {0}".format(err))

#Uses the pygments package to tokenize and format text for display
def tokenize( input_file, file_format, text_style ):
        lexer = get_lexer_by_name(file_format, stripall=True)
        formatter = HtmlFormatter(noclasses=True,nobackground= True,style=text_style)
        return (highlight(input_file,lexer,formatter))


def resetOnOpen( self, event ):
        '''Resets graphical components when opening a new file '''
        self.convertButton.Enable()
        self.convertFile.Enable(1)
        self.convertedWebView.SetPage(_EMPTY_PAGE, "")
        self.matlabWebView.SetPage(_EMPTY_PAGE,"")
        self.statusBar.SetStatusText( "Ready",0 )


def initializePrintingDefaults(self):
        '''Initializes printing parameters for printing'''
        self.pdata = wx.PrintData()
        self.pdata.SetPaperId(wx.PAPER_LETTER)
        self.pdata.SetOrientation(wx.PORTRAIT)
        self.margins = (wx.Point(15,15), wx.Point(15,15))


# -----------------------------------------------------------------------------
# Global configuration constants
# -----------------------------------------------------------------------------

_HELP_URL = __help_url__
_LICENSE_URL = __license_url__
_VERSION = __version__
_IS_OUTPUT_SAVED = False
_SAVEAS_ODE = False #Used to save the right file format
_EMPTY_PAGE='''<HTML lang=en><HEAD></HEAD>
                <BODY><!-- empty page --></BODY> </HTML> ''' #Used as empty value to clear the empty WebView text field


# -----------------------------------------------------------------------------
# Graphical User Interface (GUI) definition
# -----------------------------------------------------------------------------
class MainFrame ( wx.Frame ):
        def __init__( self, parent ):
                wx.Frame.__init__ ( self, parent, id = wx.ID_ANY,
                                    title = "Welcome to " + __title__,
                                    pos = wx.DefaultPosition, size = wx.Size( 780,790 ),
                                    style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
                self.SetSizeHintsSz( wx.Size( 760,-1 ))
                self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )

                #Interface with the back-end
                self.controller = Controller()

                #Construct a status bar
                self.statusBar = self.CreateStatusBar(5, wx.ST_SIZEGRIP|wx.ALWAYS_SHOW_SB|wx.RAISED_BORDER, wx.ID_ANY )
                self.statusBar.SetFieldsCount(5)
                self.statusBar.SetToolTipString( "Status" )
                self.statusBar.SetStatusText("Ready",0)
                self.statusBar.SetStatusText('Version ' + _VERSION ,4)

                #Construct a menu bar
                self.menuBar = wx.MenuBar( 0 )

                self.fileMenu = wx.Menu()
                self.openFile = wx.MenuItem( self.fileMenu, wx.ID_OPEN, "Open"+ "\t" + "Ctrl+O", wx.EmptyString, wx.ITEM_NORMAL )
                self.fileMenu.AppendItem( self.openFile )

                self.fileHistory = wx.FileHistory(8)
                self.config = wx.Config(__title__ + "_local", style=wx.CONFIG_USE_LOCAL_FILE)
                self.fileHistory.Load(self.config)

                recent = wx.Menu()
                self.fileHistory.UseMenu(recent)
                self.fileHistory.AddFilesToMenu()
                self.fileMenu.AppendMenu(wx.ID_ANY, "&Recent Files", recent)
                self.fileMenu.AppendSeparator()

                self.saveFile = wx.MenuItem( self.fileMenu, wx.ID_SAVE, "Save"+ "\t" + "Ctrl+S", wx.EmptyString, wx.ITEM_NORMAL )
                self.fileMenu.AppendItem( self.saveFile )
                self.fileMenu.AppendSeparator()

                self.pageSetup = wx.MenuItem( self.fileMenu, wx.ID_PAGE_SETUP, "Page Setup"+ "\t" + "F5", wx.EmptyString, wx.ITEM_NORMAL )
                self.fileMenu.AppendItem( self.pageSetup )
                self.printOption = wx.MenuItem( self.fileMenu, wx.ID_PRINT, "Print"+ "\t" + "F8", wx.EmptyString, wx.ITEM_NORMAL )
                self.fileMenu.AppendItem( self.printOption )
                self.fileMenu.AppendSeparator()
                initializePrintingDefaults(self)# initialize the print data and set some default values

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
                self.helpItem = wx.MenuItem( self.helpMenu, wx.ID_HELP, __title__ + " Help"+ "\t" + "F1", wx.EmptyString, wx.ITEM_NORMAL )
                self.helpMenu.AppendItem( self.helpItem )

                self.helpMenu.AppendSeparator()

                self.license = wx.MenuItem( self.helpMenu, wx.ID_ANY, "GNU Lesser General Public License", wx.EmptyString, wx.ITEM_NORMAL )
                self.helpMenu.AppendItem( self.license )

                self.about = wx.MenuItem( self.helpMenu, wx.ID_ABOUT, "About " + __title__, wx.EmptyString, wx.ITEM_NORMAL )
                self.helpMenu.AppendItem( self.about )

                self.menuBar.Append( self.helpMenu, "Help" )

                self.SetMenuBar( self.menuBar )

                #Add sizers(3) and elements for matlab and translated text
                mainSizer = wx.BoxSizer( wx.VERTICAL )
                mainSizer.SetMinSize( wx.Size( 1,5 ) )
                mainSizer.AddSpacer( ( 0, 1), 0, wx.EXPAND|wx.TOP, 5 ) #Diff


                #Top sizer
                labelFont = wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString )
                topPanelSizer = wx.GridSizer( 2, 1, 0, 0 )

                fileConvSizer1 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "File selection" ), wx.HORIZONTAL )
                self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, "Choose a file for conversion:", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_staticText6.Wrap( -1 )
                self.m_staticText6.SetFont( labelFont )
                fileConvSizer1.Add( self.m_staticText6, 1, wx.ALL, 10 )
                self.filePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", "*.m", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
                self.filePicker.SetMinSize( wx.Size( 350,-1 ) )
                self.filePicker.SetFont( labelFont )
                fileConvSizer1.Add( self.filePicker, 6, wx.ALL, 7 )
                topPanelSizer.Add( fileConvSizer1, 1, wx.ALL|wx.EXPAND, 1 )

                sbSizer9 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "File conversion" ), wx.VERTICAL )
                optionLayoutSizer = wx.GridSizer( 1, 6, 0, 40 )
                self.staticTextOpt = wx.StaticText( self, wx.ID_ANY, "Variable encoding: ", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.staticTextOpt.Wrap( -1 )
                self.staticTextOpt.SetFont(labelFont)
                optionLayoutSizer.Add( self.staticTextOpt, 0, wx.ALL, 8 )
                self.varsAsSpecies = wx.RadioButton( self, wx.ID_ANY, "SBML Species", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
                self.varsAsSpecies.SetValue( True )
                optionLayoutSizer.Add( self.varsAsSpecies, 0, wx.ALL, 8 )
                self.varsAsParams = wx.RadioButton( self, wx.ID_ANY, "SBML Parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
                optionLayoutSizer.Add( self.varsAsParams, 0, wx.ALL, 8 )
                optionLayoutSizer.AddSpacer( ( 0, 0), 1, wx.ALL|wx.EXPAND, 2 )
                optionLayoutSizer.AddSpacer( ( 0, 0), 1, wx.ALL|wx.EXPAND, 2 )
                self.convertButton = wx.Button( self, wx.ID_ANY, "Convert", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.convertButton.SetFont(labelFont)
                self.convertButton.Disable()
                optionLayoutSizer.Add( self.convertButton, 1, wx.ALIGN_LEFT|wx.ALIGN_RIGHT|wx.ALL, 5 )
                sbSizer9.Add( optionLayoutSizer, 0, wx.EXPAND, 5 )
                gSizer7 = wx.GridSizer( 0, 6, 0, 40 )

                self.modeType = wx.StaticText( self, wx.ID_ANY, "Output format: ", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.modeType.Wrap( -1 )
                self.modeType.SetFont(labelFont)
                gSizer7.Add( self.modeType, 0, wx.ALL, 8 )
                self.reactionBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML (reactions)", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
                self.reactionBasedModel.SetValue( True )
                gSizer7.Add( self.reactionBasedModel, 0, wx.ALL, 8 )
                self.equationBasedModel = wx.RadioButton( self, wx.ID_ANY, "SBML (equations)", wx.DefaultPosition, wx.DefaultSize, 0 )
                gSizer7.Add( self.equationBasedModel, 0, wx.ALL, 8 )
                self.xppModel = wx.RadioButton( self, wx.ID_ANY, "XPP/XPPAUT", wx.DefaultPosition, wx.DefaultSize, 0 )
                gSizer7.Add( self.xppModel, 0, wx.ALL, 8 )
                sbSizer9.Add( gSizer7, 0, wx.EXPAND, 5 )
                topPanelSizer.Add( sbSizer9, 2, wx.ALL|wx.EXPAND, 1 )

                mainSizer.Add( topPanelSizer, 1, wx.ALL|wx.EXPAND, 5 )


                #Mid sizer
                panelTextFont = wx.Font( wx.NORMAL_FONT.GetPointSize() -1, 70, 90, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString )

                midPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "MATLAB File" ), wx.VERTICAL )
                self.matlabWebView = wx.html2.WebView.New( self, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND  )
                self.matlabWebView.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )
                self.matlabWebView.SetToolTipString( "Input file for conversion" )
                self.matlabWebView.SetFont( panelTextFont )
                self.matlabWebView.SetPage(_EMPTY_PAGE, "")
                midPanelSizer.Add( self.matlabWebView, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
                mainSizer.Add( midPanelSizer, 2, wx.ALL|wx.EXPAND, 5 )

                #Bottom sizer
                bottomPanelSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Converted File" ), wx.VERTICAL )
                self.convertedWebView = wx.html2.WebView.New( self, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND )
                self.convertedWebView.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )
                self.convertedWebView.SetFont( panelTextFont )
                self.convertedWebView.SetToolTipString( "Output file after conversion" )
                self.convertedWebView.SetPage(_EMPTY_PAGE, "")
                bottomPanelSizer.Add( self.convertedWebView, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5 )
                mainSizer.Add( bottomPanelSizer, 2, wx.ALL|wx.EXPAND, 5 )

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
                self.Bind( wx.EVT_MENU, self.OnPageSetup, id= self.pageSetup.GetId() )
                self.Bind( wx.EVT_MENU, self.OnPrint, id=self.printOption.GetId())
                self.Bind( wx.EVT_MENU_RANGE, self.onFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
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
                        resetOnOpen(self, event)
                        openFile(self, event, path)
                        self.filePicker.SetPath(path)
                        #Only reset values when file was loaded
                        modifyHistory(self, event , path)
                        _IS_OUTPUT_SAVED = False
                dlg.Destroy()


        def onFilePicker(self, event):
                resetOnOpen(self, event)
                path=self.filePicker.GetPath()
                openFile(self, event, path)
                modifyHistory(self, event, path)
                _IS_OUTPUT_SAVED = False


        def onSaveAs( self, event ):
                saveFile(self, event)


        def onFileHistory(self, event):
                resetOnOpen(self, event)
                fileNum = event.GetId() - wx.ID_FILE1
                path = self.fileHistory.GetHistoryFile(fileNum)
                modifyHistory (self, event, path)
                self.filePicker.SetPath(path)
                openFile(self, event, path)


        def onExit( self, event ):
                self.Close(True)


        def onClear( self, event ):
                global _IS_OUTPUT_SAVED
                self.matlabWebView.SetPage(_EMPTY_PAGE,"")
                self.convertedWebView.SetPage(_EMPTY_PAGE, "")
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
                self.convertedWebView.SetPage(_EMPTY_PAGE, "")

                self.statusBar.SetStatusText( "Generating output ..." ,0)
                wx.BeginBusyCursor()
                try:
                        self.controller.parse_File(self.file_contents)
                        #output XPP files
                        if self.xppModel.GetValue():
                                [output, extra] = self.controller.build_model(use_species=self.varsAsSpecies.GetValue(),
                                                                              output_format="xpp",
                                                                              name_after_param=False,
                                                                              add_comments=False)

                                self.convertedWebView.SetPage(tokenize(output, "matlab", "borland"),"")
                                self.statusBar.SetStatusText("XPP/XPPAUT ODE format",2)

                        #output equation-based SBML
                        elif self.equationBasedModel.GetValue():
                                 [output, extra] = self.controller.build_model(use_species=self.varsAsSpecies.GetValue(),
                                                                               output_format="sbml",
                                                                               name_after_param=False,
                                                                               add_comments=False)

                                 self.convertedWebView.SetPage(tokenize(output, "xml", "borland"),"")
                                 self.statusBar.SetStatusText("SBML format - equations",2)
                        #output reaction-based SBML
                        else:
                                if not self.controller.check_network_connection():
                                        msg = "A network connection is needed for this feature, but the network appears to be unavailable."
                                        dlg = wx.MessageDialog(self, msg, "Warning", wx.OK | wx.ICON_WARNING)
                                        dlg.ShowModal()
                                        dlg.Destroy()
                                else:
                                        sbml = self.controller.build_reaction_model(use_species=self.varsAsSpecies.GetValue(),
                                                                               name_after_param=False,
                                                                               add_comments=False)

                                        self.convertedWebView.SetPage(tokenize(sbml, "xml", "borland"),"")
                                        self.statusBar.SetStatusText("SBML format - reactions", 2)

                except IOError as err:
                        wx.EndBusyCursor()
                        report(self, event, "IOError: {0}".format(err))
                except Exception as exc:
                        wx.EndBusyCursor()
                        report(self, event, "Exception: {0}".format(exc))
                else:
                        wx.EndBusyCursor()
                        self.statusBar.SetStatusText("Done", 0)
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
                dlg = wx.AboutDialogInfo()
                dlg.SetName(__title__)
                dlg.SetVersion(__version__)
                dlg.SetLicense(__license__)
                dlg.SetDescription('\n'.join(textwrap.wrap(
                        __title__ + " is the Model ODE Converter for Creating Automated "
                        "SBML INteroperability.  It is a user-assisted converter "
                        "that can take MATLAB or Octave ODE-based models in "
                        "biology and translate them into the SBML format.", 81)))
                dlg.SetWebSite(__url__)
                dlg.SetDevelopers([
                        "Michael Hucka (California Institute of Technology)",
                        "Sarah Keating (European Bioinformatics Institute)",
                        "Harold Gomez (Boston University)"
                ])

                wx.AboutBox(dlg)


        def onClose( self, event ):
                checkSaveOutput( self,event )
                self.Destroy()


        # Printing Handlers
        def OnPageSetup(self, evt):
                data = wx.PageSetupDialogData()
                data.SetPrintData(self.pdata)
                data.SetDefaultMinMargins(True)
                data.SetMarginTopLeft(self.margins[0])
                data.SetMarginBottomRight(self.margins[1])
                dlg = wx.PageSetupDialog(self, data)

                if dlg.ShowModal() == wx.ID_OK:
                        data = dlg.GetPageSetupData()
                        self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
                        self.pdata.SetPaperId(data.GetPaperId())
                        self.margins = (data.GetMarginTopLeft(),
                                        data.GetMarginBottomRight())
                dlg.Destroy()


        def OnPrint(self, evt):
                data = wx.PrintDialogData(self.pdata)
                printer = wx.Printer(data)
                text = self.convertedWebView.GetPageText()
                printout = PrintDialog(text, __title__ + " output", self.margins)
                useSetupDialog = True
                if not printer.Print(self, printout, useSetupDialog) \
                   and printer.GetLastError() == wx.PRINTER_ERROR:
                        wx.MessageBox(
                                "There was a problem printing.\n"
                                "Perhaps your current printer is not set correctly?",
                                "Printing Error", wx.OK)
                else:
                        data = printer.GetPrintDialogData()
                        self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
                printout.Destroy()


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def gui_main():
        app = wx.App(False)
        frame = MainFrame(None)
        frame.Show()
        app.MainLoop()

gui_main()
