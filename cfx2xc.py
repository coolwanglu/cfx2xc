#!/usr/bin/env python

"""
cfx2xc.py

Convert a CursorFX theme to an X11 Cursor theme

by Wang Lu <coolwanglu(a)gmail.com>
first version at 2011.04.04

Based on the analysis from http://hi.baidu.com/fatfish888/blog/item/3592500392c27808738da516.html

*** Requirements: python, python image library, xcursorgen ***
"""


import zlib
import struct
import sys
import logging
import Image
import os
import re

LOG_LEVEL=logging.DEBUG
TMP_DIR='tmp_cfx2xc'
ORIGINAL_DIR=TMP_DIR+'/original'
OUTPUT_DIR=TMP_DIR+'/cursors'
SCRIPT_DIR=TMP_DIR+'/scripts'
CFG_DIR=TMP_DIR+'/cfgs'
SCRIPT_LINE_PATTERN=re.compile(r'(\d+)(?:-(\d+))?(?:,(\d+))?')

def try_mkdir(d):
    try:
        os.mkdir(d)
    except:
        pass

class CursorXP():
    def __init__ (self):
        logging.basicConfig(level=LOG_LEVEL, format='%(message)s')

    def convert(self, fn):
        try_mkdir(TMP_DIR)
        try_mkdir(ORIGINAL_DIR)
        try_mkdir(OUTPUT_DIR)
        try_mkdir(SCRIPT_DIR)
        try_mkdir(CFG_DIR)

        data = open(fn).read()
        (self.version # maybe
        ,self.header_size
        ,self.data_size # uncompressed
        ,self.theme_type # maybe...like pointer/trail/effect
        ) = struct.unpack_from('<IIII', data, 0)
        (self.info_size,) = struct.unpack_from('<I', data, self.header_size-4)

        logging.debug('Header Info:\n\n\
Version: %u\n\
Header size: %u\n\
Data size: %u\n\
Info size: %u\n\n'\
% (self.version, self.header_size, self.data_size, self.info_size))

        data = zlib.decompress(data[self.header_size:])
        assert len(data) == self.data_size

        self.info = data[:self.info_size].decode('utf-16le')
        logging.info('Theme info: %s' % (','.join(self.info.split('\0')),))

        # start processing image data
        cur_pos = self.info_size
        while cur_pos < len(data):
            (pointer_type # maybe: 2 for pointer, 4 for effect, 8 for trail
            ,size_of_header_without_script
            ,size_of_header_and_image) = struct.unpack_from('<3I', data, cur_pos)

            if pointer_type != 2:
                logger.info('non-pointer image found, skipped')
                cur_pos += size_of_header_and_image
                continue
            
            (unknown1
            ,image_index
            ,unknown2
            ,unknown3
            ,frame_count
            ,image_width
            ,image_height
            ,frame_interval
            ,unknown4
            ,animation_type # 2 for loop, 3 for alternate animation, 0 for neither
            ,mouse_x
            ,mouse_y
            ,size_of_header_with_script
            ,size_of_image
            ,size_of_header_without_script2
            ,size_of_script
            ) = struct.unpack_from('<16I',data, cur_pos+struct.calcsize('<3I'))
          
            logging.info('Image #%d:\n\
type: %u\n\
unknown1: %u\n\
index: %u\n\
unknown2: %u\n\
unknown3: %u\n\
frame count: %u\n\
image size: %ux%u\n\
frame_interval %u\n\
unknown4: %u\n\
animation type: %u\n\
mouse position: (%u,%u)\n\
size of script: %u\n\
size of script2: %u\n'\
% (image_index, pointer_type, unknown1, image_index, unknown2, unknown3, frame_count, image_width, image_height, frame_interval, unknown4, animation_type, mouse_x, mouse_y, size_of_script, size_of_header_without_script2))


            assert size_of_header_without_script == size_of_header_without_script2
            assert size_of_header_with_script == size_of_header_without_script + size_of_script
            assert size_of_header_and_image == size_of_header_with_script + size_of_image
            assert size_of_image == image_width * image_height * 4

            # crop images
            img = Image.fromstring("RGBA", (image_width, image_height), data[cur_pos+size_of_header_with_script:cur_pos+size_of_header_and_image], "raw", "BGRA", 0, -1)
            frame_width = image_width / frame_count
            frame_height = image_height
            for i in range(frame_count):
                img.crop((frame_width*(i-1),0,frame_width*i,image_height)).save('%s/img%s_%d.png'%(ORIGINAL_DIR,image_index,i))

            # parse script...
            # currently "repeat/end repeat" is not supported
            cfg = open('%s/img%d.cfg'%(CFG_DIR, image_index), 'w')
            xcursor_size = max(frame_width, frame_height)

            if size_of_script > 0:
                script_data = data[cur_pos+size_of_header_without_script:cur_pos+size_of_header_with_script].decode('utf-16le')[:-1].replace(';','\n').split()
                
                open('%s/script%d'%(SCRIPT_DIR, image_index),'w').write('\n'.join(script_data))

                last_interval = frame_interval
                for l in script_data:
                    try:
                        (start_frame, end_frame, interval) = SCRIPT_LINE_PATTERN.match(l).groups()
                        start_frame = int(start_frame)
                        if end_frame is None:
                            end_frame = start_frame
                        else:
                            end_frame = int(end_frame)
                        if interval is None:
                            interval = last_interval
                        else:
                            interval = int(interval)
                            last_interval = interval

                        step = 1 if end_frame >= start_frame else -1

                        # note that the frame index in the script is 1-based
                        for i in range(start_frame, end_frame+step, step):
                            cfg.write('%d %d %d %s/img%s_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, i-1, interval))

                    except:
                        logging.info('Cannot parse script line:\n%s' % (l,))
                        raise
                        pass
            else:
                for i in range(frame_count):
                    cfg.write('%d %d %d %s/img%s_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, i, frame_interval))
            cfg.close() 

            os.system('xcursorgen "%s/img%d.cfg" "%s/cur%d"' % (CFG_DIR, image_index, OUTPUT_DIR, image_index))
            
            cur_pos += size_of_header_and_image
         



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: ' + sys.argv[0] + ' <CursorXP theme file>'
        sys.exit(-1)

    CursorXP().convert(sys.argv[1])

