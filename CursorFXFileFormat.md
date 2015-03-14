#The format of the .CursorFX file

Base on the analysis on [link1](http://hi.baidu.com/fatfish888/item/06ef0909f854d618ebfe3822) and [link2](http://hi.baidu.com/fatfish888/item/993a0cff3981de5cc8f33722)

## The Structure ##


---


```
/////// BEGINNING_OF_FILE

// FILE HEADER
struct {
  int version:4; // not sure
  int header_size:4
  int data_size_before_compressed:4;
  int theme_type:4; // not sure
  int info_size:4;
} header;

/////////////////
// EVERYTHING BELOW ARE COMPRESSED WITH ZLIB

char theme_info[info_size]; // theme name, author etc...
                            // several 0-terminated strings, encoded in utf-16le

// now comes the pointers, each pointer consists of a header and an image
// the pointers are stored one by one till the end
struct {
  // HEADER BEGIN
  // common part for pointer, effect & trail
  int pointer_type:4; // 2 for pointer, 4 for effect, 8 for trail
  int size_of_header:4;
  int size_of_pointer:4;
  
  // effect & trail and not supported by cfx2xc, and the detail info are unknown
  // info below are for type 'pointer' only (pointer_type == 2)
  int unknown:4;
  int image_index:4; // 0-19, the index of this pointer, 
                     // 0 for standard_select, 19 for button etc...
  int cursor_status:4; // 1 for normal, 2 for pressed
  int unknown:4;
  int frame_count:4;
  int image_width,image_height:4;
  int frame_interval:4;
  int animation_type:4; // 0 for none, 2 for loop, 3 for alternate
  int unknown:4;
  int mouse_x,mouse_y:4; // hot spot
  int size_of_header_and_script:4; // == size_of_header + size_of_script
  int size_of_image:4;
  int size_of_header:4;
  int size_of_script:4;
  // END OF HEADER

  char script[size_of_script]; // encoded in utf-16le

  char image_data[size_of_image]; // an image of size (image_width, image_height)
                                  // stored in raw RGBA, bottom-up
                                  // the image stores the frame sequence horizontally
  
} pointers []; // this is actually not accurate, because size_of_script & size_of_image may differ for pointers

/////// END_OF_FILE
```


---


## Note ##
All integers are stored in little endian