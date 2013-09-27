#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

version = "0.1"
authors = ("Peter Stroia-Williams", '')
copyright = "© 2010"
comments = "A somewhat messily coded but functional match viewer."

import pygtk
pygtk.require("2.0")
import gtk
import cairo
import pangocairo
import math
import os
import sys

def force_redraw(widget):
    x, y, w, h = widget.allocation
    widget.window.invalidate_rect((0,0,w,h),False)
    return True

class RedrawManager(object):
    widgetList = []
    def __init__(self, widgetList):
        self.widgetList.extend(widgetList)

    def force_redraw_all(self) :
        for widget in self.widgetList :
            force_redraw(widget)

def euclideanDistance(point1, point2):
    sumSqrDif = 0
    for (a,b) in zip(point1, point2):
        sumSqrDif += pow(a - b, 2)
    return math.sqrt(sumSqrDif)

class PointDrawModeEnum(object):
    doNotDraw = 0
    normal = 1
    highlight = 2

class DrawModeRef(object):
    def __init__(self, drawMode = PointDrawModeEnum.doNotDraw):
        self.drawMode = drawMode

class PointWithDrawModeRef(object) :
    def __init__(self, position, drawModeRef) :
        self.position = position
        self.drawModeRef = drawModeRef

class CairoImageWidgetEventHandler(object) :

    scale_scroll_multiplier = 1.02

    point_near_pointer_dist = 10

    def __init__(self, drawingArea, redrawManager = None):
        self.imageFilename = None
        self.pointList = None
        self.buttonPressStartPoss = None
        self.drawingArea = drawingArea
        self.imageToDispMatrix = cairo.Matrix()
        self.dispToImageMatrix = cairo.Matrix()

        self.showNumbers = False

        if redrawManager :
            self.redrawManager = redrawManager
        else :
            self.redrawManager = RedrawManager(drawingArea)

        self.cursorPosition = None
        self.near_point = None
        gtk.DrawingArea.__init__(drawingArea)

        drawingArea.connect("expose_event", self.on_expose_event)
        drawingArea.connect("scroll_event", self.on_scroll_event)
        drawingArea.connect("motion_notify_event", self.on_motion_notify_event)
        drawingArea.connect("button_press_event", self.on_button_press_event)
        drawingArea.connect("button_release_event", self.on_button_release_event)

    def on_file_set(self, widget) :
        self.imageFilename = widget.get_filename()

    def set_point_list(self, pointList) :
        self.pointList = pointList

    def on_expose_event(self, widget, event):
        context = widget.window.cairo_create()
        # set a clip region for the expose event
        context.rectangle(event.area[0], event.area[1],
                                event.area.width, event.area.height)
        context.clip()

        self.draw(context)

    def draw(self, context):
        context.set_matrix(self.imageToDispMatrix)

        if self.imageFilename :
            context.save()

            imSurface = cairo.ImageSurface.create_from_png(self.imageFilename)
            sizeOfDrawingAreaNeeded = self.imageToDispMatrix.transform_distance(imSurface.get_width(), imSurface.get_height())
            self.drawingArea.set_size_request(int(sizeOfDrawingAreaNeeded[0]), int(sizeOfDrawingAreaNeeded[1]))
            context.set_source_surface(imSurface)
            context.rectangle(0, 0,imSurface.get_width() , imSurface.get_height())
            context.fill()

            context.restore()
        if self.pointList :
            for point in self.pointList :
                if point.drawModeRef.drawMode != PointDrawModeEnum.doNotDraw :
                    context.save()

                    context.set_line_width(0.5 * context.get_line_width())
                    context.arc(point.position[0], point.position[1], 5, 0, 2 * math.pi)
                    if point.drawModeRef.drawMode == PointDrawModeEnum.highlight:
                        context.set_source_rgb(0.0, 1.0, 0.0)
                        context.fill()
                    elif point.drawModeRef.drawMode == PointDrawModeEnum.normal:
                        context.stroke()
                    context.restore()
            if self.showNumbers :
                for i in range(len(self.pointList)) :
                    context.save()
                    pc = pangocairo.CairoContext(context)
                    context.move_to(self.pointList[i].position[0], self.pointList[i].position[1])
                    textLayout = pc.create_layout()
                    textLayout.set_text(str(i))
                    pc.show_layout(textLayout)
                    context.restore()

            # if drawing rectangle
            if self.buttonPressStartPoss :
                context.save()
                context.set_line_width(0.2 * context.get_line_width())
                context.set_dash((3,3))
                context.move_to(self.buttonPressStartPoss[0], self.buttonPressStartPoss[1])
                context.line_to(self.cursorPosition[0], self.buttonPressStartPoss[1])
                context.line_to(self.cursorPosition[0], self.cursorPosition[1])
                context.stroke()
                context.move_to(self.buttonPressStartPoss[0], self.buttonPressStartPoss[1])
                context.line_to(self.buttonPressStartPoss[0], self.cursorPosition[1])
                context.line_to(self.cursorPosition[0], self.cursorPosition[1])
                context.stroke()
                context.restore()

        #if self.cursorPosition :
        #  context.save()
        #  context.set_line_width(0.5 * context.get_line_width())
        #  context.arc(self.cursorPosition[0], self.cursorPosition[1], 5, 0, 2 * math.pi)
        #  context.stroke()
        #  context.restore()

    def on_scroll_event(self, widget, event) :

        pointerPosStart = self.imageToDispMatrix.transform_point(self.cursorPosition[0], self.cursorPosition[1])
        if event.direction == gtk.gdk.SCROLL_UP:

            self.imageToDispMatrix.scale(self.scale_scroll_multiplier,
                                          self.scale_scroll_multiplier)


            xx, yx, xy, yy, x0, y0 = self.imageToDispMatrix
            self.dispToImageMatrix = cairo.Matrix(xx, yx, xy, yy, x0, y0)
            self.dispToImageMatrix.invert()


        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.imageToDispMatrix.scale(1.0/self.scale_scroll_multiplier,
                                          1.0/self.scale_scroll_multiplier)
            xx, yx, xy, yy, x0, y0 = self.imageToDispMatrix
            self.dispToImageMatrix = cairo.Matrix(xx, yx, xy, yy, x0, y0)
            self.dispToImageMatrix.invert()

        pointerPosEnd = self.imageToDispMatrix.transform_point(self.cursorPosition[0], self.cursorPosition[1])

        self.imageToDispMatrix.translate(-pointerPosEnd[0]+pointerPosStart[0],-pointerPosEnd[1]+pointerPosStart[1])
        xx, yx, xy, yy, x0, y0 = self.imageToDispMatrix
        self.dispToImageMatrix = cairo.Matrix(xx, yx, xy, yy, x0, y0)
        self.dispToImageMatrix.invert()

        self.redrawManager.force_redraw_all()



        return True

    def highlightPointsInRectangle(self, recPoint1, recPoint2):

        if self.cursorPosition[0] < self.buttonPressStartPoss[0] :
            minX = self.cursorPosition[0]
            maxX = self.buttonPressStartPoss[0]
        else :
            minX = self.buttonPressStartPoss[0]
            maxX = self.cursorPosition[0]

        if self.cursorPosition[1] < self.buttonPressStartPoss[1] :
            minY = self.cursorPosition[1]
            maxY = self.buttonPressStartPoss[1]
        else :
            minY = self.buttonPressStartPoss[1]
            maxY = self.cursorPosition[1]


        for point in self.pointList:
            if point.position[0] >= minX and point.position[0] <= maxX and point.position[1] >= minY and point.position[1] <= maxY:
                point.drawModeRef.drawMode = PointDrawModeEnum.highlight
            else :
                point.drawModeRef.drawMode = PointDrawModeEnum.normal

    def on_motion_notify_event(self, widget, event):
        prev_curs_point = self.cursorPosition
        prev_near_point = self.near_point

        self.near_point = None
        cur_min_dist = 100

        if event.is_hint :
            x, y, state = event.window.get_pointer()
            self.cursorPosition = x,y
        else :
            self.cursorPosition = event.x, event.y
            state = event.state

        self.cursorPosition = self.dispToImageMatrix.transform_point(self.cursorPosition[0], self.cursorPosition[1])

        if self.pointList :
            for point in self.pointList:
                cur_dist = euclideanDistance(self.cursorPosition, point.position)


                if cur_dist < self.point_near_pointer_dist and cur_dist < cur_min_dist :
                    cur_min_dist = cur_dist
                    self.near_point = point

        if prev_near_point and prev_near_point != self.near_point :
            prev_near_point.drawModeRef.drawMode = PointDrawModeEnum.normal
        if self.near_point :
            self.near_point.drawModeRef.drawMode = PointDrawModeEnum.highlight

        if self.buttonPressStartPoss and self.pointList :
            self.highlightPointsInRectangle(self.buttonPressStartPoss, self.cursorPosition)

        self.redrawManager.force_redraw_all()
        return True

    def on_button_press_event(self, widget, event) :
        if event.button == 1 : #button 1 pressed
            self.buttonPressStartPoss = self.dispToImageMatrix.transform_point(event.x, event.y)
    def on_button_release_event(self, widget, event) :
        if event.button == 1 :
            if self.buttonPressStartPoss and self.pointList :
                self.highlightPointsInRectangle(self.buttonPressStartPoss, self.cursorPosition)
            self.buttonPressStartPoss = None
            self.redrawManager.force_redraw_all()

    def on_leave_notify(self, widget, event):
        self.cursorPosition = None
        self.redrawManager.force_redraw_all()
        return True



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

        self.im1widgetHandler.imageFilename = os.path.normpath(projDir + '/' + line1.strip())
        self.im2widgetHandler.imageFilename = os.path.normpath(projDir + '/' + line2.strip())

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
        self.im1widgetHandler.imageFilename = self.im2widgetHandler.imageFilename
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
            on_saveAsMenuItem_activate(widget)
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

       #   matchList[0:1] = []

        pointList1 = []
        pointList2 = []
        for pointPairString in matchList :
            try :
                y1, x1, y2, x2 = map(float,pointPairString.split())

                if self.rowColRadioButton.get_active() :
                    point1 = x1, y1
                    point2 = x2, y2
                else :
                    point1 = y1, x1
                    point2 = y2, x2


                curDrawModeRef = DrawModeRef(PointDrawModeEnum.normal)

                pointList1.append(PointWithDrawModeRef(point1,curDrawModeRef))

                pointList2.append(PointWithDrawModeRef(point2,curDrawModeRef))

            except ValueError:
                pass


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




    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("MatchViewer.glade")

        drawArea1 = self.builder.get_object("im1DrawingArea")
        drawArea2 = self.builder.get_object("im2DrawingArea")

        self.redrawManager = RedrawManager([drawArea1, drawArea2])

        self.im1widgetHandler = CairoImageWidgetEventHandler(drawArea1, self.redrawManager)
        self.im2widgetHandler = CairoImageWidgetEventHandler(drawArea2, self.redrawManager)


     #   self.builder.connect_signals()
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
