#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

version = "0.1"
authors = ("Peter Stroia-Williams", '')
copyright = "© 2010"
comments = "A somewhat messily coded but functional match viewer."

import matchviewcanvas

import pygtk
pygtk.require("2.0")
import gtk
import os
import sys


class MatchViewerApp(object):

    matchListFN = None

    def on_window_destroy(self, widget) :
        gtk.main_quit()
        return True

    def saveProject(self) :
        projFile = open(self.projFN, "w")
        projDir = os.path.dirname(self.projFN)
        projFile.write(os.path.relpath(self.im1widgetHandler.imageFilename,projDir) + '\n')
        projFile.write(os.path.relpath(self.im2widgetHandler.imageFilename,projDir) + '\n')
        projFile.write(os.path.relpath(self.matchListFN,projDir) + '\n')
        if self.rowColRadioButton.get_active() :
            projFile.write("row col format\n")
        else :
            projFile.write("xy format\n")
        projFile.close()

    def openProject(self) :
        projFile = open(self.projFN, "r")
        projDir = os.path.dirname(self.projFN)

        line1 = projFile.readline()
        line2 = projFile.readline()
        line3 = projFile.readline()
        line4 = projFile.readline()

        projFile.close()

        self.im1widgetHandler.set_image_file(os.path.normpath(projDir + '/' + line1.strip()))
        self.im2widgetHandler.set_image_file(os.path.normpath(projDir + '/' + line2.strip()))

        matchListFN = os.path.normpath(projDir + '/' + line3.strip())

        if line4 == "row col format\n" :
            self.rowColRadioButton.set_active(True)
            self.xyRadioButton.set_active(False)
        else :
            self.rowColRadioButton.set_active(False)
            self.xyRadioButton.set_active(True)

        self.loadMatchList(matchListFN)

        self.builder.get_object("im1chooserbutton").set_filename(self.im1widgetHandler.imageFilename)
        self.builder.get_object("im2chooserbutton").set_filename(self.im2widgetHandler.imageFilename)
        self.builder.get_object("matchlistchooserbutton4").set_filename(matchListFN)

    def on_swapImages_menuitem_activate(self, widget) :
        tempImFN = self.im1widgetHandler.imageFilename
        self.im1widgetHandler.set_image_file(self.im2widgetHandler.imageFilename)
        self.im2widgetHandler.imageFilename = tempImFN

        self.builder.get_object("im1chooserbutton").set_filename(self.im1widgetHandler.imageFilename)
        self.builder.get_object("im2chooserbutton").set_filename(self.im2widgetHandler.imageFilename)

        self.redrawManager.force_redraw_all()


    def on_new_menuitem_activate(self, widget) :
        self.openWindow.show()

    def on_open_menuitem_activate(self, widget) :
        dialog = gtk.FileChooserDialog("Open Project", None, gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.projFN = dialog.get_filename()
            print dialog.get_filename(), 'selected'
            self.openProject()

        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no files selected'
        dialog.hide()

    def on_saveAsMenuItem_activate(self, widget) :
        dialog = gtk.FileChooserDialog("Save Project As", None, gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.projFN = dialog.get_filename()

            self.saveProject()
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no files selected'
        dialog.hide()

    def on_saveMenuItem_activate(self, widget) :
        if self.projFN == None :
            self.on_saveAsMenuItem_activate(widget)
        else :
            self.saveProject()


    def on_openWindow_delete_event(self, widget, event = None) :
        self.openWindow.hide()
        return True
    def on_saveAsDialog_delete_event(self, widget, event = None) :
        self.saveAsDialog.hide()
        return True

    def loadMatchList(self, filename) :
        self.matchListFN = filename
        self.pointList1 = []
        matchListFile = open(self.matchListFN)
        matchList = []
        for line in matchListFile :
            matchList.append(line)
        
        pointList1, pointList2 = matchviewcanvas.loadMatchList(filename)
       
        self.im1widgetHandler.set_point_list(pointList1)
        self.im2widgetHandler.set_point_list(pointList2)

        self.redrawManager.force_redraw_all()

    def on_matchlistchooserbutton4_file_set(self, widget) :
        self.loadMatchList(widget.get_filename())

    def on_rowCol_radiobutton_toggled(self, widget, data=None) :
        if(self.matchListFN):
            self.loadMatchList(self.matchListFN)



    def on_numbermatchesmenuitem_toggled(self, widget) :
        self.im1widgetHandler.showNumbers = self.im2widgetHandler.showNumbers = widget.get_active()
        self.redrawManager.force_redraw_all()

    def on_aboutMenuItem_activate(self, widget) :
        dialog = gtk.AboutDialog()
        dialog.set_name("MatchViewer")
        dialog.set_version(version)
        dialog.set_authors(authors)
        dialog.set_copyright(copyright)
        dialog.set_comments(comments)

        dialog.run()
        dialog.destroy()

    def getGladeFilename(self):
        dir = os.path.dirname(__file__)
        print dir
        return os.path.join(dir, "MatchViewer.glade")

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.getGladeFilename())

        drawArea1 = self.builder.get_object("im1DrawingArea")
        drawArea2 = self.builder.get_object("im2DrawingArea")

        self.redrawManager = matchviewcanvas.RedrawManager([drawArea1, drawArea2])

        self.im1widgetHandler = matchviewcanvas.CairoImageWidgetEventHandler(drawArea1, self.redrawManager)
        self.im2widgetHandler = matchviewcanvas.CairoImageWidgetEventHandler(drawArea2, self.redrawManager)

        self.builder.connect_signals({ "on_window_destroy"              : self.on_window_destroy,
                                       "on_new_menuItem_activate" : self.on_new_menuitem_activate,
                                       "on_openWindow_delete_event" : self.on_openWindow_delete_event,
                                       "on_openWindowCloseButton_clicked" : self.on_openWindow_delete_event,
                                       "on_im1chooserbutton_file_set" : self.im1widgetHandler.on_file_set,
                                       "on_im2chooserbutton_file_set" : self.im2widgetHandler.on_file_set,
                                       "on_matchlistchooserbutton4_file_set" : self.on_matchlistchooserbutton4_file_set,
                                       "on_numbermatchesmenuitem_toggled" : self.on_numbermatchesmenuitem_toggled,
                                       "on_saveAsMenuItem_activate"       : self.on_saveAsMenuItem_activate,
                                       "on_saveAsDialog_delete_event" : self.on_saveAsDialog_delete_event,
                                       "on_saveMenuItem_activate" : self.on_saveMenuItem_activate,
                                       "on_open_menuitem_activate" : self.on_open_menuitem_activate,
                                       "on_aboutMenuItem_activate" : self.on_aboutMenuItem_activate,
                                       "on_rowCol_radiobutton_toggled" : self.on_rowCol_radiobutton_toggled,
                                       "on_swapImages_menuitem_activate" : self.on_swapImages_menuitem_activate
                                      })
        self.window = self.builder.get_object("window")
        self.window.show()

        self.openWindow = self.builder.get_object("openWindow")

        self.rowColRadioButton = self.builder.get_object("rowCol_radiobutton")
        self.xyRadioButton = self.builder.get_object("xy_radiobutton")

        self.rowColRadioButton.set_active(True)
        self.xyRadioButton.set_active(False)

        self.projFN = None

        if len(sys.argv) == 2 :
            self.projFN = sys.argv[1]
            if not os.path.isabs(self.projFN) :
                self.projFN = os.path.abspath(self.projFN)
            self.openProject()


if __name__ == "__main__":
#  pos = 10, 20
#  elipParams = 1, 20, 16
#  eliplse = Elipse(pos,elipParams)
    app = MatchViewerApp()
    gtk.main()