import cv2
import time

def detect(frame, classifier):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    objs = classifier.detectMultiScale(gray, 1.3, 5)
    return objs

# use webcam
cap = cv2.VideoCapture(0)
fps = 10
prev = 0

classifier = cv2.CascadeClassifier("998_763_14_35.xml")

if(cap.isOpened() == False):
    print("Error opening video stream or file")

while(cap.isOpened()):
    ret, frame = cap.read()
    time_elapsed = time.time() - prev
    if ret == True:
        if time_elapsed > 1./fps:
            prev = time.time()
            objs = detect(frame, classifier)
            res = frame.copy()
            for (x, y, w, h) in objs:
                cv2.rectangle(res, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("Press q to quit", res)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break