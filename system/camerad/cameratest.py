import os

from threading import Thread
import cv2, time
import numpy as np
import pyopencl as cl
import pyopencl.array as cl_array
from common.basedir import BASEDIR
import copy

W, H = 1164, 874
INW, INH = 800, 448

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

# define a video capture object
#vid = cv2.VideoCapture(0, cv2.CAP_V4L)
#vid.set(cv2.CAP_PROP_FRAME_WIDTH, INW)
#vid.set(cv2.CAP_PROP_FRAME_HEIGHT, INH)
#vid.set(cv2.CAP_PROP_CONVERT_RGB, 0)
  

y = np.zeros((INH, INW), dtype=np.uint8)
u = np.zeros((INH, INW), dtype=np.uint8)
v = np.zeros((INH, INW), dtype=np.uint8)
out_y = np.zeros((H, W), dtype=np.uint8)
out_uv = np.zeros((H//2, W), dtype=np.uint8)

class VideoStreamWidget(object):
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src, cv2.CAP_V4L)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, INW)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, INH)
        print(self.capture.get(cv2.CAP_PROP_FPS))
        self.capture.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        # Start the thread to read frames from the video stream
        self.thread = Thread(target=self.update, args=())
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
                print(time.time() - self.t)
                self.t = time.time()
            time.sleep(.01)

    def get_frame(self):
        if self.hasFrame:
            return True, self.frame
        return False, False
    
    def stop(self):
        self.run = False
        self.capture.release()



video_stream_widget = VideoStreamWidget(0)
t = time.time()
while(True):
    #print(time.time() - t)
      
    # Capture the video frame
    # by frame
    #ret, frame = vid.read()
    ret, frame = video_stream_widget.get_frame()
    if not ret or time.time() - t < 0.03:
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
    cv2.imshow('yuv', out_yuv)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
  
# Destroy all the windows
cv2.destroyAllWindows()