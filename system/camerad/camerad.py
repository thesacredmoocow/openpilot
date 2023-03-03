#!/usr/bin/env python3
import argparse
import math
import os
import signal
import threading
import time
from multiprocessing import Process, Queue
from typing import Any
import gc
import copy

import numpy as np
import pyopencl as cl
import pyopencl.array as cl_array
import cv2

import cereal.messaging as messaging
from cereal import log, car
from cereal.visionipc import VisionIpcServer, VisionStreamType
from common.basedir import BASEDIR
from common.numpy_fast import clip
from common.realtime import DT_DMON, Ratekeeper, set_realtime_priority
from selfdrive.car.honda.values import CruiseButtons
from tools.sim.lib.can import can_function

W, H = 1280, 720
REPEAT_COUNTER = 5
PRINT_DECIMATION = 100
STEER_RATIO = 15.

def camerad_thread(sm=None, pm=None):
  gc.disable()
  set_realtime_priority(0)

  if pm is None:
    pm = messaging.PubMaster(['driverCameraState', 'roadCameraState', 'wideRoadCameraState'])


  if sm is None:
    sm = messaging.SubMaster(['carControl', 'controlsState'])

  #camera init stuff here
  #pub_type = 'driverCameraState'
  pub_type = 'wideRoadCameraState'
  yuv_type = VisionStreamType.VISION_STREAM_WIDE_ROAD
  #yuv_type = VisionStreamType.VISION_STREAM_DRIVER
  vipc_server = VisionIpcServer("camerad")
  frame_road_id = 0
  wide_road_id = 0

  vipc_server.create_buffers(VisionStreamType.VISION_STREAM_ROAD, 5, False, W, H)
  vipc_server.create_buffers(VisionStreamType.VISION_STREAM_WIDE_ROAD, 5, False, W, H)
  vipc_server.start_listener()

  # set up for pyopencl rgb to yuv conversion
  ctx = cl.create_some_context()
  queue = cl.CommandQueue(ctx)
  cl_arg = f" -DHEIGHT={H} -DWIDTH={W} -DRGB_STRIDE={W * 3} -DUV_WIDTH={W // 2} -DUV_HEIGHT={H // 2} -DRGB_SIZE={W * H} -DCL_DEBUG "

  kernel_fn = os.path.join(BASEDIR, "tools/sim/rgb_to_nv12.cl")
  with open(kernel_fn) as f:
    prg = cl.Program(ctx, f.read()).build(cl_arg)
    krnl = prg.rgb_to_nv12
  Wdiv4 = W // 4 if (W % 4 == 0) else (W + (4 - W % 4)) // 4
  Hdiv4 = H // 4 if (H % 4 == 0) else (H + (4 - H % 4)) // 4

  capRoad = cv2.VideoCapture(0)
  #capWideRoad = cv2.VideoCapture(2)
  capRoad.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
  capRoad.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

  while True:
    #sm.update()

    ret, frameRoad = capRoad.read()
    #ret, frameWideRoad = capWideRoad.read()
    #frameRoad = cv2.resize(frameRoad, [W, H])
    #frameWideRoad = cv2.resize(frameWideRoad, [W, H])

    #img = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    #img = np.reshape(img, (H, W, 4))
    #img = img[:, :, [0, 1, 2]].copy()

    # convert RGB frame to YUV
    #rgb = np.reshape(img, (H, W * 3))
    rgb = np.reshape(frameRoad, (H, W * 3))
    rgb_cl = cl_array.to_device(queue, rgb)
    yuv_cl = cl_array.empty_like(rgb_cl)
    krnl(queue, (np.int32(Wdiv4), np.int32(Hdiv4)), None, rgb_cl.data, yuv_cl.data).wait()
    yuv = np.resize(yuv_cl.get(), rgb.size // 2)
    eof = int(frame_road_id * 0.05 * 1e9)

    vipc_server.send(yuv_type, yuv.data.tobytes(), wide_road_id, eof, eof)
    vipc_server.send(VisionStreamType.VISION_STREAM_ROAD, yuv.data.tobytes(), frame_road_id, eof, eof)

    dat = messaging.new_message(pub_type)
    msg = {
      "frameId": frame_road_id,
      "transform": [1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0]
    }
    setattr(dat, pub_type, msg)
    pm.send(pub_type, dat)
    pm.send('roadCameraState', dat)

    wide_road_id += 1
    frame_road_id += 1



def main(sm=None, pm=None):
  camerad_thread(sm, pm)


if __name__ == '__main__':
  main()
