#!/usr/bin/env python
#
# @file    Moccasin_GUI.py
# @brief   Custom class for printing on Moccasin(GUI)  
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
import sys
import wx
# -----------------------------------------------------------------------------
# Global configuration constants
# -----------------------------------------------------------------------------
_FONTSIZE = 10

# -----------------------------------------------------------------------------
# Printout class definition
# -----------------------------------------------------------------------------

#A printout class that is able to print simple text documents.
#Does not handle page numbers or titles, and it assumes that no
#lines are longer than what will fit within the page width

class PrintDialog(wx.Printout):
      
    def __init__(self, text, title, margins):
        wx.Printout.__init__(self, title)
        self.lines = text.split('\n')
        self.margins = margins


    def HasPage(self, page):
        return page <= self.numPages


    def GetPageInfo(self):
        return (1, self.numPages, 1, self.numPages)


    def CalculateScale(self, dc):
        # Scale the DC such that the printout is roughly the same as
        # the screen scaling.
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        ppiScreenX, ppiScreenY = self.GetPPIScreen()
        logScale = float(ppiPrinterX)/float(ppiScreenX)

        # Now adjust if the real page size is reduced (such as when
        # drawing on a scaled wx.MemoryDC in the Print Preview.)  If
        # page width == DC width then nothing changes, otherwise we
        # scale down for the DC.
        pw, ph = self.GetPageSizePixels()
        dw, dh = dc.GetSize()
        scale = logScale * float(dw)/float(pw)

        # Set the DC's scale.
        dc.SetUserScale(scale, scale)

        # Find the logical units per millimeter (for calculating the
        # margins)
        self.logUnitsMM = float(ppiPrinterX)/(logScale*25.4)


    def CalculateLayout(self, dc):
        # Determine the position of the margins and the
        # page/line height
        topLeft, bottomRight = self.margins
        dw, dh = dc.GetSize()
        self.x1 = topLeft.x * self.logUnitsMM
        self.y1 = topLeft.y * self.logUnitsMM
        self.x2 = dc.DeviceToLogicalXRel(dw) - bottomRight.x * self.logUnitsMM 
        self.y2 = dc.DeviceToLogicalYRel(dh) - bottomRight.y * self.logUnitsMM 

        # use a 1mm buffer around the inside of the box, and a few
        # pixels between each line
        self.pageHeight = self.y2 - self.y1 - 2*self.logUnitsMM
        font = wx.Font(_FONTSIZE, wx.TELETYPE, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)
        self.lineHeight = dc.GetCharHeight() 
        self.linesPerPage = int(self.pageHeight/self.lineHeight)


    def OnPreparePrinting(self):
        # calculate the number of pages
        dc = self.GetDC()
        self.CalculateScale(dc)
        self.CalculateLayout(dc)
        self.numPages = len(self.lines) / self.linesPerPage
        if len(self.lines) % self.linesPerPage != 0:
            self.numPages += 1


    def OnPrintPage(self, page):
        dc = self.GetDC()
        self.CalculateScale(dc)
        self.CalculateLayout(dc)

        # draw a page outline at the margin points
        dc.SetPen(wx.Pen("black", 0))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        r = wx.RectPP((self.x1, self.y1),
                      (self.x2, self.y2))
        dc.DrawRectangleRect(r)
        dc.SetClippingRect(r)

        # Draw the text lines for this page
        line = (page-1) * self.linesPerPage
        x = self.x1 + self.logUnitsMM
        y = self.y1 + self.logUnitsMM
        while line < (page * self.linesPerPage):
            dc.DrawText(self.lines[line], x, y)
            y += self.lineHeight
            line += 1
            if line >= len(self.lines):
                break
        return True

