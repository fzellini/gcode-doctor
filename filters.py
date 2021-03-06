import math

import pygcode
from commons import gCodeBlocks


def feed_rate_multiply_filter(par):
    """
    apply proportional linear mapping correction to feed:

    :param par: multiply factor, if string parse
    :return:
    """

    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("feed_rate_multiply_filter: {}".format(value))

    for line in block_to_filter.lines:
        if line.contains(pygcode.gcodes.GCodeFeedRate):
            gcode_feed_rate = line.get(pygcode.gcodes.GCodeFeedRate)
            gcode_feed_rate.word.value *= value


def feed_rate_max_filter(par):
    """

    :param par:
    :return:
    """
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("feed_rate_max_filter: {}".format(value))

    for line in block_to_filter.lines:
        if line.contains(pygcode.gcodes.GCodeFeedRate):
            gcode_feed_rate = line.get(pygcode.gcodes.GCodeFeedRate)
            gcode_feed_rate.word.value = gcode_feed_rate.word.value / block_to_filter.fmax * value




def spindle_speed_multiply_filter(par):
    """
    apply proportional linear mapping correction to spindle:

    :param par: multiply factor, if string parse
    :return:
    """

    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("spindle_speed_multiply_filter: {}".format(value))

    for line in block_to_filter.lines:
        if line.contains(pygcode.gcodes.GCodeSpindleSpeed):
            gcode_spindle_speed = line.get(pygcode.gcodes.GCodeSpindleSpeed)
            gcode_spindle_speed.word.value *= value


def spindle_speed_max_filter(par):
    """

    :param par: max value of spindle
    :return:
    """

    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("spindle_speed_max_filter: {}".format(value))

    for line in block_to_filter.lines:
        if line.contains(pygcode.gcodes.GCodeSpindleSpeed):
            gcode_spindle_speed = line.get(pygcode.gcodes.GCodeSpindleSpeed)
            gcode_spindle_speed.word.value = gcode_spindle_speed.word.value/ block_to_filter.smax * value


def startx_filter(par):
    """
    modify gcodes in order to start at x=par
    :param par:
    :return:
    """
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("startx_filter: {}".format(value))

    if block_to_filter.xmin == value:
        print("startx_filter: already start at {}".format(value))

    for line in block_to_filter.lines:
        for gcode in line.block.gcodes:
            try:
                if gcode.X is not None:
                    gcode.X = gcode.X - block_to_filter.xmin + value
            except AttributeError:
                pass


def mindistance_filter(par):
    """
    modify gcodes in order that 2 consecutive 01 distance is not less than parameter
    :param par:
    :return:
    """
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("mindistance_filter: {}".format(value))

    removed_codes = 0
    total_codes = 0
    g01blocks = block_to_filter.g01blocks
    ng01 = len(g01blocks)

    for g01block in g01blocks:
        if g01block.size() < 4:
            continue
        lastX = None
        lastY = None

        linecount = len(g01block.lines)
        first = True
        for j, line in enumerate(g01block.lines):
            gcode_to_remove = []
            for i, gcode in enumerate(line.block.gcodes):
                try:
                    if gcode.X is not None:
                        px = gcode.X
                    if gcode.Y is not None:
                        py = gcode.Y

                    distance = None
                    if not first and px is not None and py is not None:
                        dx = px-lastX
                        dy = py-lastY

                        distance = math.sqrt(dx*dx+dy*dy)

                    total_codes += 1
                    if (distance is None) or (distance > value):
                        # emetto
                        lastX = px
                        lastY = py
                    else:
                        # remove this code
                        #print("remove {} from line {}".format(gcode, line))
                        gcode_to_remove.append(gcode)

                    first = False

                except AttributeError:
                    pass
            if len(gcode_to_remove) and line.islast is not None and not line.islast:
                removed_codes += len(gcode_to_remove)
                new_gcode_block = []
                for g1 in line.block.gcodes:
                    if g1 not in gcode_to_remove:
                        new_gcode_block.append(g1)
                line.block.gcodes = new_gcode_block

    print ("Removed {} out of {}".format(removed_codes, total_codes))


def starty_filter(par):
    """
    modify gcodes in order to start at x=par
    :param par:
    :return:
    """
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        value = float(par)
    except ValueError:
        value = eval(par)

    print("starty_filter: {}".format(value))

    if block_to_filter.xmin == value:
        print("starty_filter: already start at {}".format(value))

    for line in block_to_filter.lines:
        for gcode in line.block.gcodes:
            try:
                if gcode.Y is not None:
                    gcode.Y = gcode.Y - block_to_filter.ymin + value
            except AttributeError:
                pass


def resize_filter(par):
    """
    include gcode in bounding box, starting at 0,0
    :param par: 100x, x200, 200x200
    :return:
    """
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    try:
        xb, yb = par.split('x')
        xb = float(xb) if len(xb) else None
        yb = float(yb) if len(yb) else None

    except ValueError:
        print("bad resize filter format: valid is <xmax>x<ymax>, e.g. 100x, 100x100, 200x")
        return

    print("resize_filter: {}x{}".format(xb, yb))

    # determine xscale and yscale
    xsize = block_to_filter.xmax-block_to_filter.xmin
    ysize = block_to_filter.ymax-block_to_filter.ymin
    # print("block_to_filter {}".format(block_to_filter))

    factor = 1
    if yb is None:
        # scale only x
        factor = xb/xsize
    if xb is None:
        # scale only x
        factor = yb/ysize
    if xb is not None and yb is not None:
        xf = xb / xsize
        yf = yb / ysize
        factor = xf if xf < yf else yf

    print("resize_filter: factor {}".format(factor))
    for line in block_to_filter.lines:
        for gcode in line.block.gcodes:
            try:
                if gcode.X is not None:
                    gcode.X = gcode.X - block_to_filter.xmin
                    gcode.X *= factor
                if gcode.Y is not None:
                    gcode.Y = gcode.Y - block_to_filter.ymin
                    gcode.Y *= factor
            except AttributeError:
                pass


def inside_first_filter():
    """
    organize gcode groups in order to prioritize inner cuts
    :return:
    """
    print("inside_first_filter")
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    g01blocks = block_to_filter.g01blocks
    ng01 = len(g01blocks)

    while True:
        swp = False
        for i in range(ng01-1):
            for j in range(i+1, ng01):
                if g01blocks[i].contains(g01blocks[j]):
                    g01blocks[i], g01blocks[j] = g01blocks[j], g01blocks[i]
                    swp = True

        if not swp:
            break

    # rearrange original lines
    block_to_filter.lines = []
    for g01block in block_to_filter.g01blocks:
        for line in g01block.lines:
            block_to_filter.lines.append(line)


def optimize_path_filter():
    """
    organize gcode groups trying to minimize path
    :return:
    """
    print("optimize_path_filter...")
    if len(gCodeBlocks) == 0:
        print("no gcode loaded: cannot apply filter")
        return
    block_to_filter = gCodeBlocks[-1]

    g01blocks = block_to_filter.g01blocks
    ng01 = len(g01blocks)

    print(block_to_filter)

    for ri in range(ng01-1):
        if ri % 10 == 0:
            print(ri, end='\r')
        next_block_index = ri + 1
        idx_shortest = g01blocks[ri].shortestPathToStart2(g01blocks, next_block_index)
        if idx_shortest is not None:
            if idx_shortest != next_block_index:
                g01blocks[next_block_index], g01blocks[idx_shortest] = \
                    g01blocks[idx_shortest], g01blocks[next_block_index]

    print()
    # rearrange original lines
    block_to_filter.lines = []
    for g01block in block_to_filter.g01blocks:
        for line in g01block.lines:
            block_to_filter.lines.append(line)

    print("optimize_path_filter done.")