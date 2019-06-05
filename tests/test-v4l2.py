#!/usr/bin/env python3
import v4l2
from v4l2 import *
#import fcntl
import mmap
import select
import time
import errno

def xioctl(fh, request, *args):
    while True:
        try:
            r = v4l2.ioctl(fh, request, *[a if type(a) != int else ffi.cast('int', a) for a in args])
        except OSError as e:
            print(e.errno)
            if e.errno != errno.EINTR:
                break
        #print(r)
        if r != - 1:
            break
    return r

vd = open('/dev/video0', 'rb+', buffering=0)
#vd = open('/dev/video0', 'rb')


print(">> get device capabilities")
cp = v4l2_capability()
xioctl(vd.fileno(), VIDIOC_QUERYCAP, cp)

print("Driver:", "".join((chr(c) for c in cp.driver)))
print("Name:", v4l2._cstr(cp.card))
print("Is a video capture device?", bool(cp.capabilities & V4L2_CAP_VIDEO_CAPTURE))
print("Supports read() call?", bool(cp.capabilities &  V4L2_CAP_READWRITE))
print("Supports streaming?", bool(cp.capabilities & V4L2_CAP_STREAMING))

print(">> device setup")
fmt = v4l2_format()
fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
xioctl(vd.fileno(), VIDIOC_G_FMT, fmt)  # get current settings
print("width:", fmt.fmt.pix.width, "height", fmt.fmt.pix.height)
print("pxfmt:", "V4L2_PIX_FMT_YUYV" if fmt.fmt.pix.pixelformat == V4L2_PIX_FMT_YUYV else fmt.fmt.pix.pixelformat)
print("bytesperline:", fmt.fmt.pix.bytesperline)
print("sizeimage:", fmt.fmt.pix.sizeimage)
xioctl(vd.fileno(), VIDIOC_S_FMT, fmt)  # set whatever default settings we got before

print(">>> streamparam")  ## somewhere in here you can set the camera framerate
parm = v4l2_streamparm()
parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
parm.parm.capture.capability = V4L2_CAP_TIMEPERFRAME
xioctl(vd.fileno(), VIDIOC_G_PARM, parm)
xioctl(vd.fileno(), VIDIOC_S_PARM, parm)  # just got with the defaults

print(">> init mmap capture")
req = v4l2_requestbuffers()
req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
req.memory = V4L2_MEMORY_MMAP
req.count = 4  # nr of buffer frames
xioctl(vd.fileno(), VIDIOC_REQBUFS, req)  # tell the driver that we want some buffers 
print("req.count", req.count)


buffers = []

print(">>> VIDIOC_QUERYBUF, mmap")
for ind in range(req.count):
    # setup a buffer
    buf = v4l2_buffer()
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
    buf.memory = V4L2_MEMORY_MMAP
    buf.index = ind
    xioctl(vd.fileno(), VIDIOC_QUERYBUF, buf)

    mm = mmap.mmap(vd.fileno(), buf.length, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=buf.m.offset)
    buffers.append(mm)

    # queue the buffer for capture
    #xioctl(vd.fileno(), VIDIOC_QBUF, buf)

print(">>> VIDIOC_QBUF")

for ind in range(req.count):
    # setup a buffer
    buf = v4l2_buffer()
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
    buf.memory = V4L2_MEMORY_MMAP
    buf.index = ind
    xioctl(vd.fileno(), VIDIOC_QBUF, buf)
    
print(">> Start streaming")
#buf_type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
buf_type=ffi.new('int *', V4L2_BUF_TYPE_VIDEO_CAPTURE)
xioctl(vd.fileno(), VIDIOC_STREAMON, buf_type)
#r=ioctl(vd.fileno(), VIDIOC_STREAMON, buf_type)

print(">> Capture image")
t0 = time.time()
max_t = 1
ready_to_read, ready_to_write, in_error = ([], [], [])
#print(">>> select")
#while len(ready_to_read) == 0 and time.time() - t0 < max_t:
#    ready_to_read, ready_to_write, in_error = select.select([vd], [], [], max_t)

print(">>> download buffers")
vid = open("/tmp/video.yuv", "wb")

for i in range(50):  # capture 50 frames
    #print(">>> select")
    ready_to_read, ready_to_write, in_error = select.select([vd.fileno()], [], [])
    #print(ready_to_read, ready_to_write, in_error)
    buf = v4l2_buffer()
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
    buf.memory = V4L2_MEMORY_MMAP
    xioctl(vd.fileno(), VIDIOC_DQBUF, buf)  # get image from the driver queue
    #print("buf.index", buf.index)
    mm = buffers[buf.index]
    # print first few pixels in gray scale part of yuvv format packed data
    #print(" ".join(("{0:08b}".format(mm[x]) for x in range(0,16,2))))
    vid.write(mm.read())  # write the raw yuyv data from the buffer to the file
    #vid.write(bytes((bit for i, bit in enumerate(mm.read()) if not i % 2)))  # convert yuyv to grayscale
    mm.seek(0)
    xioctl(vd.fileno(), VIDIOC_QBUF, buf)  # requeue the buffer

print(">> Stop streaming")
ioctl(vd.fileno(), VIDIOC_STREAMOFF, buf_type)
vid.close()
vd.close()

print("video saved to video.yuv")
print("play it with mpv video.yuv --demuxer=rawvideo --demuxer-rawvideo-w=640 --demuxer-rawvideo-h=480 --demuxer-rawvideo-format=YUY2")
print("play it with ffplay -video_size 640x480 -pixel_format yuyv422 -f rawvideo video.yuv")
