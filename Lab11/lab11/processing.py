import cv2
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--image", help="path to the image", default="img/Lenna.png")

args = parser.parse_args()

path = args.image

image = cv2.imread(path)

cv2.imshow("Original", image)

resized = cv2.resize(image, (400, 400))

x1, y1, x2, y2 = 100, 120, 300, 360

roi = resized[y1:y2, x1:x2]
cv2.imshow("ROI", roi)

cv2.rectangle(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
cv2.imshow("Rectangle", resized)

gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
cv2.imshow("Gray", gray)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_img = clahe.apply(gray)
cv2.imshow("CLAHE", clahe_img)

cv2.imwrite("./img/clahe.jpg", clahe_img)

cv2.waitKey(0)
cv2.destroyAllWindows()
