# -*- coding: utf-8 -*-
import argparse
import math
import sys
import pygcode

from filters import feed_rate_multiply_filter, mindistance_filter, optimize_path_filter
from filters import feed_rate_max_filter
from filters import spindle_speed_multiply_filter
from filters import spindle_speed_max_filter
from filters import startx_filter
from filters import starty_filter
from filters import inside_first_filter
from filters import resize_filter

from commons import gCodeBlocks


class GCodeLine(pygcode.Line):
    def __init__(self, s):
        self.islast = None
        super().__init__(s)

    def contains(self, class_type):
        for gcode in self.block.gcodes:
            if type(gcode) == class_type:
                return True
        return False

    def get(self, class_type):
        for gcode in self.block.gcodes:
            if type(gcode) == class_type:
                return gcode
        return None


class G01Block:
    """
    a block of gcodes consisting of a G00 followed by G01
    useful to do inside_first cut filter
    """
    def __init__(self):
        self.lines = []
        self.xmin = sys.float_info.max
        self.xmax = sys.float_info.min
        self.ymin = sys.float_info.max
        self.ymax = sys.float_info.min
        self.startx = None
        self.starty = None
        self.endx = None
        self.endy = None
        self.last01line = None
        self.first = True

    def appendLine(self, line):

        gcode = None

        if line.contains(pygcode.gcodes.GCodeRapidMove):
            gcode = line.get(pygcode.gcodes.GCodeRapidMove)
        if line.contains(pygcode.gcodes.GCodeLinearMove):
            gcode = line.get(pygcode.gcodes.GCodeLinearMove)

        if gcode is not None:
            line.islast = True
            if self.last01line is not None:
                self.last01line.islast = False
            self.last01line = line
            if gcode.X is not None:
                self.xmin = min(gcode.X, self.xmin)
                self.xmax = max(gcode.X, self.xmax)

            if gcode.Y is not None:
                self.ymin = min(gcode.Y, self.ymin)
                self.ymax = max(gcode.Y, self.ymax)

            if (gcode.X is not None) and (gcode.Y is not None):
                if self.first:
                    self.startx = gcode.X
                    self.starty = gcode.Y
                    self.first = False
                else:
                    self.endx = gcode.X
                    self.endy = gcode.Y

        self.lines.append(line)

    def size(self):
        return len(self.lines)

    def isvalid(self):
        if len(self.lines) == 0:
            return False
        first = self.lines[0]
        for last in self.lines[::-1]:
            if len(last.block.gcodes):
                break
        if not first.contains(pygcode.gcodes.GCodeRapidMove):
            return False
        if not (last.contains(pygcode.gcodes.GCodeStopSpindle) or last.contains(pygcode.gcodes.GCodeLinearMove)):
            return False

        return True

    def distanceToStart(self, other_block):
        if (not self.isvalid()) or (not other_block.isvalid()):
            return None
        dx = self.endx-other_block.startx
        dy = self.endy-other_block.endy
        distance = math.sqrt(dx*dx+dy*dy)
        return distance

    def shortestPathToStart(self, block_array):
        """
        return the index of the shortest
        :param block_array:
        :return:
        """
        d = sys.float_info.max
        min_i = None
        for i, block in enumerate(block_array):
            dn = self.distanceToStart(block)
            if dn < d:
                d = dn
                min_i = i
        return min_i

    def shortestPathToStart2(self, block_array, start_index):
        """
        return the index of the shortest
        :param block_array:
        :param start_index:
        :return:
        """
        d = sys.float_info.max
        min_i = None
        ln = len(block_array)
        i = start_index
        while i < ln:
            dn = self.distanceToStart(block_array[i])

            if dn is not None and dn < d:
                d = dn
                min_i = i
            i += 1
        return min_i

    def contains(self, other_block):
        """
        this block contains other_block ?
        :param other_block:
        :return: True if this block contains the other block
        """
        if self.isvalid() and other_block.isvalid():
            if self.xmin < other_block.xmin and self.xmax > other_block.xmax and \
                    self.ymin < other_block.ymin and self.ymax > other_block.ymax:
                return True
        return False

    def __repr__(self):
        s = "block of {} lines of code, isvalid {}".format(len(self.lines), self.isvalid())
        if self.isvalid():
            s = "{}, x from {} to {}, y from {} to {}".format(s, self.xmin, self.xmax, self.ymin, self.ymax)
        return s


class GCodeBlock:
    """
    gcode block, red from file or generated by function
    """
    @staticmethod
    def read_from_file(filename):
        g = GCodeBlock("file: {}".format(filename))
        lma = G01Block()
        with open(filename, 'r') as fh:
            for line_text in fh.readlines():
                line = GCodeLine(line_text)
                g.appendLine(line)
                if not(line.contains(pygcode.gcodes.GCodeLinearMove)  or len(line.gcodes)==0):
                #if line.contains(pygcode.gcodes.GCodeRapidMove):
                    if lma.size() > 0:
                        g.g01blocks.append(lma)
                        lma = G01Block()

                lma.appendLine(line)

        if lma.size() > 0:
            g.g01blocks.append(lma)
        print (g)
        return g

    def __init__(self, desc):
        self.desc = desc
        self.lines = []
        self.g01blocks = []
        self.xmin = sys.float_info.max
        self.xmax = sys.float_info.min
        self.ymin = sys.float_info.max
        self.ymax = sys.float_info.min
        self.smin = 0
        self.smax = 0
        self.fmin = 0
        self.fmax = 0

    def appendLine(self, line):
        gcode = None
        gcode_spindle_speed = None
        gcode_feed_rate = None

        if line.contains(pygcode.gcodes.GCodeRapidMove):
            gcode = line.get(pygcode.gcodes.GCodeRapidMove)
        if line.contains(pygcode.gcodes.GCodeLinearMove):
            gcode = line.get(pygcode.gcodes.GCodeLinearMove)

        if line.contains(pygcode.gcodes.GCodeSpindleSpeed):
            gcode_spindle_speed = line.get(pygcode.gcodes.GCodeSpindleSpeed)
        if line.contains(pygcode.gcodes.GCodeFeedRate):
            gcode_feed_rate = line.get(pygcode.gcodes.GCodeFeedRate)

        if gcode is not None:
            if gcode.X is not None:
                self.xmin = min(gcode.X, self.xmin)
                self.xmax = max(gcode.X, self.xmax)

            if gcode.Y is not None:
                self.ymin = min(gcode.Y, self.ymin)
                self.ymax = max(gcode.Y, self.ymax)

        if gcode_spindle_speed is not None:
            self.smin = min(gcode_spindle_speed.word.value, self.smin)
            self.smax = max(gcode_spindle_speed.word.value, self.smax)
        if gcode_feed_rate is not None:
            self.fmin = min(gcode_feed_rate.word.value, self.fmin)
            self.fmax = max(gcode_feed_rate.word.value, self.fmax)

        self.lines.append(line)

    def __repr__(self):
        s = "{}, {} lines of code, g01blocks: {}".format(self.desc, len(self.lines), len(self.g01blocks))
        if self.xmin != sys.float_info.max:
            s = "{}, X from {} to {}".format(s, self.xmin, self.xmax)
        if self.ymin != sys.float_info.max:
            s = "{}, Y from {} to {}".format(s, self.ymin, self.ymax)
        if self.smin != sys.float_info.max:
            s = "{}, S from {} to {}".format(s, self.smin, self.smax)
        if self.fmin != sys.float_info.max:
            s = "{}, F from {} to {}".format(s, self.fmin, self.fmax)

        return s


def write_gcode(filename):

    print("write_gcode to file {}".format(filename))

    with open(filename, "w") as h:
        for block in gCodeBlocks:
            h.write("; <gcodedoctor>\n")
            h.write("; {}\n".format(block))
            h.write("; </gcodedoctor>\n")
            for line in block.lines:
                if len(line.block.gcodes) or line.comment is not None:
                    h.write("{}\n".format(line))

#            for g01block in block.g01blocks:
#                h.write("; {}\n".format(g01block))
#                for line in g01block.lines:
#                    h.write("{}\n".format(line))


def read_gcode(filename):
    """
    Read gcode into new buffer
    :param filename:
    :return:
    """
    print("read_gcode from file {}".format(filename))
    block = GCodeBlock.read_from_file(filename)
    gCodeBlocks.append(block)


class GcodeReadAction(argparse.Action):

    def __call__(self, _parser, namespace, values, option_string=None):
        read_gcode(values)


class GcodeWriteAction(argparse.Action):

    def __call__(self, _parser, namespace, values, option_string=None):
        write_gcode(values)


class GcodeInsideFirstFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        inside_first_filter()


class GcodeFeedRateFilterMultiplyAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        feed_rate_multiply_filter(values)


class GcodeFeedRateMaxFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        feed_rate_max_filter(values)


class GcodeSpindleSpeedFilterMultiplyAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        spindle_speed_multiply_filter(values)


class GcodeSpindleSpeedMaxAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        spindle_speed_max_filter(values)


class GcodeStartXFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        startx_filter(values)


class GcodeStartYFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        starty_filter(values)


class GcodeResizeFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        resize_filter(values)


class GcodeMinDistanceFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        mindistance_filter(values)


class GcodeOptimizePathFilterAction(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None):
        optimize_path_filter()



if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='gcode doctor', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--readgcode", action=GcodeReadAction)
    parser.add_argument("--writegcode", action=GcodeWriteAction)
    parser.add_argument("--filter-inside-first", nargs=0, action=GcodeInsideFirstFilterAction)
    parser.add_argument("--filter-optimize-path", nargs=0, action=GcodeOptimizePathFilterAction)
    parser.add_argument("--filter-start-x", action=GcodeStartXFilterAction)
    parser.add_argument("--filter-start-y", action=GcodeStartYFilterAction)
    parser.add_argument("--filter-resize", action=GcodeResizeFilterAction)
    parser.add_argument("--filter-min-distance", action=GcodeMinDistanceFilterAction)
    parser.add_argument("--filter-feed-rate-multiply", action=GcodeFeedRateFilterMultiplyAction)
    parser.add_argument("--filter-feed-rate-max", action=GcodeFeedRateMaxFilterAction)
    parser.add_argument("--filter-spindle-speed-multiply", action=GcodeSpindleSpeedFilterMultiplyAction)
    parser.add_argument("--filter-spindle-speed-max", action=GcodeSpindleSpeedMaxAction)

    args = parser.parse_args()




