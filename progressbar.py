#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
def process_bar(percent, width = 50):
    use_num = int(percent * width)
    space_num = int(width - use_num)
    percent = percent * 100
    print('\rReceiving[%s%s]%d%%' % (use_num*'#', space_num*' ', percent), end = '')

# print('\rReceiving[%s%s]%d%%' % ((int(precent * width))*'#', (int(width - int(precent * width)))*' ', precent * 100), flush = True, end = '')