#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import cg_algorithms as alg
import numpy as np
from PIL import Image


if __name__ == '__main__':
    input_file = sys.argv[1] #command file
    output_dir = sys.argv[2] #dir which stored bmp picture
    os.makedirs(output_dir, exist_ok=True)

    item_dict = {} #describe how and where to draw
    pen_color = np.zeros(3, np.uint8)
    width = 0
    height = 0

    with open(input_file, 'r') as fp:
        line = fp.readline()
        while line:
            line = line.strip().split(' ')
            #reset Canvas and clear item_dict
            if line[0] == 'resetCanvas':
                item_dict = {} #清空画布
                width = int(line[1])
                height = int(line[2])
            #draw the Canvas by item_dict, and save as .bmp picture
            elif line[0] == 'saveCanvas':
                save_name = line[1]
                #three dimension
                canvas = np.zeros([height, width, 3], np.uint8)
                #red 255, green 255, blue 255
                canvas.fill(255)
                for item_type, p_list, algorithm, color in item_dict.values():
                    pixels = []
                    if item_type == 'line':
                        pixels = alg.draw_line(p_list, algorithm)
                    elif item_type == 'polygon':
                        pixels = alg.draw_polygon(p_list, algorithm)
                    elif item_type == 'ellipse':
                        pixels = alg.draw_ellipse(p_list)
                    elif item_type == 'curve':
                        pixels = alg.draw_curve(p_list, algorithm)
                    for x, y in pixels:
                        canvas[height-1-y, x] = color
                #save as bmp
                Image.fromarray(canvas).save(os.path.join(output_dir, save_name + '.bmp'), 'bmp')
            #bleow deals item_dict
            elif line[0] == 'setColor':
                pen_color[0] = int(line[1])
                pen_color[1] = int(line[2])
                pen_color[2] = int(line[3])
            elif line[0] == 'drawLine':
                item_id = line[1]
                x0 = int(line[2])
                y0 = int(line[3])
                x1 = int(line[4])
                y1 = int(line[5])
                algorithm = line[-1]
                item_dict[item_id] = ['line', [[x0, y0], [x1, y1]], algorithm, np.array(pen_color)]
            elif line[0] == 'drawPolygon':
                item_id = line[1]
                #number of coordinates
                coor_num = (int)((len(line) - 3)/2)
                pixels = []
                for i in range(0, coor_num):
                    x = int(line[2+2*i])
                    y = int(line[3+2*i])
                    pixels.append([x,y])
                algorithm = line[-1]
                item_dict[item_id] = ['polygon', pixels, algorithm, np.array(pen_color)]
            elif line[0] == 'drawEllipse':
                item_id = line[1]
                x0 = int(line[2])
                y0 = int(line[3])
                x1 = int(line[4])
                y1 = int(line[5])   
                algorithm = 'default'
                item_dict[item_id] = ['ellipse', [[x0, y0], [x1, y1]], algorithm, np.array(pen_color)]
            elif line[0] == 'drawCurve':
                item_id = line[1]
                #number of coordinates
                coor_num = (int)((len(line) - 3)/2)
                pixels = []
                for i in range(0, coor_num):
                    x = int(line[2+2*i])
                    y = int(line[3+2*i])
                    pixels.append([x,y])
                algorithm = line[-1]
                item_dict[item_id] = ['curve', pixels, algorithm, np.array(pen_color)]   
            elif line[0] == 'translate':
                item_id = line[1]
                dx = int(line[2])
                dy = int(line[3])
                if item_id in item_dict:
                    new_p_list = alg.translate(item_dict[item_id][1], dx, dy)
                    item_dict[item_id][1] = new_p_list
            elif line[0] == 'rotate':
                item_id = line[1]
                xr = int(line[2])
                yr = int(line[3])
                theta = int(line[4])
                if item_id in item_dict:
                    # can't rotate ellipse
                    if item_dict[item_id][0] != 'ellipse':
                        new_p_list = alg.rotate(item_dict[item_id][1], xr, yr, theta)
                        item_dict[item_id][1] = new_p_list
            ...

            line = fp.readline()

