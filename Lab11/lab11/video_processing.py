import cv2
import argparse

def detect(frame, classifier):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    objs = classifier.detectMultiScale(gray, 1.3, 5)
    return objs

parser = argparse.ArgumentParser()

parser.add_argument("--video", help="path to the video", default="./video/video.mp4")

args = parser.parse_args()

path = args.video

cap = cv2.VideoCapture(path)

fps = 10.0

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('./video/output.avi', fourcc, fps, (640, 360))

if(cap.isOpened() == False):
    print("Error opening video stream or file")

classifier = cv2.CascadeClassifier("998_763_14_35.xml")

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret == True:
        objs = detect(frame, classifier)
        res = frame.copy()
        for (x, y, w, h) in objs:
            cv2.rectangle(res, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # cv2.imshow("Press q to quit", res)
        out.write(res)
        # if cv2.waitKey(16) & 0xFF == ord("q"):
        #     break
    else:
        break
        
cap.release()
out.release()
cv2.destroyAllWindows()