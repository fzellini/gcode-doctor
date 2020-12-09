# gcode-doctor
A python program to manipulate gcode, resize, change max spindle speed, change feed rate

"""
python3 gdoctor.py -h
usage: gdoctor.py [-h] [--readgcode READGCODE] [--writegcode WRITEGCODE]
                  [--filter-inside-first] [--filter-start-x FILTER_START_X]
                  [--filter-start-y FILTER_START_Y]
                  [--filter-resize FILTER_RESIZE]
                  [--filter-feed-rate-multiply FILTER_FEED_RATE_MULTIPLY]
                  [--filter-feed-rate-max FILTER_FEED_RATE_MAX]
                  [--filter-spindle-speed-multiply FILTER_SPINDLE_SPEED_MULTIPLY]
                  [--filter-spindle-speed-max FILTER_SPINDLE_SPEED_MAX]

gcode doctor

optional arguments:
  -h, --help            show this help message and exit
  --readgcode READGCODE
  --writegcode WRITEGCODE
  --filter-inside-first
  --filter-start-x FILTER_START_X
  --filter-start-y FILTER_START_Y
  --filter-resize FILTER_RESIZE
  --filter-feed-rate-multiply FILTER_FEED_RATE_MULTIPLY
  --filter-feed-rate-max FILTER_FEED_RATE_MAX
  --filter-spindle-speed-multiply FILTER_SPINDLE_SPEED_MULTIPLY
  --filter-spindle-speed-max FILTER_SPINDLE_SPEED_MAX
"""
