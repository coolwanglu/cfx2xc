#!/usr/bin/env python

"""
cfx2xc.py

Homepage: http://code.google.com/p/cfx2xc/

Convert a CursorFX theme to an X11 Cursor theme

by Wang Lu <coolwanglu(a)gmail.com>
first version at 2011.04.04

Based on the analysis from http://hi.baidu.com/fatfish888/blog/item/3592500392c27808738da516.html

*** Requirements: python, python image library, xcursorgen, tar ***
"""


import zlib
import struct
import sys
import logging
import Image
import os
import re
import shutil


LOG_LEVEL=logging.DEBUG

PREPARE_TMP=True  # clear TMP_DIR before work
REMOVE_TMP=False  # clear TMP_DIR after work

AUTO_CROP=True # remove transparent border
SCALE=1. # resize ratio
RESIZE_FILTER=Image.ANTIALIAS 

INFINITE_INTERVAL=1000000 # interval given to xcursorgen in order to stop animation

TMP_DIR='tmp_cfx2xc' # be careful about this name, all files inside will be cleared!
LOG_FILENAME='log.txt'


# Don't change anything below this line

# OUTPUT_DIR will be TMP_DIR/<theme name>
OUTPUT_BASE_DIR=TMP_DIR+'/target'
ORIGINAL_DIR=TMP_DIR+'/original'
SCRIPT_DIR=TMP_DIR+'/scripts'
CFG_DIR=TMP_DIR+'/cfgs'
SCRIPT_LINE_PATTERN=re.compile(r'(\d+)(?:-(\d+))?(?:,(\d+))?')

CURSOR_STATUS_NORMAL = 1
CURSOR_STATUS_PRESSED = 2

ANIMATION_TYPE_NONE = 0
ANIMATION_TYPE_LOOP = 2
ANIMATION_TYPE_ALTERNATE = 3

# prepend the numbers to the filename such that they'll display in a nice order in a file manager

# the list of output file names are based on http://fedoraproject.org/wiki/Artwork/EchoCursors/NamingSpec
# and sd2xc was also referred to
CURSORFX_NAMEMAP={
         0  : ('00standard_select', ('default'
                                    ,'arrow'

                                    ,'top-left-arrow'
                                    ,'top_left_arrow'
                                    ,'left_ptr'

                                    ,'x-cursor'
                                    ,'X_cursor'
                                    ))

        ,1  : ('01help_select', ('ask'
                                ,'dnd-ask'

                                ,'help'
                                ,'question_arrow'
                                ,'whats_this'
                                ,'d9ce0ab605698f320427677b458ad60b'
                                ))

        ,2  : ('02working_in_background', ('progress'
                                          ,'left_ptr_watch'
                                          ,'08e8e1c95fe2fc01f976f1e063a24ccd'
                                          ,'3ecb610c1bf2410f44200f48c40d3599'
                                          ))

        ,3  : ('03busy', ('wait'
                         ,'watch'
                         ,'0426c94ea35c87780ff01dc239897213'
                         ))

        ,4  : ('04precision_select', ('crosshair'
                                     ,'cross'
                                     ,'cross_reverse'
                                     ,'tcross'
                                     ))

        ,5  : ('05text_select', ('text'
                                ,'xterm'
                                ,'ibeam'

                                ,'vertical-text'
                                ))

        ,6  : ('06handwriting', ('pencil',
                                ))

        ,7  : ('07unavailable', ('no-drop'
                                ,'dnd-none'
                                ,'03b6e0fcb3499374a867c041f52298f0'

                                ,'not-allowed'
                                ,'crossed_circle'
                                ,'forbidden'

                                ,'pirate'
                                ))

        ,8  : ('08north_resize', ('col-resize'
                                 ,'sb_v_double_arrow'
                                 ,'split_v'
                                 ,'14fef782d02440884392942c11205230'

                                 ,'n-resize'
                                 ,'top_side'

                                 ,'ns-resize'
                                 ,'v_double_arrow'
                                 ,'size_ver'
                                 ,'00008160000006810000408080010102'

                                 ,'top-tee'
                                 ,'top_tee'

                                 ,'up'
                                 ,'sb_up_arrow'
                                 ))

        ,9  : ('09south_resize', ('bottom-tee'
                                 ,'bottom_tee'

                                 ,'down'
                                 ,'sb_down_arrow'

                                 ,'s-resize'
                                 ,'bottom_side'
                                 ))

        ,10 : ('10west_resize', ('ew-resize'
                                ,'h_double_arrow'
                                ,'size_hor'
                                ,'028006030e0e7ebffc7f7070c0600140'

                                ,'left'
                                ,'sb_left_arrow'

                                ,'left-tee'
                                ,'left_tee'

                                ,'row-resize'
                                ,'sb_h_double_arrow'
                                ,'split_h'
                                ,'2870a09082c103050810ffdffffe0204'

                                ,'w-resize'
                                ,'left_side'
                                ))
        
        ,11 : ('11east_resize', ('e-resize'
                                ,'right_side'

                                ,'right'
                                ,'sb_right_arrow'

                                ,'right-tee'
                                ,'right_tee'
                                ))

        ,12 : ('12northwest_resize', ('nw-resize'
                                     ,'top_left_corner'
                                     ,'ul_angle'

                                     ,'nwse-resize'
                                     ,'fd_double_arrow'
                                     ,'size_fdiag'
                                     ,'c7088f0f3e6c8088236ef8e1e3e70000'
                                     ))

        ,13 : ('13southeast_resize', ('se-resize'
                                     ,'bottom_right_corner'
                                     ,'lr_angle'
                                     ))

        ,14 : ('14northeast_resize', ('ne-resize'
                                     ,'top_right_corner'
                                     ,'ur_angle'

                                     ,'nesw-resize'
                                     ,'bd_double_arrow'
                                     ,'size_bdiag'
                                     ,'fcf1c3c7cd4491d801f1e1c78f100000'
                                     ))

        ,15 : ('15southwest_resize', ('sw-resize'
                                     ,'bottom_left_corner'
                                     ,'ll_angle'
                                     ))

        ,16 : ('16move', ('cell'
                         ,'plus'

                         ,'all-scroll' 
                         ,'fleur'
                         ,'size_all'
                         ))

        ,17 : ('17alternate_select', ('top-right-arrow'
                                     ,'right_ptr'

                                     ,'move'
                                     ,'dnd-move'
                                     ,'4498f0e0c1937ffe01fd06f973665830'
                                     ,'9081237383d90e509aa00f00170e968f'

                                     ,'up-arrow'
                                     ,'center_ptr'
                                     ,'up_arrow'
                                     ))

        ,18 : ('18hand', ('alias'
                         ,'link'
                         ,'dnd-link'
                         ,'3085a0e285430894940527032f8b26df'
                         ,'640fb0e74195791501fd1ed57b41487f'

                         ,'left-hand'
                         ,'hand1'
                         ,'9d800788f1b08800ae810202380a0822'

                         ,'pointer'
                         ,'hand2'
                         ,'pointing_hand'
                         ,'e29285e634086352946a0e7090d73106'

                         ,'openhand'
                         ,'a2a266d0498c3104214a47bd64ab0fc8'
                         ,'b66166c04f8c3109214a4fbd64a50fc8'
                         ,'hand'
                         ))

        ,19 : ('19button', ('copy'
                           ,'dnd-copy'
                           ,'1081e37283d90000800003c07f3ef6bf'
                           ,'6407b0e94181790501fd1e167b474872'
                           ))
}

def try_mkdir(d):
    try:
        os.mkdir(d)
    except:
        pass

class CursorFX():
    def convert(self, fn):
        assert fn.endswith('.CursorFX')

        if PREPARE_TMP:
            try:
                shutil.rmtree(TMP_DIR)
            except:
                pass

        # OUTPUT_DIR and OUTPUT_CURSOR_DIR can will be created later, because we need to retrieve the theme_name first
        try_mkdir(TMP_DIR)
        try_mkdir(OUTPUT_BASE_DIR)
        try_mkdir(ORIGINAL_DIR)
        try_mkdir(SCRIPT_DIR)
        try_mkdir(CFG_DIR)

        logging.basicConfig(filename='%s/%s'%(TMP_DIR, LOG_FILENAME),level=LOG_LEVEL, format='%(message)s')

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

        self.info = data[:self.info_size].decode('utf-16le').split('\0')[:-1]
        logging.info('Theme info: %s' % (','.join(self.info),))
        while len(self.info) < 2:
            self.info.append('')

        if self.info[0].strip() == '':
            theme_name = fn[:-len('.CursorFX')]
        else:
            theme_name = self.info[0].strip()
        theme_name = theme_name.replace(' ','')
        theme_name = theme_name.replace(',','_')

        OUTPUT_DIR = OUTPUT_BASE_DIR + '/' + theme_name
        OUTPUT_CURSOR_DIR = OUTPUT_DIR + '/cursors'

        try_mkdir(OUTPUT_DIR)
        try_mkdir(OUTPUT_CURSOR_DIR)

        # start processing image data
        cur_pos = self.info_size
        while cur_pos < len(data):
            (pointer_type # maybe: 2 for pointer, 4 for effect, 8 for trail
            ,size_of_header_without_script
            ,size_of_header_and_image) = struct.unpack_from('<3I', data, cur_pos)

            if pointer_type != 2:
                logging.info('non-pointer image (%d) found, skipped' % (pointer_type,))
                cur_pos += size_of_header_and_image
                continue
            
            (unknown1
            ,image_index
            ,cursor_status
            ,unknown3
            ,frame_count
            ,image_width
            ,image_height
            ,frame_interval
            ,animation_type
            ,unknown4
            ,mouse_x
            ,mouse_y
            ,size_of_header_with_script
            ,size_of_image
            ,size_of_header_without_script2
            ,size_of_script
            ) = struct.unpack_from('<16I',data, cur_pos+struct.calcsize('<3I'))
          
            logging.debug('Image #%d:\n\
type: %u\n\
unknown1: %u\n\
index: %u\n\
status: %u\n\
unknown3: %u\n\
frame count: %u\n\
image size: %ux%u\n\
frame_interval %u\n\
unknown4: %u\n\
animation type: %u\n\
mouse position: (%u,%u)\n\
size of script: %u\n'\
% (image_index, pointer_type, unknown1, image_index, cursor_status, unknown3, frame_count, image_width, image_height, frame_interval, unknown4, animation_type, mouse_x, mouse_y, size_of_script))


            assert size_of_header_without_script == size_of_header_without_script2
            assert size_of_header_with_script == size_of_header_without_script + size_of_script
            assert size_of_header_and_image == size_of_header_with_script + size_of_image
            assert size_of_image == image_width * image_height * 4

            # crop images
            img = Image.fromstring("RGBA", (image_width, image_height), data[cur_pos+size_of_header_with_script:cur_pos+size_of_header_and_image], "raw", "BGRA", 0, -1)
            img.save('%s/img%d-%d.png'%(ORIGINAL_DIR, image_index, cursor_status))

            frame_width = image_width / frame_count
            frame_height = image_height

            img_list = []

            for i in range(frame_count):
                img_list.append(img.crop((frame_width*i,0,frame_width*(i+1),image_height)))
            
            # crop transparent border
            if AUTO_CROP:
                bbox = [mouse_x, mouse_y, mouse_x+1, mouse_y+1]
                for i in range(frame_count):
                    tbbox = img_list[i].getbbox()
                    if tbbox is not None:
                        bbox[0] = min(bbox[0], tbbox[0])
                        bbox[1] = min(bbox[1], tbbox[1])
                        bbox[2] = max(bbox[2], tbbox[2])
                        bbox[3] = max(bbox[3], tbbox[3])
                for i in range(frame_count):
                    img_list[i] = img_list[i].crop(bbox) 
                mouse_x -= bbox[0]
                mouse_y -= bbox[1]

            # resize
            for i in range(frame_count):
                w,h = img_list[i].size
                img_list[i] = img_list[i].resize((int(w*SCALE),int(h*SCALE)), RESIZE_FILTER)
            mouse_x = int(mouse_x * SCALE)
            mouse_y = int(mouse_y * SCALE)

            # save
            for i in range(frame_count):
                img_list[i].save('%s/img%d-%d_%d.png'%(ORIGINAL_DIR, image_index, cursor_status, i))

            # parse script...
            # currently "repeat/end repeat" is not supported
            cfg = open('%s/img%d-%d.cfg'%(CFG_DIR, image_index, cursor_status), 'w')
            
            #xcursor_size = max(frame_width, frame_height)
            xcursor_size = 32

            if size_of_script > 0:
                script_data = data[cur_pos+size_of_header_without_script:cur_pos+size_of_header_with_script].decode('utf-16le')[:-1].replace(';','\n').split()
                
                script_file = open('%s/script%d'%(SCRIPT_DIR, image_index),'w')
                script_file.write('\n'.join(script_data))
                script_file.close()

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
                            cfg.write('%d %d %d %s/img%d-%d_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, cursor_status, i-1, interval))

                    except:
                        logging.info('Cannot parse script line:\n%s' % (l,))
                        raise
                        pass
            else:
                if animation_type == ANIMATION_TYPE_NONE:
                    for i in range(frame_count):
                        cfg.write('%d %d %d %s/img%d-%d_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, cursor_status, i, (frame_interval if (i < frame_count-1) else INFINITE_INTERVAL)))
                elif animation_type == ANIMATION_TYPE_LOOP:
                    for i in range(frame_count):
                        cfg.write('%d %d %d %s/img%d-%d_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, cursor_status, i, frame_interval))
                elif animation_type == ANIMATION_TYPE_ALTERNATE:
                    for i in range(frame_count):
                        cfg.write('%d %d %d %s/img%d-%d_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, cursor_status, i, frame_interval))
                    for i in range(frame_count-2, 0, -1):
                        cfg.write('%d %d %d %s/img%d-%d_%d.png %d\n' % (xcursor_size, mouse_x, mouse_y, ORIGINAL_DIR, image_index, cursor_status, i, frame_interval))
                else:
                    logging.error('Unknown animation type: %d' % (animation_type,))
                    
            cfg.close() 

            # output
            (outfilename, links) = CURSORFX_NAMEMAP.get(image_index, ('%02dunknown'%(image_index,),()))

            # dirty codes for pressed cursors
            if cursor_status == CURSOR_STATUS_PRESSED:
                outfilename += '_pressed'
                links = ()

            os.system('xcursorgen "%s/img%d-%d.cfg" "%s/%s"' % (CFG_DIR, image_index, cursor_status, OUTPUT_CURSOR_DIR, outfilename))
            for l in links:
                try:
                    os.symlink(outfilename, '%s/%s' % (OUTPUT_CURSOR_DIR, l))
                except:
                    logging.info('failed in creating symlink: %s -> %s' % (outfilename, l))
            
            cur_pos += size_of_header_and_image

        # package
        index_theme_file = open('%s/index.theme' % (OUTPUT_DIR,),'w')
        index_theme_file.write("""[Icon Theme]
Name=%s
Comment=%s - converted by cfx2xc
Example=default
Inherits=core
""" % (theme_name, self.info[1]))
        index_theme_file.close()

        os.system('tar -caf "%s.tar.gz" -C "%s" "%s"' % (theme_name, OUTPUT_BASE_DIR, theme_name))

        if REMOVE_TMP:
            shutil.rmtree(TMP_DIR)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: ' + sys.argv[0] + ' <CursorFX theme file>'
        sys.exit(-1)

    if not sys.argv[1].endswith('.CursorFX'):
        print 'Not a CursorFX file!'
        sys.exit(-1)

    CursorFX().convert(sys.argv[1])

