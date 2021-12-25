#!/usr/bin/env python3

import re
import argparse
import os
import glob

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

parser = argparse.ArgumentParser(description='Creates one gcode file from multiple enumerated gcode files by splitting them at given layer heights.')
parser.add_argument('dir', type=dir_path)
parser.add_argument('layer_heights', nargs='+', help='a space seperated list of layer heights of where to cut from each input file')

args = parser.parse_args()

working_dir = args.dir
layer_heights = sorted([float(x) for x in args.layer_heights])

globed_in_files = glob.glob(os.path.join(working_dir, '*.gcode'))
in_files = sorted([fname for fname in globed_in_files if re.match("[0-9]+.gcode", os.path.basename(fname))])

if len(in_files) == 0:
    print(f'No numbered gcode files found as input in directory {working_dir}. Exiting.')
    exit()

print(f'Found {len(in_files)} input gcode files in directory {working_dir}')

if len(in_files) < 2:
    print('Two or more input files needed. Exiting.')
    exit()

out_file_path = os.path.join(working_dir, 'out.gcode')

print(f'{len(layer_heights)} layer heights were given: {layer_heights}')

# check we have one more file than split layer heights
if len(in_files) != len(layer_heights) + 1:
    print('Need exactly one more input files than layer heights for this to work. Exiting.')
    exit()

def get_gcode_layer_count(fname):
    layers_found = 0
    with open(fname) as open_file:
        for line in open_file:
            if line.startswith(';LAYER_CHANGE'):
                layers_found += 1
    return layers_found

def print_gcode_retraction_settings(fname):
    print(f'Retraction settings in file {fname}:')
    with open(fname) as open_file:
        for line in open_file:
            if line.startswith('; retract_'):
                print(line, end='')

def get_gcode_max_layer_height(fname):
    max_layer_height = 0.0
    with open(fname) as open_file:
        get_layer = False
        for line in open_file:
            if line.startswith(';LAYER_CHANGE'):
                    get_layer = True
                    continue
            if get_layer:
#                print(line)
                get_layer = False
                layer_height_search = re.search(';Z:([.0-9]+)', line)
                if layer_height_search:
                    layer_height = layer_height_search.group(1)
#                    print(layer_height)
                    max_layer_height = float(layer_height)
    return max_layer_height

layer_counts = set()
max_layer_heights = set()
for fname in in_files:
    count = get_gcode_layer_count(fname)
    layer_counts.add(count)
    max = get_gcode_max_layer_height(fname)
    max_layer_heights.add(max) 
    print (f'{os.path.basename(fname)} has {count} layers and {max} max layer height')

if len(layer_counts) != 1:
    print('Not all files have the same layer count. Exiting')
    exit()

if len(max_layer_heights) != 1:
    print('Not all files have the same max layer height. Exiting')
    exit()

max_layer_height = max_layer_heights.pop()

for height in layer_heights:
    if height > max_layer_height:
        print(f'Given height {height} is bigger than maximum layer height {max_layer_height}. Exiting')
        exit()

print('##########')
for in_file in in_files:
    print_gcode_retraction_settings(in_file)
    print('##########')

with open(out_file_path, 'w') as out_file:
    def write_line_out(line):
        out_file.write(f"{i} ### {line}")

    in_wanted_line = True
    for i, in_file in enumerate(in_files):
        with open(in_file) as current_file:
            get_layer = False
            
            for line in current_file:
                if line.startswith(';LAYER_CHANGE'):
                    get_layer = True
                    if in_wanted_line:
                        write_line_out(line)
                    continue
                if get_layer:
        #            print(line)
                    get_layer = False
                    layer_height_search = re.search(';Z:([.0-9]+)', line)
                    if layer_height_search:
                        layer_height = layer_height_search.group(1)
    #                    print(layer_height)
                        layer_height = float(layer_height)

                        if i == 0:
                            lower = 0
                        else:
                            try:
                                lower = float(layer_heights[i-1])
                            except IndexError:
                                lower = 0
                        try:
                            higher = float(layer_heights[i])
                        except IndexError:
                            higher = float('inf')

                        if layer_height >= lower and layer_height < higher:
                            #print(i, layer_height)
                            in_wanted_line = True
                        else: 
                            in_wanted_line = False
                            continue
                if in_wanted_line:
                    write_line_out(line)

print(f'Output written to file {out_file_path}')

