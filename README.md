# v4l2-cffi: Python binding for V4L2 API

This binding parses your current version of `/usr/src/linux/videodev2.h`,
and builds a python wrapper around it using `cffi`. It's somewhat different to
other python v4l2 bindings ([v4l2](https://pypi.org/project/v4l2/), [v4l2capture](https://pypi.org/project/v4l2capture/), [pyv4l2](https://github.com/duanhongyi/pyv4l2)) as `v4l2-cffi` uses the current installed version of
your V4L2 kernel framework, instead of using its own version. Its main drawback is that some part may not be (and are not, see below) recognized.

  - Installation:   just run
  ```
python3 setup.py install --user
  ```
  - Test: there is a small test script in the `tests` directory which simply grabs 50 frames from `/dev/video0` and puts the result in `/tmp/video.yuv` (yes, it supposes that your video device is configured to capture YUV frames).

This is a Work in Progress, only tested with Ubuntu 18.04 (kernel 4.15.0-51-generic).
Actually I am not sure that it is maintainable due to the limitations in the python C parsers (`pycparser` and `pycparserext`).

There are still some unparsed stuff, (badly) displayed when you run the setup script

```
generated /tmp/v4l2-cffi/v4l2_cache/videodev2.defines.h from /usr/include/linux/videodev2.h
Error:
not parsed  10
V4L2_MAP_COLORSPACE_DEFAULT(is_sdtv,is_hdtv) --> ((is_sdtv) ? V4L2_COLORSPACE_SMPTE170M : ((is_hdtv) ? V4L2_COLORSPACE_REC709 : V4L2_COLORSPACE_SRGB))
V4L2_MAP_XFER_FUNC_DEFAULT(colsp) --> ((colsp) == V4L2_COLORSPACE_ADOBERGB ? V4L2_XFER_FUNC_ADOBERGB : ((colsp) == V4L2_COLORSPACE_SMPTE240M ? V4L2_XFER_FUNC_SMPTE240M : ((colsp) == V4L2_COLORSPACE_DCI_P3 ? V4L2_XFER_FUNC_DCI_P3 : ((colsp) == V4L2_COLORSPACE_RAW ? V4L2_XFER_FUNC_NONE : ((colsp) == V4L2_COLORSPACE_SRGB || (colsp) == V4L2_COLORSPACE_JPEG ? V4L2_XFER_FUNC_SRGB : V4L2_XFER_FUNC_709)))))
V4L2_MAP_YCBCR_ENC_DEFAULT(colsp) --> (((colsp) == V4L2_COLORSPACE_REC709 || (colsp) == V4L2_COLORSPACE_DCI_P3) ? V4L2_YCBCR_ENC_709 : ((colsp) == V4L2_COLORSPACE_BT2020 ? V4L2_YCBCR_ENC_BT2020 : ((colsp) == V4L2_COLORSPACE_SMPTE240M ? V4L2_YCBCR_ENC_SMPTE240M : V4L2_YCBCR_ENC_601)))
V4L2_MAP_QUANTIZATION_DEFAULT(is_rgb_or_hsv,colsp,ycbcr_enc) --> (((is_rgb_or_hsv) && (colsp) == V4L2_COLORSPACE_BT2020) ? V4L2_QUANTIZATION_LIM_RANGE : (((is_rgb_or_hsv) || (colsp) == V4L2_COLORSPACE_JPEG) ? V4L2_QUANTIZATION_FULL_RANGE : V4L2_QUANTIZATION_LIM_RANGE))
V4L2_DV_BT_BLANKING_WIDTH(bt) --> ((bt)->hfrontporch + (bt)->hsync + (bt)->hbackporch)
V4L2_DV_BT_FRAME_WIDTH(bt) --> ((bt)->width + V4L2_DV_BT_BLANKING_WIDTH(bt))
V4L2_DV_BT_BLANKING_HEIGHT(bt) --> ((bt)->vfrontporch + (bt)->vsync + (bt)->vbackporch + (bt)->il_vfrontporch + (bt)->il_vsync + (bt)->il_vbackporch)
V4L2_DV_BT_FRAME_HEIGHT(bt) --> ((bt)->height + V4L2_DV_BT_BLANKING_HEIGHT(bt))
V4L2_CTRL_ID2CLASS(id) --> ((id) & 0x0fff0000UL)
V4L2_CTRL_ID2WHICH(id) --> ((id) & 0x0fff0000UL)

```
