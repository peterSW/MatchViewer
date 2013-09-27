import pygtk
pygtk.require("2.0")
import gtk
import cairo
import pangocairo
import math
import os

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

    def __str__(self):
        if(self.drawMode == PointDrawModeEnum.doNotDraw):
            return "doNotDraw"
        elif(self.drawMode == PointDrawModeEnum.normal):
            return "normal"
        else:
            return "highlight"

class PointWithDrawModeRef(object) :
    def __init__(self, position, drawModeRef, similarity, ambiguity, drawColour = (0,0,0)) :
        self.position = position
        self.drawModeRef = drawModeRef
        self.similarity = similarity
        self.ambiguity = ambiguity

        self.drawColour = drawColour

    def __str__(self):
        return "Position: " + str(self.position) + "  drawMode: " + str(self.drawModeRef) +  "  drawColour: " + str(self.drawColour)

class CairoImageWidgetEventHandler(object) :

    scale_scroll_multiplier = 1.02

    point_near_pointer_dist = 10

    def __init__(self, drawingArea, redrawManager = None):
        self.imSurface = None
        self.overlayImSurface = None
        self.overlayAlpha = 0.5
        self.pointList = None
        self.buttonPressStartPoss = None
        self.drawingArea = drawingArea
        self.imageToDispMatrix = cairo.Matrix()
        self.dispToImageMatrix = cairo.Matrix()

        self.showNumbers = False
        self.showSimilarity = False
        self.showAmbiguity = False

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
        self.set_image_file(widget.get_filename())

    def set_point_list(self, pointList) :
        self.pointList = pointList

    def set_image_file(self, imageFN):
        if imageFN and os.path.exists(imageFN):
            self.imageFilename = imageFN
            self.imSurface = cairo.ImageSurface.create_from_png(imageFN)
    def set_overlay_image_file(self, imageFN):
        print "setting overlay image to: ", imageFN
        if imageFN and os.path.exists(imageFN):
            self.overlayImSurface = cairo.ImageSurface.create_from_png(imageFN)
    def set_overlay_alpha(self, alpha, redraw = True):
        print "overlay Alpha set to: ", alpha
        self.overlayAlpha = alpha
        if redraw:
            self.redraw()

    def on_expose_event(self, widget, event):
        context = widget.window.cairo_create()
        # set a clip region for the expose event
        context.rectangle(event.area[0], event.area[1],
                                event.area.width, event.area.height)
        context.clip()

        self.draw(context)

    def draw(self, context):
        context.set_matrix(self.imageToDispMatrix)

        if self.imSurface :
            context.save()

            sizeOfDrawingAreaNeeded = self.imageToDispMatrix.transform_distance(self.imSurface.get_width(), self.imSurface.get_height())
            self.drawingArea.set_size_request(int(sizeOfDrawingAreaNeeded[0]), int(sizeOfDrawingAreaNeeded[1]))
            context.set_source_surface(self.imSurface)
            context.rectangle(0, 0,self.imSurface.get_width() , self.imSurface.get_height())
            context.paint()

            context.restore()

        if self.overlayImSurface:
            context.save()

            sizeOfDrawingAreaNeeded = self.imageToDispMatrix.transform_distance(self.imSurface.get_width(), self.imSurface.get_height())
            self.drawingArea.set_size_request(int(sizeOfDrawingAreaNeeded[0]), int(sizeOfDrawingAreaNeeded[1]))
            context.set_source_surface(self.overlayImSurface)
            context.rectangle(0, 0,self.overlayImSurface.get_width() , self.overlayImSurface.get_height())
            context.paint_with_alpha(self.overlayAlpha)

            context.restore()


        if self.pointList :
            for point in self.pointList :
                if point.drawModeRef.drawMode != PointDrawModeEnum.doNotDraw :
                    context.save()
                    context.new_sub_path()
                    context.set_line_width(0.5 * context.get_line_width())
                    context.arc(point.position[0], point.position[1], 5, 0, 2 * math.pi)
                    if point.drawModeRef.drawMode == PointDrawModeEnum.highlight:
                        context.set_source_rgb(0.0, 1.0, 0.0)
                        context.stroke()
                        #context.new_sub_path()
                        if self.showSimilarity :
                            pc = pangocairo.CairoContext(context)
                            context.move_to(point.position[0], point.position[1])
                            textLayout = pc.create_layout()
                            textLayout.set_text(str(point.similarity))
                            pc.show_layout(textLayout)
                            #context.new_sub_path()
                        if self.showAmbiguity :
                            pc = pangocairo.CairoContext(context)
                            context.move_to(point.position[0], point.position[1]-30)
                            textLayout = pc.create_layout()
                            textLayout.set_text(str(point.ambiguity))
                            pc.show_layout(textLayout)
                           # context.new_sub_path()
                    elif point.drawModeRef.drawMode == PointDrawModeEnum.normal:
                        context.set_source_rgb(point.drawColour[0],point.drawColour[1],point.drawColour[2])
                        context.stroke()

                        #context.new_sub_path()
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

        # if near point has changed
        if prev_near_point != self.near_point :
            # if there was a previous point
            if prev_near_point :
                prev_near_point.drawModeRef.drawMode = PointDrawModeEnum.normal

                if prev_near_point.similarity:
                    self.statusbar.pop(self.statusbarContext)
            # if there is a near point
            if self.near_point:
                if self.near_point.similarity:
                    self.statusbar.push(self.statusbarContext, "Similatity: " + self.near_point.similarity + "  Ambiguity: " + str(1.0/float(self.near_point.ambiguity)))



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

    def redraw(self):
        force_redraw(self.drawingArea)

def loadMatchList(filename, switchXY = False, colour = (0,0,0)):
    matchListFile = open(filename)
    matchList = []
    for line in matchListFile :
        matchList.append(line)

   #   matchList[0:1] = []

    if isinstance(colour, gtk.gdk.Color):
        colour = colour.red_float, colour.green_float, colour.blue_float

    pointList1 = []
    pointList2 = []
    for pointPairString in matchList :
        try :
            pointPairString = pointPairString.split()
            y1, x1, y2, x2 = map(float,pointPairString[:4])

            if switchXY :
                point1 = x1, y1
                point2 = x2, y2
            else :
                point1 = y1, x1
                point2 = y2, x2

            similarity = None
            ambiguity = None
            if len(pointPairString) == 6 :
                similarity = pointPairString[4]
                ambiguity = pointPairString[5]



            curDrawModeRef = DrawModeRef(PointDrawModeEnum.normal)

            pointList1.append(PointWithDrawModeRef(point1,curDrawModeRef, similarity, ambiguity, colour))

            pointList2.append(PointWithDrawModeRef(point2,curDrawModeRef, similarity, ambiguity, colour))

        except ValueError:
            pass

    return pointList1, pointList2
