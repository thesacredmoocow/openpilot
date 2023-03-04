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
import cv2

import cereal.messaging as messaging
from cereal.visionipc import VisionIpcServer, VisionStreamType
from common.basedir import BASEDIR
from common.realtime import DT_DMON, set_realtime_priority

W, H = 1164, 874
INW, INH = 864, 480

# copied from common.transformations/camera.py
eon_focal_length = 910.0  # pixels
eon_dcam_focal_length = 860.0  # pixels

webcam_focal_length = -908.0/1.5  # pixels

eon_intrinsics = np.array([
  [eon_focal_length,   0.,   1164/2.],
  [  0.,  eon_focal_length,  874/2.],
  [  0.,    0.,     1.]])

webcam_intrinsics = np.array([
  [webcam_focal_length,   0.,   1280/2/1.5],
  [  0.,  webcam_focal_length,  720/2/1.5],
  [  0.,    0.,     1.]])

trans_webcam_to_eon_rear = np.dot(eon_intrinsics, np.linalg.inv(webcam_intrinsics))

class VideoStreamWidget(object):
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src, cv2.CAP_V4L)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, INW)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, INH)
        self.capture.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        # Start the thread to read frames from the video stream
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.run = True
        self.hasFrame = False
        #self.frame = None

        self.thread.start()
        
    def update(self):
        # Read the next frame from the stream in a different thread
        self.t = time.time()
        while self.run:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
                self.hasFrame = True
                self.t = time.time()
            time.sleep(.01)

    def get_frame(self):
        if self.hasFrame:
            return True, self.frame
        return False, False
    
    def stop(self):
        self.run = False


def camerad_thread(sm=None, pm=None):
  gc.disable()
  set_realtime_priority(0)

  if pm is None:
    pm = messaging.PubMaster(['driverCameraState', 'roadCameraState', 'wideRoadCameraState'])


  if sm is None:
    sm = messaging.SubMaster(['carControl', 'controlsState'])

  #camera init stuff here
  pub_type = 'driverCameraState'
  #pub_type = 'roadCameraState'
  #yuv_type = VisionStreamType.VISION_STREAM_ROAD
  yuv_type = VisionStreamType.VISION_STREAM_DRIVER
  vipc_server = VisionIpcServer("camerad")
  frame_road_id = 0

  vipc_server.create_buffers(yuv_type, 5, False, W, H)
  vipc_server.start_listener()

  #capRoad = cv2.VideoCapture(0, cv2.CAP_V4L)
  #capRoad.set(cv2.CAP_PROP_FRAME_WIDTH, INW)
  #capRoad.set(cv2.CAP_PROP_FRAME_HEIGHT, INH)
  #capRoad.set(cv2.CAP_PROP_FPS, 30)
  #capRoad.set(cv2.CAP_PROP_CONVERT_RGB, 0)

  y = np.zeros((INH, INW), dtype=np.uint8)
  u = np.zeros((INH, INW), dtype=np.uint8)
  v = np.zeros((INH, INW), dtype=np.uint8)
  out_y = np.zeros((H, W), dtype=np.uint8)
  out_uv = np.zeros((H//2, W), dtype=np.uint8)

  video_stream_widget = VideoStreamWidget(0)
  t = time.time()
  while True:
    ret, frame = video_stream_widget.get_frame()#capRoad.read()

    if not ret or time.time() - t < 0.04:
        time.sleep(0.01)
        continue
    t = time.time()
    y = frame[:,:,0]
    u[:,1::2] = frame[:,:,1][:,::2]
    u[:,::2] = u[:,1::2]
    v[:,::2] = frame[:,:,1][:,1::2]
    v[:,1::2] = v[:,::2]
    yuv = cv2.merge([y, u, v])

    yuv = cv2.warpPerspective(yuv, trans_webcam_to_eon_rear, (1164, 874), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out_y = yuv[:,:,0]
    out_uv[:,::2] = yuv[:,:,1][::2,::2]
    out_uv[:,1::2] = yuv[:,:,2][::2,::2]
    out_yuv = yuv = np.append(out_y, out_uv, axis=0)
    eof = int(frame_road_id * 0.05 * 1e9)

    vipc_server.send(yuv_type, out_yuv.data.tobytes(), frame_road_id, eof, eof)

    dat = messaging.new_message(pub_type)
    msg = {
      "frameId": frame_road_id,
      "transform": [1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0]
    }
    setattr(dat, pub_type, msg)
    pm.send(pub_type, dat)
    frame_road_id += 1



def main(sm=None, pm=None):
  camerad_thread(sm, pm)


if __name__ == '__main__':
  main()
