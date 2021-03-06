#!/usr/bin/env python2
#
# @file    Moccasin_GUI.py
# @brief   Graphical User Interface (GUI) for MOCCASIN
# @author  Harold Gomez
# @author  Michael Hucka
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
# ------------------------------------------------------------------------- -->

from   distutils.version import LooseVersion
import os
import re
import requests
import sys
from   sys import platform
import textwrap
import webbrowser

# We need wx.html2, which was introduced in wxPython 2.9.
import wx
if LooseVersion(wx.__version__) < LooseVersion('2.9'):
    raise Exception('The ' + moccasin.__title__
                    + ' GUI requires wxPython version 2.9 or higher')

# Imports for tokenizing, formatting and displaying .m or .xml files
import wx.html2
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import wx.lib.dialogs
import wx.html
from pkg_resources import get_distribution, DistributionNotFound

import wx.adv

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import moccasin
from moccasin.errors import *
from .controller import Controller
from .network_utils import have_network
from .printDialog import PrintDialog
from .moccasin_logo import getMoccasinLogoIcon


# -----------------------------------------------------------------------------
# Global configuration constants.
# -----------------------------------------------------------------------------

_TITLE           = moccasin.__title__
_URL             = moccasin.__url__
_HELP_URL        = moccasin.__help_url__
_LICENSE         = moccasin.__license__
_LICENSE_URL     = moccasin.__license_url__
_VERSION         = moccasin.__version__
_EMPTY_PAGE      ='''<HTML lang=en><HEAD></HEAD>
<BODY><!-- empty page --></BODY> </HTML> ''' # Used as empty value to clear the empty WebView text field


# -----------------------------------------------------------------------------
# Utility functions.
# -----------------------------------------------------------------------------

_WX4 = wx.__version__.startswith('4')

def wxAppendItem(menu, thing):
    if _WX4:
        menu.Append(thing)
    else:
        menu.AppendItem(thing)

def wxAppendMenu(menu, *args):
    if _WX4:
        menu.Append(*args)
    else:
        menu.AppendMenu(*args)

def wxSetToolTip(item, text):
    if _WX4:
        item.SetToolTip(text)
    else:
        item.SetToolTipString(text)


# Uses the pygments package to tokenize and format text for display
def tokenize(input_file, file_format, text_style):
    lexer = get_lexer_by_name(file_format, stripall = True)
    formatter = HtmlFormatter(noclasses = True, nobackground = True, style = text_style)
    return (highlight(input_file, lexer, formatter))


# -----------------------------------------------------------------------------
# Graphical User Interface (GUI) definition.
# -----------------------------------------------------------------------------

class MainFrame (wx.Frame):
    _output_saved = True
    _save_as_ode  = False               # Used to save the right file format

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id = wx.ID_ANY,
                          title = _TITLE,
                          pos = wx.DefaultPosition, size = wx.Size(780,790),
                          style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)

        if _WX4:
            self.SetSizeHints(wx.Size(780,-1))
        else:
            self.SetSizeHintsSz(wx.Size(780,-1))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))

        # Interface with the back-end
        self.controller = Controller()

        # Construct a status bar
        if _WX4:
            self.statusBar = self.CreateStatusBar(
                5, wx.ALWAYS_SHOW_SB|wx.RAISED_BORDER, wx.ID_ANY)
        else:
            self.statusBar = self.CreateStatusBar(
                5, wx.ST_SIZEGRIP|wx.ALWAYS_SHOW_SB|wx.RAISED_BORDER, wx.ID_ANY)
        self.statusBar.SetFieldsCount(5)
        wxSetToolTip(self.statusBar, "Status")
        self.statusBar.SetStatusText("Ready", 0)
        self.statusBar.SetStatusText('Version ' + _VERSION, 4)

        # Construct a menu bar
        self.menuBar = wx.MenuBar(0)

        self.fileMenu = wx.Menu()
        self.openFileOption = wx.MenuItem(self.fileMenu, wx.ID_OPEN,
                                          "Open"+ "\t" + "Ctrl+O",
                                          wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.fileMenu, self.openFileOption)

        self.fileHistory = wx.FileHistory(8)
        self.config = wx.Config(_TITLE + "_local", style = wx.CONFIG_USE_LOCAL_FILE)
        self.fileHistory.Load(self.config)

        recent = wx.Menu()
        self.fileHistory.UseMenu(recent)
        self.fileHistory.AddFilesToMenu()
        wxAppendMenu(self.fileMenu, wx.ID_ANY, "&Recent Files", recent)
        self.fileMenu.AppendSeparator()

        self.saveMenuOption = wx.MenuItem(self.fileMenu, wx.ID_SAVE,
                                          "Save"+ "\t" + "Ctrl+S",
                                          wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.fileMenu, self.saveMenuOption)
        self.fileMenu.AppendSeparator()

        self.pageSetup = wx.MenuItem(self.fileMenu, wx.ID_PAGE_SETUP,
                                     "Page Setup"+ "\t" + "F5",
                                     wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.fileMenu, self.pageSetup)
        self.printOption = wx.MenuItem(self.fileMenu, wx.ID_PRINT,
                                       "Print"+ "\t" + "F8",
                                       wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.fileMenu, self.printOption)
        self.fileMenu.AppendSeparator()
        self.initializePrintingDefaults() # initialize the print data and set some default values

        self.exit = wx.MenuItem(self.fileMenu, wx.ID_EXIT,
                                "Exit"+ "\t" + "Alt+F4",
                                wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.fileMenu, self.exit)

        self.menuBar.Append(self.fileMenu, "File")

        self.editMenu = wx.Menu()
        self.clear = wx.MenuItem(self.editMenu, wx.ID_CLEAR,
                                 "Clear"+ "\t" + "Ctrl+L",
                                 wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.editMenu, self.clear)

        self.menuBar.Append(self.editMenu, "Edit")

        self.runMenu = wx.Menu()
        self.convertFile = wx.MenuItem(self.runMenu, wx.ID_ANY,
                                       "Convert"+ "\t" + "Ctrl+R",
                                       wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.runMenu, self.convertFile)
        self.convertFile.Enable(0)

        self.menuBar.Append(self.runMenu, "Run")

        self.windowMenu = wx.Menu()
        self.close = wx.MenuItem(self.windowMenu, wx.ID_CLOSE,
                                 "CloseAll",
                                 wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.windowMenu, self.close)

        self.menuBar.Append(self.windowMenu, "Window")

        self.helpMenu = wx.Menu()
        self.helpItem = wx.MenuItem(self.helpMenu, wx.ID_HELP,
                                    _TITLE + " Help"+ "\t" + "F1",
                                    wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.helpMenu, self.helpItem)

        self.helpMenu.AppendSeparator()

        self.license = wx.MenuItem(self.helpMenu, wx.ID_ANY,
                                   _LICENSE,
                                   wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.helpMenu, self.license)

        self.about = wx.MenuItem(self.helpMenu, wx.ID_ABOUT,
                                 "About " + _TITLE,
                                 wx.EmptyString, wx.ITEM_NORMAL)
        wxAppendItem(self.helpMenu, self.about)

        self.menuBar.Append(self.helpMenu, "Help")

        self.SetMenuBar(self.menuBar)

        # Add sizers(3) and elements for matlab and translated text
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.SetMinSize(wx.Size(1, 5))
        if _WX4:
            mainSizer.AddSpacer(1)
        else:
            mainSizer.AddSpacer((0, 1), 0, wx.EXPAND|wx.TOP, 5) # Diff
        # Top sizer
        labelFont = wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90,
                            False, wx.EmptyString)
        topPanelSizer = wx.FlexGridSizer(6, 1, 0, 0)

        fileConvSizer1 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "File selection"), wx.HORIZONTAL)
        self.m_staticText6 = wx.StaticText(self, wx.ID_ANY,
                                           "MATLAB file to be converted:",
                                           wx.DefaultPosition, wx.DefaultSize, 10)
        self.m_staticText6.Wrap(-1)
        self.m_staticText6.SetFont(labelFont)
        self.m_staticText6.SetToolTip("The input file to be converted by MOCCASIN.")
        fileConvSizer1.Add(self.m_staticText6, 1, wx.ALL, 6)
        self.filePicker = wx.FilePickerCtrl(self, wx.ID_ANY, path = wx.EmptyString,
                                            message = "Select a file",
                                            wildcard = "*.m",
                                            pos = wx.DefaultPosition,
                                            size = wx.DefaultSize)
        self.filePicker.SetMinSize(wx.Size(350, -1))
        self.filePicker.SetFont(labelFont)
        fileConvSizer1.Add(self.filePicker, 6, wx.ALL, 1)
        topPanelSizer.Add(fileConvSizer1, 1, wx.ALL|wx.EXPAND, 5)

        sbSizer9 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Conversion actions"),
                                     wx.VERTICAL)
        optionLayoutSizer = wx.GridSizer(1, 6, 0, 375 if platform == 'darwin' else 385)

        self.staticTextOpt = wx.StaticText(self, wx.ID_ANY, "Encode variables as: ",
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.staticTextOpt.Wrap(-1)
        self.staticTextOpt.SetFont(labelFont)
        self.staticTextOpt.SetToolTip("The dynamic variables in a model can be encoded either as SBML species or SBML reactions.")
        optionLayoutSizer.Add(self.staticTextOpt, 0, wx.ALL, 6)
        self.varsAsSpecies = wx.RadioButton(self, wx.ID_ANY, "SBML Species",
                                            wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.varsAsSpecies.SetValue(True)
        optionLayoutSizer.Add(self.varsAsSpecies, 0, wx.ALL, 6)
        self.varsAsParams = wx.RadioButton(self, wx.ID_ANY, "SBML Parameters",
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        optionLayoutSizer.Add(self.varsAsParams, 0, wx.ALL, 6)
        sbSizer9.Add(optionLayoutSizer)

        gSizer7 = wx.GridSizer(0, 6, 0, 375 if platform == 'darwin' else 385)
        self.modeType = wx.StaticText(self, wx.ID_ANY, "Produce output format: ",
                                      wx.DefaultPosition, wx.DefaultSize, 0)
        self.modeType.Wrap(-1)
        self.modeType.SetFont(labelFont)
        self.modeType.SetToolTip("The conversion results can be written in SBML or XPP format.")
        gSizer7.Add(self.modeType, 0, wx.ALL, 6)
        self.reactionBasedModel = wx.RadioButton(self, wx.ID_ANY, "SBML (reaction-based)",
                                                 wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.reactionBasedModel.SetValue(True)
        gSizer7.Add(self.reactionBasedModel, 0, wx.ALL, 6)
        self.equationBasedModel = wx.RadioButton(self, wx.ID_ANY, "SBML (equation-based)",
                                                 wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.equationBasedModel, 0, wx.ALL, 6)
        self.xppModel = wx.RadioButton(self, wx.ID_ANY, "XPP/XPPAUT",
                                       wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.xppModel, 0, wx.ALL, 6)
        sbSizer9.Add(gSizer7, 0, wx.EXPAND, 5)

        optionInset = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Conversion options"), wx.VERTICAL)
        optionGrid = wx.GridSizer(1, 2, 10, 10)

        self.assumeTranslatable = wx.CheckBox(self, id = wx.ID_ANY,
                                              label = 'Assume array operations are not used')
        self.assumeTranslatable.SetToolTip("Relax compatibility checks for certain constructs (such as element-wise multiplication) that would otherwise be assumed to mean the variables are matrices.")
        self.assumeTranslatable.SetFont(labelFont)
        optionGrid.Add(self.assumeTranslatable, flag = wx.ALL, border = 6)

        self.addMoccasinComments = wx.CheckBox(self, id = wx.ID_ANY,
                                              label = 'Add converter info as comments in file')
        self.addMoccasinComments.SetToolTip("Relax compatibility checks for certain constructs (such as element-wise multiplication) that would otherwise be assumed to mean the variables are matrices.")
        self.addMoccasinComments.SetFont(labelFont)
        self.addMoccasinComments.Value = True
        self.addMoccasinComments.SetToolTip("Write a comment into the output file with the MOCCASIN version, time stamp, and other information.")
        optionGrid.Add(self.addMoccasinComments, flag = wx.ALL, border = 6)
        optionInset.Add(optionGrid, 0, wx.EXPAND, 0)

        self.convertButton = wx.Button(self, wx.ID_ANY, "Convert",
                                       wx.DefaultPosition, wx.DefaultSize, 0)
        self.convertButton.SetFont(labelFont)
        self.convertButton.Disable()

        buttonHSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonVSizer = wx.BoxSizer(wx.VERTICAL)
        buttonHSizer.Add(self.convertButton, 0, wx.CENTER)
        buttonVSizer.AddSpacer(10)
        buttonVSizer.Add(buttonHSizer, 0, wx.CENTER)

        topPanelSizer.Add(sbSizer9, 2, wx.ALL|wx.EXPAND, 5)
        topPanelSizer.Add(optionInset, 2, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(topPanelSizer, 1, wx.ALL|wx.EXPAND, 0)

        # Mid sizer
        panelTextFont = wx.Font(wx.NORMAL_FONT.GetPointSize() -1, 70, 90,
                                wx.FONTWEIGHT_NORMAL, False, wx.EmptyString)

        midPanelSizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "MATLAB File"),
                                          wx.VERTICAL)
        self.matlabWebView = wx.html2.WebView.New(self, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND )
        self.matlabWebView.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        wxSetToolTip(self.matlabWebView, "Input file for conversion")
        self.matlabWebView.SetFont(panelTextFont)
        self.matlabWebView.SetPage(_EMPTY_PAGE, "")
        midPanelSizer.Add(self.matlabWebView, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(midPanelSizer, 2, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(buttonVSizer, 0, wx.ALL|wx.EXPAND, 0)

        # Bottom sizer
        bottomPanelSizer = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Converted File"), wx.VERTICAL)
        self.convertedWebView = wx.html2.WebView.New(
            self, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND)
        self.convertedWebView.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        self.convertedWebView.SetFont(panelTextFont)
        wxSetToolTip(self.convertedWebView, "Output file after conversion")
        self.convertedWebView.SetPage(_EMPTY_PAGE, "")
        bottomPanelSizer.Add(
            self.convertedWebView, 1, wx.ALIGN_BOTTOM|wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(bottomPanelSizer, 2, wx.ALL|wx.EXPAND, 5)

        # Set frame sizer
        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Bind GUI elements to specific events
        self.Bind(wx.EVT_MENU, self.onOpen, id = self.openFileOption.GetId())
        self.Bind(wx.EVT_MENU, self.onSaveAs, id = self.saveMenuOption.GetId())
        self.Bind(wx.EVT_MENU, self.onExit, id = self.exit.GetId())
        self.Bind(wx.EVT_MENU, self.onClear, id = self.clear.GetId())
        self.Bind(wx.EVT_MENU, self.onConvert, id = self.convertFile.GetId())
        self.Bind(wx.EVT_MENU, self.onCloseAll, id = self.close.GetId())
        self.Bind(wx.EVT_MENU, self.onHelp, id = self.helpItem.GetId())
        self.Bind(wx.EVT_MENU, self.onLicense, id = self.license.GetId())
        self.Bind(wx.EVT_MENU, self.onAbout, id = self.about.GetId())
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.onFilePicker, id = self.filePicker.GetId())
        self.Bind(wx.EVT_BUTTON, self.onConvert, id = self.convertButton.GetId())
        self.Bind(wx.EVT_MENU, self.OnPageSetup, id= self.pageSetup.GetId())
        self.Bind(wx.EVT_MENU, self.OnPrint, id=self.printOption.GetId())
        self.Bind(wx.EVT_MENU_RANGE, self.onFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        self.Bind(wx.EVT_CLOSE, self.onClose)


    def __del__(self):
        pass

    # -------------------------------------------------------------------------
    # Virtual Event Handlers
    # -------------------------------------------------------------------------

    def onOpen(self, event):
        dirname=""
        if self.needSaveOutput(event):
            self.saveFile(event)
            return
        else:
            self._output_saved = True
        dlg = wx.FileDialog(self, "Choose a file", dirname, "", "*.m", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            path=os.path.join(dirname, filename)
            self.resetOnOpen(event)
            self.openFile(event, path)
            self.filePicker.SetPath(path)
            # Only reset values when file was loaded
            self.modifyHistory(event, path)
        dlg.Destroy()


    def onFilePicker(self, event):
        if self.needSaveOutput(event):
            if not self.saveFile(event):
                return
        else:
            self._output_saved = True
        self.resetOnOpen(event)
        path = self.filePicker.GetPath()
        if not os.path.isfile(path):
            return
        self.openFile(event, path)
        self.modifyHistory(event, path)


    def onSaveAs(self, event):
        self.saveFile(event)
        self._output_saved = True


    def onFileHistory(self, event):
        self.resetOnOpen(event)
        fileNum = event.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.modifyHistory (event, path)
        self.filePicker.SetPath(path)
        self.openFile(event, path)


    def onExit(self, event):
        self.Close(True)


    def onClear(self, event):
        self.matlabWebView.SetPage(_EMPTY_PAGE,"")
        self.convertedWebView.SetPage(_EMPTY_PAGE, "")
        self.filePicker.SetPath("")
        self.statusBar.SetStatusText("Ready",0)
        self.statusBar.SetStatusText("",2)
        self.convertButton.Disable()
        self.convertFile.Enable(0)
        self.reactionBasedModel.SetValue(True)
        self.varsAsSpecies.SetValue(True)
        self.assumeTranslatable.SetValue(False)
        self.addMoccasinComments.SetValue(True)
        self._output_saved = True


    def onConvert(self, event):
        if self.needSaveOutput(event):
            if not self.saveFile(event):
                return
        self.convertedWebView.SetPage(_EMPTY_PAGE, "")
        self.statusBar.SetStatusText("Generating output ...", 0)
        wx.BeginBusyCursor()
        try:
            self.controller.parse_contents(self.file_contents)
            self.controller.check_translatable(self.assumeTranslatable.Value)
            # output XPP files
            if self.xppModel.GetValue():
                output = self.controller.build_model(
                    use_species = self.varsAsSpecies.GetValue(),
                    output_format = "xpp",
                    name_after_param = False,
                    add_comments = self.addMoccasinComments.Value)

                self.convertedWebView.SetPage(tokenize(output, "matlab", "borland"), "")
                self.statusBar.SetStatusText("XPP/XPPAUT ODE format", 2)

            # output equation-based SBML
            elif self.equationBasedModel.GetValue():
                output = self.controller.build_model(
                    use_species = self.varsAsSpecies.GetValue(),
                    output_format = "sbml",
                    name_after_param = False,
                    add_comments = self.addMoccasinComments.Value)

                self.convertedWebView.SetPage(tokenize(output, "xml", "borland"), "")
                self.statusBar.SetStatusText("SBML format - equations", 2)
            # Output reaction-based SBML
            else:
                if not have_network():
                    msg = "A network connection is needed for this feature, but the network appears to be unavailable."
                    dlg = wx.MessageDialog(self, msg, "Warning", wx.OK | wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    sbml = self.controller.build_reaction_model(
                        use_species = self.varsAsSpecies.GetValue(),
                        name_after_param = False,
                        add_comments = self.addMoccasinComments.Value)

                    self.convertedWebView.SetPage(tokenize(sbml, "xml", "borland"), "")
                    self.statusBar.SetStatusText("SBML format - reactions",  2)
                    self._output_saved = False

        except IOError as err:
            wx.EndBusyCursor()
            self.report("upon attempting to convert the file", err)
        except Exception as err:
            wx.EndBusyCursor()
            self.report("upon attempting to convert the file", err)
        else:
            wx.EndBusyCursor()
            self.statusBar.SetStatusText("Done", 0)
            self._output_saved = False
            self._save_as_ode = self.xppModel.GetValue()


    def onCloseAll(self, event):
        self.Close(True)


    def onHelp(self, event):
        wx.BeginBusyCursor()
        webbrowser.open(_HELP_URL)
        wx.EndBusyCursor()


    def onLicense(self, event):
        wx.BeginBusyCursor()
        webbrowser.open(_LICENSE_URL)
        wx.EndBusyCursor()


    def onAbout(self, event):
        dlg = wx.adv.AboutDialogInfo()
        dlg.SetIcon(getMoccasinLogoIcon())
        dlg.SetName(_TITLE)
        dlg.SetVersion(_VERSION)
        dlg.SetLicense(_LICENSE)
        dlg.SetDescription('\n'.join(textwrap.wrap(
            _TITLE + " is the Model ODE Converter for Creating Automated "
            "SBML INteroperability.  It is a user-assisted converter "
            "that can take MATLAB or Octave ODE-based models in "
            "biology and translate them into the SBML format.", 81)))
        dlg.SetWebSite(_URL)
        dlg.AddDeveloper(u"Michael Hucka (California Institute of Technology)")
        dlg.AddDeveloper(u"\nSarah Keating (European Bioinformatics Institute)")
        dlg.AddDeveloper(u"\nHarold G\u00f3mez (ETH Zurich)")
        wx.adv.AboutBox(dlg)


    def onClose(self, event):
        if self.needSaveOutput(event):
            if not self.saveFile(event):
                return
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
            self.margins = (data.GetMarginTopLeft(), data.GetMarginBottomRight())
        dlg.Destroy()


    def OnPrint(self, evt):
        data = wx.PrintDialogData(self.pdata)
        printer = wx.Printer(data)
        text = self.convertedWebView.GetPageText()
        printout = PrintDialog(text, _TITLE + " output", self.margins)
        useSetupDialog = True
        if (not printer.Print(self, printout, useSetupDialog)
            and printer.GetLastError() == wx.PRINTER_ERROR):
            wx.MessageBox("There was a problem printing.\n"
                          "Perhaps your current printer is not set correctly?",
                          "Printing Error", wx.OK)
        else:
            data = printer.GetPrintDialogData()
            self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
        printout.Destroy()


    # -----------------------------------------------------------------------------
    # Helper functions
    # -----------------------------------------------------------------------------

    def getPackageVersion(self):
        project = _TITLE
        version = None  # required for initialization of globals
        try:
            version = 'Version ' + __version__
        except DistributionNotFound:
            version = '(local)'
        return version


    # Cleans up the converted text stored in convertedWebView and checks if empty
    def isOutputEmpty(self):
        content = self.convertedWebView.GetPageSource()
        outputText = (re.sub(r"\s+", "", content, flags=re.UNICODE)).encode('utf8')
        initText = re.sub(r"\s+", "", _EMPTY_PAGE)
        if outputText == initText:
            return True
        return False


    def saveFile(self, event):
        '''Saves converted output to file'''
        msg = None
        fileFormat = None

        if self._save_as_ode:
            msg = "Save ODE File"
            fileFormat = "ODE files (*.ODE)|*.ode"
        elif self.isOutputEmpty():
            msg = "Save File As"
            fileFormat = "All files (*.*)|*.*"
        else:
            msg = "Save SBML File"
            fileFormat = "SBML files (*.xml)|*.xml"

        dlg = wx.FileDialog(self, msg, "", "", fileFormat, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return False
        else:
            output = open(dlg.GetPath(), 'w')
            output.write(self.convertedWebView.GetPageText().replace("\n",""))
            output.close()
            self._output_saved = True
            return True


    def needSaveOutput(self, event):
        '''Checks that converted output is saved and asks the user what to do.'''
        if (not self._output_saved and not self.isOutputEmpty()):
            msg = _TITLE + " output may be lost. Do you want to save the current converted output first?"
            dlg = wx.MessageDialog(self, msg, "Warning", wx.YES_NO | wx.ICON_WARNING)
            answer = (dlg.ShowModal() == wx.ID_YES)
            dlg.Destroy()
            return answer
        else:
            return False


    def report(self, context, error):
        '''Serves to give feedback to the user in case of failure'''

        msg = str(error)
        msg = msg[:1].upper() + msg[1:]
        if isinstance(error, MoccasinException):
            if isinstance(error, NotConvertibleError):
                msg += " – MOCCASIN is unable to convert this file."
            elif isinstance(error, IncompleteInputError):
                msg += " – the file is incomplete."
            elif isinstance(error, UnsupportedInputError):
                msg += " – MOCCASIN does not support this kind of input at this time."
            elif isinstance(error, ConversionError):
                msg += " – MOCCASIN cannot handle some constructs in this file – please contact the developers."
            elif isinstance(error, MatlabParsingError):
                msg += " – MOCCASIN is unable to parse this MATLAB file – please contact the developers."

        short = '{}\n\nWould you like to try to continue?\n(Click "no" to quit now)'.format(msg)
        dlg = wx.MessageDialog(self, message = short,
                               caption = "MOCCASIN experienced an error {}".format(context),
                                style = wx.YES_NO | wx.YES_DEFAULT | wx.HELP | wx.ICON_ERROR)
        clicked = dlg.ShowModal()
        if clicked == wx.ID_HELP:
            details = ("MOCCASIN has encountered an error:\n"
                       + "─"*30
                       + "\n{}\n".format(msg)
                       + "─"*30
                       + "\nIf the problem is due to the content of this file "
                       + "(for example, MOCCASIN could not find a call to an "
                       + "odeNN function, or could not parse the file for some "
                       + "reason), then please try again with a different file. "
                       + "\n\nIf you don't know why the error occurred or it is "
                       + "beyond your control, the best action now is to save "
                       + "your work and contact the developers. You can reach the "
                       + "developers via the issue tracker or email:\n"
                       + "    Issue tracker: https://github.com/sbmlteam/moccasin/issues\n"
                       + "    Email: moccasin-dev@googlegroups.com\n"
                       + "        or sbml-team@googlegroups.com")
            dlg = wx.lib.dialogs.ScrolledMessageDialog(self, details, "Error")
            dlg.ShowModal()
            dlg.Destroy()
        elif clicked == wx.ID_NO:
            dlg.Destroy()
            self.onClose("Quitting due to error")
        else:
            dlg.Destroy()


    def modifyHistory(self, event, path):
        '''Saves opened files to the recent list menu'''
        self.fileHistory.AddFileToHistory(path)
        self.fileHistory.Save(self.config)
        self.config.Flush() # Only necessary for Linux systems


    def openFile(self, event, path):
        '''Deals with importing matlab files'''
        try:
            f = open(path, 'r')
            self.file_contents = f.read()
            self.matlabWebView.SetPage(tokenize(self.file_contents, "matlab", "igor"), "")
            f.close()
        except IOError as err:
            self.report("when opening a file", "IOError: {0}".format(err))


    def resetOnOpen(self, event):
        '''Resets graphical components when opening a new file '''
        self.convertButton.Enable()
        self.convertFile.Enable(1)
        self.convertedWebView.SetPage(_EMPTY_PAGE, "")
        self.matlabWebView.SetPage(_EMPTY_PAGE, "")
        self.statusBar.SetStatusText("Ready", 0)
        self._output_saved = True


    def initializePrintingDefaults(self):
        '''Initializes printing parameters for printing'''
        self.pdata = wx.PrintData()
        self.pdata.SetPaperId(wx.PAPER_LETTER)
        self.pdata.SetOrientation(wx.PORTRAIT)
        self.margins = (wx.Point(15,15), wx.Point(15,15))


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def gui_main():
    app = wx.App(False)
    app.SetAppName(_TITLE)
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()
