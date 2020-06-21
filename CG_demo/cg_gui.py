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
    QColorDialog, QInputDialog, QFileDialog,
    QAction,QToolBar)
from PyQt5.QtGui import (
    QPainter, QMouseEvent, QColor, QPixmap,QTransform)
from PyQt5.QtCore import QRectF, Qt,QSignalBlocker

global g_penColor #used when set pencolor
g_penColor = QColor(0,0,0) #black
# size of canvas
global g_width, g_height
g_width = g_height = 600
# is_draw_finish, status
global g_draw_finish, g_draw_status, g_edit_status
# for access
global g_list_widget, g_window, g_canvas
global g_transform

g_draw_finish = 1
g_draw_status = ["line","ellipse", "polygon","curve"]
g_edit_status = ['translate','rotate','scale','clip']
g_transform = QTransform()

def is_close(pos0, pos1):
    """判断两个点是否足够近,用于多边形的闭合和选择图元"""
    if abs(pos0[0]-pos1[0])<=5 and abs(pos0[1]-pos1[1])<=5:
        return True
    else :
        return False

def atoi(s):
   s = s[::-1]
   num = 0
   for i, v in enumerate(s):
      for j in range(0, 10):
         if v == str(j):
            num += j * (10 ** i)
   return num

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
        self.cur_id = ''
        #draw polygon need temp_item to judge start 
        self.temp_item = MyItem(self.temp_id, 'noneType', \
                                    [[0, 0], [0, 0]], 'noneAlg')
        # 拖动画布时判断画布的缩放情况
        self.is_image_scaling = 0

    #clear canvas
    def clear_canvas(self):
        #clear
        self.list_widget.clear()
        self.clear_scene()
        self.main_window.reset_id()
        self.item_dict = {}
        self.selected_id = ''

        self.status = ''
        self.temp_algorithm = ''
        self.temp_id = '-1'
        self.cur_id = ''
        self.temp_item = MyItem(self.temp_id, 'noneType', \
                                    [[0, 0], [0, 0]], 'noneAlg')      
        global g_draw_finish
        g_draw_finish = 1
        global g_penColor
        g_penColor = QColor(0,0,0)
    
    def clear_scene(self):
        for item in self.scene().items():
            self.scene().removeItem(item)
    
    def start_draw(self, status, algorithm):
        self.check_finish()
        global g_draw_finish
        g_draw_finish = 0
        self.status = status
        self.temp_algorithm = algorithm
        self.temp_id = self.main_window.get_id()
        
    def selectedItemClear(self):
        if self.selected_id == '':
            return
        self.item_dict[self.selected_id].edit_clear()
        
    def start_edit(self, status, algorithm):
        self.check_finish()
        global g_draw_finish
        g_draw_finish = 0
        self.status = status
        self.temp_algorithm = algorithm
        self.selectedItemClear()
    
    def finish_draw(self):
        global g_draw_finish
        g_draw_finish = 1
        self.main_window.id_inc()
        self.temp_id = self.main_window.get_id()
        
    def check_finish(self):
        """for key_id in list(self.item_dict.keys()):
            item = self.item_dict[key_id]
            if item.item_type == 'delete':
                self.scene().removeItem(item)
                del self.item_dict[key_id]"""
        global g_draw_finish
        if g_draw_finish == 1:
            return 
        # finish the last item
        if self.status == 'polygon':
            # 多边形没画完就去干别的了
            if self.temp_item.p_list[0] != self.temp_item.p_list[-1]:
                tmp_p_list = self.temp_item.p_list[0][:]
                self.temp_item.p_list.append(tmp_p_list)
                self.updateScene([self.sceneRect()])
        self.finish_draw()
        
    def clear_selection(self):
        # 避免只剩一个item的时候QListWidget无法两次选中
        """if g_list_widget.count()==1:
            g_list_widget.setCurrentRow(-1)"""
        self.list_widget.clearSelection()
        if self.selected_id != '':
            if self.selected_id in self.item_dict.keys():
                self.item_dict[self.selected_id].selected = False
            self.selected_id = ''

    def selection_changed(self, selected):
        self.check_finish()
        self.main_window.statusBar().clearMessage()
        self.main_window.statusBar().showMessage('图元选择： %s' % selected)
        if self.selected_id != '':
            if self.selected_id in self.item_dict.keys():
                self.item_dict[self.selected_id].selected = False
                self.item_dict[self.selected_id].update()
            self.selected_id = ''
        strList = selected.split()
        if strList == []:
            # 重置画布的时候也会进入这个函数
            return
        self.selected_id = strList[-1]
        self.item_dict[self.selected_id].selected = True
        self.item_dict[self.selected_id].update()
        # can continously choose by click
        if self.status != 'choose':
            self.status = ''
        self.updateScene([self.sceneRect()])
        
    def choose_item(self):
        self.status = 'choose'
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        self.cur_id = ''
        
        # choose item by clicking canvas
        if self.status == 'choose':
            # item = g_canvas.scene().itemAt(x, y, g_transform)
            items = g_canvas.scene().items()
            pos = [x,y]
            # break_flg
            b_flg = False
            id = ''
            # select in canvas
            for item in items:
                if b_flg:
                    break
                for coor in item.pixels:
                    if is_close(coor, pos):
                        b_flg = True
                        self.selection_changed(item.id)
                        id = item.id
                        break
            # select in list_widget
            for i in range(g_list_widget.count()):
                widget_item = g_list_widget.item(i)
                strList = widget_item.text().split()
                if(strList[-1] == id):
                    QSignalBlocker(g_list_widget)
                    widget_item.setSelected(True)
                    break
        
        # 点击边界外附近时拖动画布
        if g_width-5 <= x <= g_width+5 and g_height-5 <= y <= g_height+5:
            self.is_image_scaling = 3  
        elif g_width-5 <= x <= g_width+5:  
            self.is_image_scaling = 1  
        elif g_height-5 <= y <= g_height+5:  
            self.is_image_scaling = 2
        
        def press_draw():
            global g_draw_status
            if self.status not in g_draw_status:
                return ''
            if self.temp_item.id != self.main_window.get_id():
                self.temp_item = MyItem(self.temp_id, self.status, \
                                        [[x, y], [x, y]], self.temp_algorithm)
                self.scene().addItem(self.temp_item)
            else:
                # needs more than two points
                if self.status == 'polygon':
                    self.temp_item.p_list.append([x,y])
                elif self.status == 'curve':
                    self.temp_item.p_list.insert(-1, [x,y])
            return self.temp_item.id
        
        def press_edit():
            if self.selected_id == '' or self.status not in g_edit_status:
                return ''
            sid = self.selected_id
            if self.status in ['translate','clip']:
                if self.status == 'clip' \
                and self.item_dict[sid].item_type != 'line':
                    g_window.statusBar().showMessage('不能裁剪非线段')
                    self.status = ''
                else:
                    self.item_dict[sid].edit_type = self.status
                    self.item_dict[sid].poi = [x,y]
                    self.item_dict[sid].poi1 = [x,y]
                    self.item_dict[sid].edit_algorithm = self.temp_algorithm
                    self.item_dict[sid].edit_over = 0
            elif self.status in ['rotate', 'scale']:
                if self.item_dict[sid].param_cnt == 0:
                    self.item_dict[sid].edit_type = self.status
                    self.item_dict[sid].center = [x,y]
                    self.item_dict[sid].edit_over = 0
                    self.item_dict[sid].param_cnt = 1
                elif self.item_dict[sid].param_cnt == 1:
                    self.item_dict[sid].poi = [x,y]
                    self.item_dict[sid].poi1 = [x,y]
                    self.item_dict[sid].param_cnt = 2
                else:
                    # cannot appear this situation, clear
                    print("error, rotate or scale not over")
            else:
                print("Undefined Behavior: No such edit situation")
                return ''
            return sid
        
        # draw or edit
        if self.is_image_scaling == 0:
            dealing_id = press_draw()
            if dealing_id != '':
                self.cur_id = dealing_id
            dealing_id = press_edit()
            if dealing_id != '':
                self.cur_id = dealing_id
        self.updateScene([self.sceneRect()])
        #self.updateScene([self.temp_item.boundingRect()])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        
        def get_real_bound(x):
            """得到不超过限制的真实边界"""
            x_max = 600
            if x>=1000:
                x_max = 1000
            elif x<=100:
                x_max = 100
            else:
                x_max = x
            return x_max

        # 缩放画布功能
        if self.is_image_scaling > 0:
            global g_width, g_height
            if self.is_image_scaling == 1:  
                g_width = get_real_bound(x)
            elif self.is_image_scaling == 2:
                g_height = get_real_bound(y)
            else:  
                g_width = get_real_bound(x)
                g_height = get_real_bound(y)
            self.resize(g_width+10, g_height+10)
            self.scene().setSceneRect(0, 0, g_width, g_height)
            self.main_window.resize(g_width, g_height)
        
        def move_draw():
            if self.status not in g_draw_status:
                return
            if self.status in ['line','ellipse','polygon']:
                self.temp_item.p_list[-1] = [x, y]
            elif self.status == 'curve':
                le = len(self.temp_item.p_list)
                if le <= 2: 
                    self.temp_item.p_list[-1] = [x, y]
                else:
                    self.temp_item.p_list[-2] = [x, y]
        
        def move_edit():
            if self.selected_id == '':
                return
            sid = self.selected_id
            if self.status in ['translate','clip']:
                self.item_dict[sid].edit_type = self.status
                self.item_dict[sid].poi1 = [x,y]
            elif self.status == 'rotate' or self.status == 'scale':
                if self.item_dict[sid].param_cnt == 1:
                    pass
                elif self.item_dict[sid].param_cnt == 2:
                    self.item_dict[sid].poi1 = [x,y]
                else:
                    self.item_dict[sid].edit_clear()
        
        if self.is_image_scaling == 0:
            move_draw()
            move_edit()
        self.updateScene([self.sceneRect()])
        #self.updateScene([self.temp_item.boundingRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        
        if self.is_image_scaling >0:
            self.is_image_scaling = 0
        
        def release_draw():
            if self.status not in g_draw_status:
                return
            if self.temp_id not in self.item_dict:
                self.item_dict[self.temp_id] = self.temp_item
                self.list_widget.addItem(self.status+" : "+self.temp_id)
                if self.status in ['line','ellipse']:
                    self.finish_draw()
                if self.status == 'polygon':
                    global g_draw_finish
                    g_draw_finish = 0
            else :
                if self.status == 'polygon'\
                and is_close(self.temp_item.p_list[0], self.temp_item.p_list[-1]):
                    # finish draw polygon
                    # [-1] and [0] refer to the same vertex
                    self.temp_item.p_list[-1] = self.temp_item.p_list[0][:]
                    self.finish_draw()
        
        def release_edit():
            if self.selected_id == '':
                return
            sid = self.selected_id
            if self.status in ['translate', 'clip']:
                self.item_dict[sid].edit_over = 1
            elif self.status == 'rotate' or self.status == 'scale':
                if self.item_dict[sid].param_cnt == 1:
                    pass
                elif self.item_dict[sid].param_cnt == 2:
                    self.item_dict[sid].edit_over = 1               
                else:
                    self.item_dict[sid].edit_clear()
        
        if self.is_image_scaling == 0:
            release_draw()
            release_edit()
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
        self.pixels = [] # 记录所有像素点
        # for edit
        self.edit_type = ''
        self.edit_algorithm = '' # used only for clip
        self.poi = [0,0] # [x,y] of move
        self.poi1 = [0,0]
        self.center = [0,0] # [x,y] of center
        self.edit_over = 0 # if the transformation operation over
        self.param_cnt = 0 # some operation needs 2 mouse_press
        
    def edit_clear(self):
        self.edit_type = ''
        self.edit_algorithm = ''
        self.center = [0,0]
        self.poi = [0,0]
        self.poi1 = [0,0]
        self.edit_over = 0
        self.param_cnt = 0
    
    def edit_finish(self, new_p_list):
        self.edit_clear()
        self.p_list = new_p_list
        
    def get_draw_pixels(self, p_list, algorithm):
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
        
    #gui会在鼠标事件自动调用paint重新绘制所有图元
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, \
              widget: Optional[QWidget] = ...) -> None:
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
            ret = angle1 - angle2
            return ret
        
        def thick_draw_point(painter, poi):
            """加粗绘制一个点,用于裁剪线段时高亮选中部分"""
            painter.drawPoint(*[poi[0]+1,poi[1]+1])
            painter.drawPoint(*[poi[0]+1,poi[1]-1])
            painter.drawPoint(*[poi[0]-1,poi[1]+1])
            painter.drawPoint(*[poi[0]-1,poi[1]-1])
            return
        
        if self.p_list == []:
            del g_canvas.item_dict[self.id]
            g_canvas.scene().removeItem(self)
            # print("Undefined Behavior: Empty line should be deleted")
            return
        
        # change p_list accoring to edit_type
        new_p_list = self.p_list
        if self.edit_type == 'translate':
            new_p_list = alg.translate(self.p_list, self.poi1[0]-self.poi[0], \
                                        self.poi1[1]-self.poi[1])
            if self.edit_over == 1:
                # finish
                self.edit_finish(new_p_list)
        elif self.edit_type == 'rotate':
            if self.item_type == 'ellipse':
                # g_window.statusBar().clearMessage()
                print("Can't rotate ellipse.")
                self.edit_finish(self.p_list)
            else:
                if self.param_cnt == 2:
                    # center and poi, poi1 all gotten
                    theta = angle([self.center, self.poi], [self.center, self.poi1])
                    new_p_list = alg.rotate(self.p_list, \
                                    self.center[0], self.center[1], theta)
                if self.edit_over == 1:
                    # clear
                    self.edit_finish(new_p_list)
        elif self.edit_type == 'scale':
            if self.param_cnt == 2:
                # 缩放倍数, 根据dx的比值确定
                if self.poi[0]-self.center[0] == 0:
                    s = 1
                else :
                    s = (self.poi1[0]-self.center[0])/(self.poi[0]-self.center[0])
                new_p_list = alg.scale(self.p_list, \
                                self.center[0], self.center[1], s)
            if self.edit_over == 1:
                self.edit_finish(new_p_list)
        elif self.edit_type == 'clip':
            if self.edit_over == 0:
                # draw the clip window
                painter.setPen(QColor(0,255,0))
                painter.drawRect( self.regionRect([self.poi,self.poi1]) )                 
                tmp_p_list = alg.clip(self.p_list, self.poi[0], self.poi[1],\
                                self.poi1[0], self.poi1[1], self.edit_algorithm)
                if tmp_p_list != []:
                    # highlight the line in clip window
                    tmp_pixels = self.get_draw_pixels(tmp_p_list,self.algorithm)
                    painter.setPen(QColor(0, 255, 0))
                    for p in tmp_pixels:
                        thick_draw_point(painter, p)
            elif self.edit_over == 1:
                # 得到裁剪后的端点
                new_p_list = alg.clip(self.p_list, self.poi[0], self.poi[1],\
                                self.poi1[0], self.poi1[1], self.edit_algorithm)
                self.edit_finish(new_p_list)
                if self.p_list == []:
                    # 线段被裁剪没了
                    self.item_type = 'delete'
                    self.pixels = []
                    g_list_widget.takeItem(g_list_widget.currentRow())
                    # g_canvas.clear_selection()
                    # del g_canvas.item_dict[self.id]
                    # g_canvas.scene().removeItem(self)
                    return
        
        item_pixels = []
        if new_p_list != []:
            if self.id == g_canvas.cur_id:
                item_pixels = self.get_draw_pixels(new_p_list, self.algorithm)
                self.pixels = item_pixels
            else:
                item_pixels = self.pixels
        else :
            print("Undefined Behavior: new_p_list shouldn't be []")
            # 线段被裁剪没了的话不该到这一步
            return 
        # draw
        painter.setPen(self.penColor)
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
        # 裁剪线段后可能出现p_list空的的图元
        if new_p_list == []:
            return [x,y,w,h]
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
        #self.list_widget.selectedIndexes
        global g_list_widget
        g_list_widget = self.list_widget

        # 使用QGraphicsView作为画布
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, g_width, g_height)
        self.canvas_widget = MyCanvas(self.scene, self)
        global g_canvas
        g_canvas = self.canvas_widget
        self.canvas_widget.setFixedSize(g_width+10, g_height+10)
        # self.canvas_widget.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        # self.setCentralWidget(self.canvas_widget)
        self.canvas_widget.main_window = self
        self.canvas_widget.list_widget = self.list_widget

        # 设置菜单栏
        menubar = self.menuBar()
        set_pen_act = menubar.addAction('设置画笔')
        reset_canvas_act = menubar.addAction('重置画布')
        save_canvas_act = menubar.addAction('保存画布')
        choose_item_act = menubar.addAction('选择图元')
        exit_act = menubar.addAction('退出')
        
        # 设置绘图工具栏
        line_dda_act = QAction('DDA线段', self)
        line_bresenham_act = QAction('Bresenham线段', self)
        polygon_dda_act = QAction('DDA多边形', self)
        polygon_bresenham_act = QAction('Bresenham多边形', self)
        ellipse_act = QAction('椭圆', self)
        curve_bezier_act = QAction('Bezier曲线', self)
        curve_b_spline_act = QAction('B-spline曲线', self)
        draw_toolbar = QToolBar('draw')
        self.addToolBar(Qt.LeftToolBarArea, draw_toolbar)
        draw_toolbar.addAction(line_dda_act)
        draw_toolbar.addAction(line_bresenham_act)
        draw_toolbar.addAction(polygon_dda_act)
        draw_toolbar.addAction(polygon_bresenham_act)
        draw_toolbar.addAction(ellipse_act)
        draw_toolbar.addAction(curve_bezier_act)
        draw_toolbar.addAction(curve_b_spline_act)
        
        # 设置编辑工具栏
        edit_toolbar = self.addToolBar('edit')
        translate_act = QAction('平移', self)
        rotate_act = QAction('旋转', self)
        scale_act = QAction('缩放', self)
        clip_cohen_sutherland_act = QAction('Cohen-Sutherland裁剪',self)
        clip_liang_barsky_act = QAction('Liang-Barsky裁剪',self)
        edit_toolbar.addAction(translate_act)
        edit_toolbar.addAction(rotate_act)
        edit_toolbar.addAction(scale_act)
        edit_toolbar.addAction(clip_cohen_sutherland_act)
        edit_toolbar.addAction(clip_liang_barsky_act)

        # 连接信号和槽函数
        # 画笔
        set_pen_act.triggered.connect(self.pen_color_change)
        # reset canvas
        reset_canvas_act.triggered.connect(self.reset_canvas)
        # 保存画布
        save_canvas_act.triggered.connect(self.save_canvas)
        # 选择图元
        choose_item_act.triggered.connect(self.choose_item)
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
        # 裁剪
        clip_cohen_sutherland_act.triggered.connect(self.clip_cohen_sutherland_action)
        clip_liang_barsky_act.triggered.connect(self.clip_liang_barsky_action)
        
        self.list_widget.currentTextChanged.connect(self.canvas_widget.selection_changed)

        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.hbox_layout.addWidget(self.list_widget, stretch=1)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲中')
        self.resize(g_width, g_height)
        # self.adjustSize()
        self.setWindowTitle('绘图工具')

    #clear and resize canvas
    def reset_canvas(self):
        self.statusBar().showMessage('重置画布')
        self.canvas_widget.clear_canvas()
        #resize
        text1,ok1 = QInputDialog.getText(self, '输入画布尺寸', 'x轴大小:')
        text2,ok2 = QInputDialog.getText(self, '输入画布尺寸', 'y轴大小:')
        if ok1!=1 or ok2!=1:
            return
        x = atoi(text1)
        y = atoi(text2)
        if x>1000 or x<100 or y>1000 or y<100:
            print("x and y must in [100,1000], please input again.")
            return
        self.canvas_widget.resize(x+10, y+10)
        self.scene.setSceneRect(0, 0, x, y)
        self.resize(x, y)
        global g_width, g_height
        g_width= x
        g_height = y
    
    #保存画布
    def save_canvas(self):
        self.statusBar().showMessage('保存画布')
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
        # 设置背景白色
        pixmap.fill(QColor(255,255,255))
        # painter
        painter = QPainter(pixmap)
        # Render scene to the pixmap
        self.scene.render(painter, rect, rect)
        painter.end()
        # save bmp file
        pixmap.save(fname[0])    
        
    #从QColorDialog中选取颜色,并设置为pen的颜色
    def pen_color_change(self):
        self.statusBar().showMessage('设置画笔颜色')
        self.canvas_widget.clear_selection() 
        # 设置画笔颜色也会令前一个没完成图形完成
        self.canvas_widget.check_finish()
        global g_penColor
        color = QColorDialog.getColor()
        g_penColor = color

    def choose_item(self):
        self.canvas_widget.choose_item()
        
    def get_id(self):
        _id = str(self.item_cnt)
        #self.item_cnt += 1
        return _id
    
    def id_inc(self):
        self.item_cnt += 1
    
    def reset_id(self):
        self.item_cnt = 0
    
    #DDA绘制线段    
    def line_dda_action(self):
        self.canvas_widget.start_draw('line', 'DDA')
        self.statusBar().showMessage('DDA算法绘制线段')
        self.canvas_widget.clear_selection() 
        
    #Bresenham绘制线段
    def line_bresenham_action(self):
        self.canvas_widget.start_draw('line','Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制线段')
        self.canvas_widget.clear_selection()
    
    def polygon_bresenham_action(self):
        self.canvas_widget.start_draw('polygon','Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制多边形')
        self.canvas_widget.clear_selection()
        
    def polygon_dda_action(self):
        self.canvas_widget.start_draw('polygon','DDA')
        self.statusBar().showMessage('DDA算法绘制多边形')
        self.canvas_widget.clear_selection()
    
    def ellipse_action(self):
        self.canvas_widget.start_draw('ellipse','default')
        self.statusBar().showMessage('绘制椭圆')
        self.canvas_widget.clear_selection()      
        
    def curve_bezier_action(self):
        self.canvas_widget.start_draw('curve','Bezier')
        self.statusBar().showMessage('Bezier算法绘制曲线')
        self.canvas_widget.clear_selection()
        
    def curve_b_spline_action(self):
        self.canvas_widget.start_draw('curve','B-spline')
        self.statusBar().showMessage('B_spline算法绘制曲线')
        self.canvas_widget.clear_selection() 
    
    # 平移
    def translate_action(self):
        self.canvas_widget.start_edit('translate','default')
        self.statusBar().showMessage('平移选中图元')
        
    # 旋转
    def rotate_action(self):
        self.canvas_widget.start_edit('rotate','default')
        self.statusBar().showMessage('旋转选中图元')
    
    # 缩放
    def scale_action(self):
        self.canvas_widget.start_edit('scale','default')
        self.statusBar().showMessage('缩放选中图元')
    
    # 裁剪线段
    def clip_cohen_sutherland_action(self):
        self.canvas_widget.start_edit('clip','Cohen-Sutherland')
        self.statusBar().clearMessage()
        self.statusBar().showMessage('Cohen-Sutherland算法裁剪线段')
        
    def clip_liang_barsky_action(self):
        self.canvas_widget.start_edit('clip','Liang-Barsky')
        self.statusBar().clearMessage()
        self.statusBar().showMessage('Liang-Barsky算法裁剪线段')
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # print(dir(QGraphicsScene))
    # help(QListWidget.selectedIndexes)
    # print(dir(QGraphicsView))
    mw = MainWindow()
    global g_window
    g_window = mw
    mw.show()
    app.exec_()
    del app
    #sys.exit(0)