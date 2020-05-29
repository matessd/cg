#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 本文件只允许依赖math库
import math
import numpy as np

def Sign(x):
    if x<0:
        return -1
    elif x==0:
        return 0
    else :
        return 1

def draw_line(p_list, algorithm):
    """绘制线段

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'，此处的'Naive'仅作为示例，测试时不会出现
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if algorithm == 'Naive':
        if x0 == x1:
            for y in range(y0, y1 + 1):
                result.append((x0, y))
        else:
            if x0 > x1:
                x0, y0, x1, y1 = x1, y1, x0, y0
            k = (y1 - y0) / (x1 - x0)
            for x in range(x0, x1 + 1):
                result.append((x, int(y0 + k * (x - x0))))
    elif algorithm == 'DDA':
        length = 0
        if abs(x0-x1) >= abs(y0-y1):
            length = abs(x0-x1)
        else:
            length = abs(y0-y1)
        x = x0+0.5; y = y0+0.5
        #avoid dividing by 0, gui may appear this situation
        if length==0:
            result.append((x0,y0))
            return result
        dx = (x1-x0)/length
        dy = (y1-y0)/length
        for i in range(1, length+1):
            #这里i是从1开始还是从0开始好？?
            result.append((math.floor(x), math.floor(y)))
            x += dx; y += dy
    elif algorithm == 'Bresenham':
        x = x0
        y = y0
        dx = abs(x1-x0)
        dy = abs(y1-y0)
        s1 = Sign(x1-x0)
        s2 = Sign(y1-y0)
        Interchange = 0
        if dy>dx:
            temp = dx
            dx = dy
            dy = temp
            Interchange = 1
        else :
            Interchange = 0
        e_ = 2*dy - dx
        for i in range(1, dx+1):
            result.append((x,y))
            #这里的while能否去掉?
            while(e_>0):
                if(Interchange==1):
                    x = x + s1
                else :
                    y = y + s2
                e_ = e_ - 2*dx
            if(Interchange==1):
                y = y + s2
            else :
                x = x + s1
            e_ = e_ + 2*dy
    return result


def draw_polygon(p_list, algorithm):
    """绘制多边形

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 多边形的顶点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    length = len(p_list)
    for i in range(length):
        line = draw_line([p_list[i], p_list[(i+1)%length]], algorithm)
        result += line
    return result


def set_ellipse_pixels(center, coord):
    """将[x,y]对称的点加入result
    :param center: (int) 椭圆中心的坐标
    :return: (list of list of int) [x,y]及其对称点
    """
    result = []
    xc,yc = center
    x,y = coord
    result.append([xc+x,yc+y])
    if x != 0:
        result.append([xc-x,yc+y])
    if y != 0:
        result.append([xc+x,yc-y])
    if x !=0 and y!=0:
        result.append([xc-x,yc-y])
    return result

def draw_ellipse(p_list):
    """绘制椭圆（采用中点圆生成算法）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 椭圆的矩形包围框左上角和右下角顶点坐标
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    # compute basic param
    xc = (p_list[0][0]+p_list[1][0])//2
    yc = (p_list[0][1]+p_list[1][1])//2
    rx = abs(p_list[0][0]-p_list[1][0])//2
    ry = abs(p_list[0][1]-p_list[1][1])//2
    rx2 = rx**2
    ry2 = ry**2
    # init before loop1
    x,y = 0,ry
    # p1_k, k=1
    p1 = ry2 - rx2*ry + rx2/4
    # region 1
    while ry2*x < rx2*y:
        result.extend( set_ellipse_pixels([xc,yc],[x,y]) )
        if p1<0:
            p1 = p1 + 2*ry2*(x+1) + ry2
        else :
            p1 = p1 + 2*ry2*(x+1) - 2*rx2*(y-1) + ry2
            y = y-1
        x = x+1
    # region 2
    p2 = ry2*(x+1/2)**2 + rx2*(y-1)**2 - rx2*ry2
    while y>=0:
        result.extend( set_ellipse_pixels([xc,yc],[x,y]) )
        if p2>0:
            p2 = p2 - 2*rx2*(y-1) + rx2
        else :
            p2 = p2 - 2*rx2*(y-1) + 2*ry2*(x+1) + rx2
            x = x+1
        y = y-1
    return result

def draw_curve(p_list, algorithm):
    """绘制曲线

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 曲线的控制点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'Bezier'和'B-spline'（三次均匀B样条曲线，曲线不必经过首末控制点）
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    if algorithm == 'Bezier':
        """ 注释掉的是直接计算步长的绘制方法,会很卡
        # P0
        result1 = []
        result1.append(p_list[0])
        le = len(p_list)
        
        # compute interval 
        distance = 1
        for i in range(le-1):
            xd = abs(p_list[i][0] - p_list[i+1][0])
            yd = abs(p_list[i][1] - p_list[i+1][1])
            distance = distance + max(xd, yd)
        interval = 0.001
        #print(0.05/le)
        #print(interval)
        
        t = interval
        while t<=1:
            posList = p_list[:]
            le_dec = le
            for i in range(le-1):
                j = 0
                while j<le_dec-1:
                    xt = (1-t)*posList[j][0] + t*posList[j+1][0]
                    yt = (1-t)*posList[j][1] + t*posList[j+1][1]
                    posList[j] = [xt,yt]
                    j = j+1
                le_dec = le_dec - 1 
            x = int(posList[0][0])
            y = int(posList[0][1])
            if result1[-1] != [x,y]:
                result1.append([x,y])
            t += interval
        # because t is float, t=1 may not appear
        if result1[-1] != p_list[-1]:
            result1.append(p_list[-1])
        for i in range(len(result1)-1):
            pixels = draw_line(result1[i:i+2], 'Bresenham')
            result.extend(pixels)
        """
        def poi_to_line_dis(poi, line):
            """计算点到直线的距离, 用于bezier曲线二分逼近时判断误差
            """
            if line[0][0]==line[1][0] and line[0][1]==line[1][1]:
                return math.sqrt( (poi[0]-line[0][0])**2 + (poi[1]-line[0][1])**2 )
            a = line[1][1] - line[0][1]
            b = line[0][0] - line[1][0]
            c = (line[1][0] - line[0][0])*line[0][1] - (line[1][1] - line[0][1])*line[0][0]
            return abs((a*poi[0] + b*poi[1] + c)/math.sqrt(a*a + b*b))
        
        def Bezier_curve(p_list):
            """为了确保精度,额外弄出来的递归函数
            通过不断二分逼近曲线,返回的是浮点数形式的坐标
            """
            n = len(p_list) - 1
            n_dec = n
            Qcurve = [p_list[0]]
            Rcurve = [p_list[-1]]
            posList = p_list[:]
            # 平分曲线, 然后求出两段曲线的控制点
            for i in range(1, n+1):
                for j in range(n_dec):
                    xt = 0.5*posList[j][0] + 0.5*posList[j+1][0]
                    yt = 0.5*posList[j][1] + 0.5*posList[j+1][1]
                    posList[j] = [xt,yt]
                    if j == 0:
                        Qcurve.append([xt, yt])
                    if (i+j) == n:
                        Rcurve.append([xt, yt])
                n_dec = n_dec - 1
            # R curve gen vertex in opposite direction
            Rcurve.reverse()
            result = []
            # 得到两段曲线的像素点
            if max([poi_to_line_dis(poi, [Qcurve[0],Qcurve[-1]]) for poi in Qcurve]) <= 0.01:
                result.extend(Qcurve)
            else:
                result.extend(Bezier_curve(Qcurve))
            if max([poi_to_line_dis(poi, [Rcurve[0],Rcurve[-1]]) for poi in Rcurve]) <= 0.01:
                result.extend(Rcurve)
            else:
                result.extend(Bezier_curve(Rcurve))
            return result

        def plot(result):
            result_t = Bezier_curve(p_list)
            vertex = []
            # 
            for poi in result_t:
                x = int(poi[0])
                y = int(poi[1])
                vertex.append([x, y])
            le = len(vertex)
            #return vertex
            for i in range(le-1):
                pixels = draw_line(vertex[i:i+2], 'Bresenham')
                result.extend(pixels)
        # call plot
        plot(result)
    elif algorithm == 'B-spline':
        k = 4 # 阶数
        n = len(p_list)-1 # 顶点的个数-1
        T = np.linspace(1,10,n+k+1) # T 范围1到10，均匀B样条曲线
        # if n >= k-1:
        #     T = [1]*k+(np.linspace(2,9,n-k+1)).tolist()+[10]*k # 准均匀样条
        x,y = [],[]
        # 递推公式
        # def de_Boor(r,t,i):
        #     if r == 0:
        #         return [args[0][i],args[1][i]]
        #     else:
        #         return ((t-T[i])/(T[i+k-r]-T[i]))*de_Boor(r-1,t,i)\
        #               +((T[i+k-r]-t)/(T[i+k-r]-T[i]))*de_Boor(r-1,t,i-1)
        def de_Boor_x(r,t,i):
            if r == 0:
                return p_list[i][0]
            else:
                if t-T[i] == 0 and T[i+k-r]- T[i]!= 0:
                    return ((T[i+k-r]-t)/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i-1)
                elif T[i+k-r]-t == 0 and T[i+k-r]-T[i] != 0:
                    return ((t-T[i])/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i)
                elif t-T[i] == 0 and T[i+k-r]-t == 0:
                    return 0
                return ((t-T[i])/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i)\
                    +((T[i+k-r]-t)/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i-1)
        def de_Boor_y(r,t,i):
            if r == 0:
                return p_list[i][1]
            else:
                if t-T[i] == 0 and T[i+k-r]- T[i]!= 0:
                    return ((T[i+k-r]-t)/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i-1)
                elif T[i+k-r]-t == 0 and T[i+k-r]-T[i] != 0:
                    return ((t-T[i])/(T[i+k-r]-T[i]))*de_Boor_x(r-1,t,i)
                elif t-T[i] == 0 and T[i+k-r]-t == 0:
                    return 0
                return ((t-T[i])/(T[i+k-r]-T[i]))*de_Boor_y(r-1,t,i)\
                    +((T[i+k-r]-t)/(T[i+k-r]-T[i]))*de_Boor_y(r-1,t,i-1)
        def plot(posList):
            for j in range(k-1,n+1):
                for t in np.linspace(T[j],T[j+1]):
                    posList.append([de_Boor_x(k-1,t,j),de_Boor_y(k-1,t,j)])
        if n >= k-1:
            plot(result)
    return result


def translate(p_list, dx, dy):
    """平移变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param dx: (int) 水平方向平移量
    :param dy: (int) 垂直方向平移量
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    pass


def rotate(p_list, x, y, r):
    """旋转变换（除椭圆外）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 旋转中心x坐标
    :param y: (int) 旋转中心y坐标
    :param r: (int) 顺时针旋转角度（°）
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    pass


def scale(p_list, x, y, s):
    """缩放变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 缩放中心x坐标
    :param y: (int) 缩放中心y坐标
    :param s: (float) 缩放倍数
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    pass


def clip(p_list, x_min, y_min, x_max, y_max, algorithm):
    """线段裁剪

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :param algorithm: (string) 使用的裁剪算法，包括'Cohen-Sutherland'和'Liang-Barsky'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1]]) 裁剪后线段的起点和终点坐标
    """
    pass
