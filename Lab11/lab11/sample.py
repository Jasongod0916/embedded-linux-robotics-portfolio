from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2

# construct the argument parse and parse the arguments


# Create a HOGDescriptor object
hog = cv2.HOGDescriptor()

# Initialize the People Detector
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


image = cv2.imread("img/input.jpg")

# rescale origin image to 400 (以寬度為基準，保持比例)(使用imutils函式進行rescale)
# ======
image = imutils.resize(image, width=400)
# ======

orig = image.copy()
cv2.imwrite("result.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 98])

# detect people in the image
(rects, weights) = hog.detectMultiScale(
    image,
    winStride=(4, 4),
    padding=(8, 8),
    scale=1.05
)

# draw the original bounding boxes
for (x, y, w, h) in rects:
    cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

# apply non-maxima suppression to the bounding boxes using a
# fairly large overlap threshold to try to maintain overlapping
# boxes that are still people
rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

# draw the final bounding boxes
for (xA, yA, xB, yB) in pick:
    # 得到行人的四個點，在原始圖案中將其括出來
    # ======
    cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
    # ======

# show the output images
cv2.imwrite("result.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 98])