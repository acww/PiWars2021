# Line following and finding for RedBrick
# Written by Angus Wallis 2020/21

from picamera.array import PiRGBArray   # Necessary imports
from picamera import PiCamera
from approxeng.input.selectbinder import ControllerResource
import Base
import numpy as np
import cv2
import threading
from queue import LifoQueue
import threaded               # Audio handling library

get_side = threaded.get_side

IMG_WIDTH = 80         # Camera Parameters
IMG_HEIGHT = 60

MID = IMG_WIDTH/2

camera = PiCamera()     # More camera parameters
camera.resolution = (IMG_WIDTH, IMG_HEIGHT)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(IMG_WIDTH, IMG_HEIGHT))

base_speed = 180   # Speed parameters
turn_speed = 150
speed_adj = 4

motors = Base.Motors(MID, base_speed, turn_speed, speed_adj)   # motor handling library does lights

def follow(MID):
    motors.drive('allign', MID[0])

# This function is from here:
# https://www.pyimagesearch.com/2015/04/20/sorting-contours-using-python-and-opencv/
# by Adrian Rosebrock on April 20, 2015
def sort_contours(cnts, method="left-to-right"):   # Generic contour sorter, left-right is what is used
    # initialize the reverse flag and sort index
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
        key=lambda b:b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return cnts

pre_allign_side = 'left'
def think(cnts, q):              # audio decision maker
    cnts = sort_contours(cnts)
    side = q.get()
    if side == 'left':          # Left most pixel if audio side is left
        cnt = cnts[0]
        L = tuple(cnt[cnt[:,:,0].argmin()][0])
        motors.drive('allign', L[0], 'h')
    else:
        cnt = cnts[-1]           # right most pixel if audio side is right
        R = tuple(cnt[cnt[:,:,0].argmax()][0])
        motors.drive('allign', R[0], 'h')
    return side

pre_approxLen = 0         # start up value
def linerun(joystick, q):      # camera thread
    side = 'right'
    while True:
        joystick.check_presses()          # checks controller
        if 'circle' in joystick.presses:  # if button on controller pressed returns to normal driving mode
            print('line finishing...')
            motors.stop()
            cv2.destroyAllWindows()
            return
        #try:
        rawCapture.truncate(0)                                          # Gets all the contours of a thresholded image
        camera.capture(rawCapture, format="bgr", use_video_port=True)
        image = rawCapture.array
        image = image[0:IMG_HEIGHT-2, 0:IMG_WIDTH]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        thresh = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)[1]
        _, contours, hierarchy=cv2.findContours(thresh.copy(),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
        cnts = sorted(contours, key=cv2.contourArea)
        if cnts:            # if there are contours
            cnt=cnts[0]                             # finds biggest contour and draws it onto the image
            accuracy=0.023*cv2.arcLength(cnt,True)
            approx=cv2.approxPolyDP(cnt,accuracy,True)
            approxLen = len((approx))
            img = cv2.drawContours(image, [approx], -1, (0,255,0), 3)
            cv2.imshow('img', img)
            if len(cnts) >= 2:                      # exception if there's two lines
                if cv2.contourArea(cnts[1]) > 1000:
                    approxLen = 7
            if approxLen >= 7:              # if there's a split decide what to do
                side = think(cnts, q)
            else:
                cnts = sort_contours(cnts)  # if there isnt a split follow the line
                if side == 'left':
                    cnt = cnts[0]
                    C = tuple(cnt[cnt[:,:,0].argmin()][0])
                else:
                    cnt = cnts[-1]
                    C = tuple(cnt[cnt[:,:,0].argmax()][0])
                follow(C)
            pre_approxLen = approxLen
        cv2.waitKey(1)       # delay to show frames

def line(joystick):         # starts the two threads
    q = LifoQueue()
    stop_thread = False
    t2 = threading.Thread(target=get_side, args=(q, lambda : stop_thread,))
    t2.start()
    linerun(joystick, q)
    stop_thread = True
    t2.join()
    return