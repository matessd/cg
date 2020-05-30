#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import cg_algorithms as alg
import math
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    qApp,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsItem,
    QListWidget,
    QHBoxLayout,
    QWidget,
    QStyleOptionGraphicsItem,
    QColorDialog, QInputDialog, QFileDialog)
from PyQt5.QtGui import QPainter, QMouseEvent, QColor, QPixmap
from PyQt5.QtCore import QRectF

global g_penColor #used when set pencolor
g_penColor = QColor(0,0,0) #black
# size of canvas
global g_width, g_height
g_width = g_height = 600
# if the last item is over
global g_draw_finish
g_draw_finish = 1

class MyCanvas(QGraphicsView):
    """
    画布窗体类，继承自QGraphicsView，采用QGraphicsView、QGraphicsScene、QGraphicsItem的绘图框架
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.main_window = None
        self.list_widget = None
        self.item_dict = {}
        self.selected_id = ''

        self.status = ''
        self.temp_algorithm = ''
        self.temp_id = '-1'
        #draw polygon need temp_item to judge start 
        self.temp_item = MyItem(self.temp_id, 'noneType', \
                                    [[0, 0], [0, 0]], 'noneAlg')

    #clear canvas
    def clear_canvas(self):
        #clear
        self.scene().clear()
        self.list_widget.clear()
        self.main_window.reset_id()
        self.item_dict = {}
        self.selected_id = ''

        self.status = ''
        self.temp_algorithm = ''
        self.temp_id = '-1'
        self.temp_item = MyItem(self.temp_id, 'noneType', \
                                    [[0, 0], [0, 0]], 'noneAlg')      
        global g_draw_finish
        g_draw_finish = 1
    
    def start_draw(self, status, algorithm):
        self.check_finish()
        global g_draw_finish
        g_draw_finish = 0
        self.status = status
        self.temp_algorithm = algorithm
        self.temp_id = self.main_window.get_id()
    
    def finish_draw(self):
        global g_draw_finish
        g_draw_finish = 1
        self.main_window.id_inc()
        self.temp_id = self.main_window.get_id()
        
    def check_finish(self):
        if g_draw_finish == 1:
            return 
        # finish the last item
        if self.status == 'polygon':
            # 多边形没画完就去干别的了
            if self.temp_item.p_list[0] != self.temp_item.p_list[-1]:
                self.temp_item.p_list.append(self.temp_item.p_list[0])
                self.updateScene([self.sceneRect()])
        self.finish_draw()
        
    def clear_selection(self):
        if self.selected_id != '':
            self.item_dict[self.selected_id].selected = False
            self.selected_id = ''

    def selection_changed(self, selected):
        self.check_finish()
        self.main_window.statusBar().showMessage('图元选择： %s' % selected)
        if self.selected_id != '':
            self.item_dict[self.selected_id].selected = False
            self.item_dict[self.selected_id].update()
        strList = selected.split()
        self.selected_id = strList[-1]
        self.item_dict[self.selected_id].selected = True
        self.item_dict[self.selected_id].update()
        self.status = ''
        self.updateScene([self.sceneRect()])
        
    def selectedItemClear(self):
        if self.selected_id == '':
            return
        self.item_dict[self.selected_id].trans_clear()
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        if self.status == 'line' or self.status == 'ellipse':
            self.temp_item = MyItem(self.temp_id, self.status, \
                                    [[x, y], [x, y]], self.temp_algorithm)
            self.scene().addItem(self.temp_item)
        elif self.status == 'polygon':
            if self.temp_item.id != self.main_window.get_id():
                self.temp_item = MyItem(self.temp_id, self.status, \
                                        [[x, y], [x, y]], self.temp_algorithm)
                self.scene().addItem(self.temp_item)          
            else:
                self.temp_item.p_list.append([x,y])
        elif self.status == 'curve':
            if self.temp_item.id != self.main_window.get_id():
                self.temp_item = MyItem(self.temp_id, self.status, \
                                        [[x, y], [x, y]], self.temp_algorithm)
                self.scene().addItem(self.temp_item)          
            else:
                if self.temp_algorithm == 'B-spline':
                    self.temp_item.p_list.append([x,y])   
                else :
                    self.temp_item.p_list.insert(-1, [x,y])   
        elif self.status == 'translate':
            if self.selected_id == '':
                return
            sid = self.selected_id
            self.item_dict[sid].trans_type = 'translate'
            self.item_dict[sid].center = [x,y]
            self.item_dict[sid].poi = [x,y]
            self.item_dict[sid].trans_over = 0
        elif self.status == 'rotate' or self.status == 'scale':
            if self.selected_id == '':
                return
            sid = self.selected_id
            if self.item_dict[sid].param_cnt == 0:
                self.item_dict[sid].trans_type = self.status
                self.item_dict[sid].center = [x,y]
                self.item_dict[sid].trans_over = 0
                self.item_dict[sid].param_cnt = 1
            elif self.item_dict[sid].param_cnt == 1:
                self.item_dict[sid].poi = [x,y]
                self.item_dict[sid].poi1 = [x,y]
                self.item_dict[sid].param_cnt = 2
            else:
                # cannot appear this situation, clear
                self.item_dict[sid].trans_clear()
        self.updateScene([self.sceneRect()])
        #self.updateScene([self.temp_item.boundingRect()])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        if self.status == 'line' or self.status == 'ellipse':
            self.temp_item.p_list[1] = [x, y]
        elif self.status == 'polygon':
            self.temp_item.p_list[-1] = [x, y]
        elif self.status == 'curve':
            le = len(self.temp_item.p_list)
            if self.temp_algorithm == 'B-spline':
                self.temp_item.p_list[-1] = [x, y]
            else:
                if le <= 2: 
                    self.temp_item.p_list[-1] = [x, y]
                else:
                    self.temp_item.p_list[-2] = [x, y]
        elif self.status == 'translate':
            if self.selected_id == '':
                return
            sid = self.selected_id
            self.item_dict[sid].trans_type = 'translate'
            self.item_dict[sid].poi = [x,y]  
            # self.item_dict[sid].trans_over = 0
        elif self.status == 'rotate' or self.status == 'scale':
            if self.selected_id == '':
                return
            sid = self.selected_id
            if self.item_dict[sid].param_cnt == 1:
                pass
            elif self.item_dict[sid].param_cnt == 2:
                self.item_dict[sid].poi1 = [x,y]                
            else:
                self.item_dict[sid].trans_clear()
        self.updateScene([self.sceneRect()])
        #self.updateScene([self.temp_item.boundingRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        def if_close(pos0, pos1):
            """
            判断两个点是否足够近,用于多边形的闭合
            """
            if abs(pos0[0]-pos1[0])<=5 and abs(pos0[1]-pos1[1])<=5:
                return True
            else :
                return False
        
        # main
        if self.status == 'line' or self.status == 'ellipse':
            self.item_dict[self.temp_id] = self.temp_item
            self.list_widget.addItem(self.status+" "+self.temp_id)
            self.finish_draw()
        elif self.status == 'polygon':
            if self.temp_id not in self.item_dict:
            #add into item_dict
                self.item_dict[self.temp_id] = self.temp_item
                self.list_widget.addItem(self.status+" "+self.temp_id)
            elif len(self.temp_item.p_list)>=4 and\
                if_close(self.temp_item.p_list[0], self.temp_item.p_list[-1]):
            #finish draw polygon
                #[-1] and [0] refer to the same vertex
                self.temp_item.p_list[-1] = self.temp_item.p_list[0]
                self.finish_draw()
                self.updateScene([self.sceneRect()])
        elif self.status == 'curve':
            if self.temp_id not in self.item_dict:
            #add into item_dict
                self.item_dict[self.temp_id] = self.temp_item
                self.list_widget.addItem(self.status+" "+self.temp_id)    
        elif self.status == 'translate':
            if self.selected_id == '':
                return
            sid = self.selected_id
            # change item p_list
            self.item_dict[sid].trans_over = 1
            # updateScene是super()时执行的
            self.updateScene([self.sceneRect()])
        elif self.status == 'rotate' or self.status == 'scale':
            if self.selected_id == '':
                return
            sid = self.selected_id
            if self.item_dict[sid].param_cnt == 1:
                pass
            elif self.item_dict[sid].param_cnt == 2:
                self.item_dict[sid].trans_over = 1               
            else:
                self.item_dict[sid].trans_clear()
            self.updateScene([self.sceneRect()])
        super().mouseReleaseEvent(event)


class MyItem(QGraphicsItem):
    """
    自定义图元类，继承自QGraphicsItem
    """
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        """
        :param item_id: 图元ID
        :param item_type: 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        :param p_list: 图元参数
        :param algorithm: 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        :param parent:
        """
        super().__init__(parent)
        self.id = item_id           # 图元ID
        self.item_type = item_type  # 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        self.p_list = p_list        # 图元参数
        self.algorithm = algorithm  # 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        self.selected = False
        
        self.penColor = g_penColor  # 自己的penColor
        # for transformation
        self.trans_type = ''
        self.poi = [0,0] # [x,y] of move
        self.center = [0,0] # [x,y] of center
        self.trans_over = 0 # if the transformation operation over
        self.param_cnt = 0 # some operation needs 2 mouse_press
        
    def trans_clear(self):
        self.trans_type = ''
        self.center = [0,0]
        self.poi = [0,0]
        self.trans_over = 0   
        self.param_cnt = 0
        
    #gui会在鼠标事件自动调用paint重新绘制所有图元
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.penColor)
        item_pixels = []
        def draw(p_list, algorithm):
            # draw figure
            result = []
            if self.item_type == 'line':
                result = alg.draw_line(p_list, algorithm)
            elif self.item_type == 'polygon':
                # 画边
                for i in range(0,len(p_list)-1):
                    result.extend(alg.draw_line([p_list[i],\
                                p_list[i+1]], algorithm))
            elif self.item_type == 'ellipse':
                result = alg.draw_ellipse(p_list)
            elif self.item_type == 'curve':
                result = alg.draw_curve(p_list, algorithm)  
            return result
        
        def angle(v1, v2):
            """计算v2相对于v1的顺时针角度
            v1 = [[x0,y0],[x1,y1]], v2同理
            """
            dx1 = v1[1][0] - v1[0][0]
            dy1 = v1[1][1] - v1[0][1]
            dx2 = v2[1][0] - v2[0][0]
            dy2 = v2[1][1] - v2[0][1]
            angle1 = math.atan2(dy1, dx1)
            angle1 = int(angle1 * 180/math.pi)
            angle2 = math.atan2(dy2, dx2)
            angle2 = int(angle2 * 180/math.pi)
            ret = angle2 - angle1
            return ret
        
        # choose p_list accoring to trans_type
        new_p_list = self.p_list
        if self.trans_type == 'translate':
            new_p_list = alg.translate(self.p_list, self.poi[0]-self.center[0], \
                                        self.poi[1]-self.center[1])
            if self.trans_over == 1:
                # clear
                self.trans_clear()
                # chang p_list
                self.p_list = new_p_list
        elif self.trans_type == 'rotate':
            if self.item_type == 'ellipse':
                print("Can't rotate ellipse")
                return 
            if self.param_cnt == 2:
                theta = angle([self.center, self.poi], [self.center, self.poi1])
                new_p_list = alg.rotate(self.p_list, \
                                self.center[0], self.center[1], theta)
            if self.trans_over == 1:
                # clear
                self.trans_clear()
                # chang p_list
                self.p_list = new_p_list      
        elif self.trans_type == 'scale':
            if self.param_cnt == 2:
                # 缩放倍数, 根据dx的比值确定
                if self.poi[0]-self.center[0] == 0:
                    s = 1
                else :
                    s = (self.poi1[0]-self.center[0])/(self.poi[0]-self.center[0])
                new_p_list = alg.scale(self.p_list, \
                                self.center[0], self.center[1], s)
            if self.trans_over == 1:
                # clear
                self.trans_clear()
                # chang p_list
                self.p_list = new_p_list    
        item_pixels = draw(new_p_list, self.algorithm)
        # draw
        for p in item_pixels:
            painter.drawPoint(*p)
        # draw bound
        if self.selected:
            painter.setPen(QColor(255, 0, 0))
            painter.drawRect(self.regionRect(new_p_list))  
    
    #绘制item时所需范围
    def boundingRect(self) -> QRectF:
        x,y,w,h = self.compute_region(self.p_list)
        return QRectF(x - 1, y - 1, w + 2, h + 2)
    
    def regionRect(self, new_p_list) -> QRectF:
        x,y,w,h = self.compute_region(new_p_list)
        return QRectF(x - 1, y - 1, w + 2, h + 2)
    
    def compute_region(self, new_p_list):
        x,y,w,h = [0,0,0,0]
        if self.item_type == 'line' or self.item_type == 'ellipse':
            x0, y0 = new_p_list[0]
            x1, y1 = new_p_list[1]
            x = min(x0, x1)
            y = min(y0, y1)
            w = max(x0, x1) - x
            h = max(y0, y1) - y
        elif self.item_type == 'polygon' or self.item_type == 'curve':
            x, y = new_p_list[0]
            w, h = new_p_list[0]
            for i in range(len(new_p_list)):
                if x > new_p_list[i][0]:
                    x = new_p_list[i][0]
                if y > new_p_list[i][1]:
                    y = new_p_list[i][1]
                if w < new_p_list[i][0]:
                    w = new_p_list[i][0]
                if h < new_p_list[i][1]:
                    h = new_p_list[i][1]
            w = w-x
            h = h-y
        return [x,y,w,h]
    """
    def compute_center(self):
        x,y,w,h = self.compute_region()
        midx = (x+w)//2
        midy = (y+h)//2
        return [midx,midy]
    """

class MainWindow(QMainWindow):
    """
    主窗口类
    """
    def __init__(self):
        super().__init__()
        self.item_cnt = 0

        # 使用QListWidget来记录已有的图元，并用于选择图元。
        # 注：这是图元选择的简单实现方法，更好的实现是在画布中直接用鼠标选择图元
        self.list_widget = QListWidget(self)
        self.list_widget.setMinimumWidth(200)

        # 使用QGraphicsView作为画布
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, g_width, g_height)
        self.canvas_widget = MyCanvas(self.scene, self)
        self.canvas_widget.setFixedSize(g_width, g_height)
        self.canvas_widget.main_window = self
        self.canvas_widget.list_widget = self.list_widget

        # 设置菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        set_pen_act = file_menu.addAction('设置画笔')
        reset_canvas_act = file_menu.addAction('重置画布')
        save_canvas_act = file_menu.addAction('保存画布')
        exit_act = file_menu.addAction('退出')
        draw_menu = menubar.addMenu('绘制')
        line_menu = draw_menu.addMenu('线段')
        #line_naive_act = line_menu.addAction('Naive')
        line_dda_act = line_menu.addAction('DDA')
        line_bresenham_act = line_menu.addAction('Bresenham')
        polygon_menu = draw_menu.addMenu('多边形')
        polygon_dda_act = polygon_menu.addAction('DDA')
        polygon_bresenham_act = polygon_menu.addAction('Bresenham')
        ellipse_act = draw_menu.addAction('椭圆')
        curve_menu = draw_menu.addMenu('曲线')
        curve_bezier_act = curve_menu.addAction('Bezier')
        curve_b_spline_act = curve_menu.addAction('B-spline')
        edit_menu = menubar.addMenu('编辑')
        translate_act = edit_menu.addAction('平移')
        rotate_act = edit_menu.addAction('旋转')
        scale_act = edit_menu.addAction('缩放')
        clip_menu = edit_menu.addMenu('裁剪')
        clip_cohen_sutherland_act = clip_menu.addAction('Cohen-Sutherland')
        clip_liang_barsky_act = clip_menu.addAction('Liang-Barsky')

        # 连接信号和槽函数
        # 画笔
        set_pen_act.triggered.connect(self.pen_color_change)
        # reset canvas
        reset_canvas_act.triggered.connect(self.reset_canvas)
        # 保存画布
        save_canvas_act.triggered.connect(self.save_canvas)
        # 退出
        exit_act.triggered.connect(qApp.quit)
        # line
        #line_naive_act.triggered.connect(self.line_naive_action)
        line_dda_act.triggered.connect(self.line_dda_action)
        line_bresenham_act.triggered.connect(self.line_bresenham_action)
        # polygon
        polygon_dda_act.triggered.connect(self.polygon_dda_action)
        polygon_bresenham_act.triggered.connect(self.polygon_bresenham_action)
        # ellipse
        ellipse_act.triggered.connect(self.ellipse_action)
        # curve
        curve_bezier_act.triggered.connect(self.curve_bezier_action)
        curve_b_spline_act.triggered.connect(self.curve_b_spline_action)
        # 平移
        translate_act.triggered.connect(self.translate_action)
        # 旋转
        rotate_act.triggered.connect(self.rotate_action)
        # 缩放
        scale_act.triggered.connect(self.scale_action)
        
        self.list_widget.currentTextChanged.connect(self.canvas_widget.selection_changed)

        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.hbox_layout.addWidget(self.list_widget, stretch=1)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲')
        self.resize(g_width, g_height)
        self.setWindowTitle('CG Demo')

    #clear and resize canvas
    def reset_canvas(self):
        self.statusBar().showMessage('重置画布')
        self.canvas_widget.clear_canvas()
        #resize
        text1,ok1 = QInputDialog.getText(self, '输入画布尺寸', 'x轴大小:')
        text2,ok2 = QInputDialog.getText(self, '输入画布尺寸', 'y轴大小:')
        if ok1!=1 or ok2!=1:
            return
        x = int(text1)
        y = int(text2)
        if x>1000 or x<100 or y>1000 or y<100:
            print("Resize Error: x>1000 or x<100 or y>1000 or y<100.")
            return
        self.canvas_widget.setFixedSize(x, y)
        self.scene.setSceneRect(0, 0, x, y)
        self.resize(x, y)
        global g_width, g_height
        g_width= x
        g_height = y
    
    #保存画布
    def save_canvas(self):
        self.statusBar().showMessage('保存画布')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection() 
        # 令前一个没完成图形完成
        self.canvas_widget.check_finish()
        
        fname = QFileDialog.getSaveFileName(self, 'Save file',\
                                        '/home/output/default','Image files (*.bmp)')        
        #cancel save
        if(fname[0]==''):
            return
        # Get QRectF
        rect = self.scene.sceneRect()
        # Create a pixmap, fill with white color
        pixmap = QPixmap(g_width, g_height)
        pixmap.fill(QColor(255,255,255))
        # painter
        painter = QPainter(pixmap)
        # Render scene to the pixmap
        self.scene.render(painter, rect, rect)
        painter.end()
        # save bmp file
        pixmap.save(fname[0])    
    
    def get_id(self):
        _id = str(self.item_cnt)
        #self.item_cnt += 1
        return _id
    
    def id_inc(self):
        self.item_cnt += 1
    
    def reset_id(self):
        self.item_cnt = 0
     
    #从QColorDialog中选取颜色,并设置为pen的颜色
    def pen_color_change(self):
        self.statusBar().showMessage('设置画笔颜色')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection() 
        # 设置画笔颜色也会令前一个没完成图形完成
        self.canvas_widget.check_finish()
        global g_penColor
        color = QColorDialog.getColor()
        g_penColor = color
    
    """    
    #绘制线段
    def line_naive_action(self):
        self.canvas_widget.start_draw_line('Naive', self.get_id())
        self.statusBar().showMessage('Naive算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()   
    """
    
    #DDA绘制线段    
    def line_dda_action(self):
        self.canvas_widget.start_draw('line', 'DDA')
        self.statusBar().showMessage('DDA算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection() 
        
    #Bresenham绘制线段
    def line_bresenham_action(self):
        self.canvas_widget.start_draw('line','Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()
    
    def polygon_bresenham_action(self):
        self.canvas_widget.start_draw('polygon','Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制多边形')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()
        
    def polygon_dda_action(self):
        self.canvas_widget.start_draw('polygon','DDA')
        self.statusBar().showMessage('DDA算法绘制多边形')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()
    
    def ellipse_action(self):
        self.canvas_widget.start_draw('ellipse','default')
        self.statusBar().showMessage('绘制椭圆')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()      
        
    def curve_bezier_action(self):
        self.canvas_widget.start_draw('curve','Bezier')
        self.statusBar().showMessage('Bezier算法绘制曲线')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()       
        
    def curve_b_spline_action(self):
        self.canvas_widget.start_draw('curve','B-spline')
        self.statusBar().showMessage('B_spline算法绘制曲线')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection() 
    
    # 平移
    def translate_action(self):
        self.canvas_widget.status = 'translate'
        self.statusBar().showMessage('平移选中图元')
        self.canvas_widget.selectedItemClear()
        
    # 旋转
    def rotate_action(self):
        self.canvas_widget.status = 'rotate'
        self.statusBar().showMessage('旋转选中图元')
        self.canvas_widget.selectedItemClear()
    
    # 缩放
    def scale_action(self):
        self.canvas_widget.status = 'scale'
        self.statusBar().showMessage('缩放选中图元')
        self.canvas_widget.selectedItemClear()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    app.exec_()
    del app
    #sys.exit(0)