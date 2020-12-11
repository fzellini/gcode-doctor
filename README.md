# gcode-doctor
A python3 program to manipulate gcode, resize, change max spindle speed, change feed rate

The program use the excellent libray [pygcode](https://github.com/fragmuffin/pygcode).

gdoctor.py has been written from scratch in order to change on the fly feed rate and spindle max speed on my k40 laser cutter.

gdoctor.py load a gcode file, apply filters, and write to a new one

A cool filter is "inside-first", that change the paths in order to cut first the inside one, in that manner, e.g. cutting a shape that has another shape inside,
the external shape does not fall before the internal shape is not cutted.

Resize filter compute xrange and yrange of the input gcode, translate to axis origin in order to have xmin=0 and ymin=0, then resize.

Resize parameter is in the form of <Xmax>x<Ymax>, if both are specified, e.g. 100x100, the output gcode  will be circumscribed in a rectangle measuring 100 x 100 mm. If only a parameter is specified, e.g. 100x or x100, the given axis max value will be the given one, and the other scaled of the same amount.

```
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
```

Ex. use:

```
python3 gdoctor.py  --readgcode=../svg2gcode/out.gcode  --filter-spindle-speed-max=1000 --filter-inside-first --filter-feed-rate-max=300 --filter-resize=x40 --writegcode=out.gcode

python3 gdoctor.py  --readgcode=../svg2gcode/out.gcode  --filter-spindle-speed-max=150 --filter-feed-rate-max=2000 --filter-resize=150x80  --filter-min-distance=0.1 --writegcode=out.gcode 

```



