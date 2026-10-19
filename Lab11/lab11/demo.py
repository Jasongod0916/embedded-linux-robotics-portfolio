from __future__ import print_function
from imutils.object_detection import non_max_suppression
import numpy as np
import imutils
import cv2
import os


# =========================
# 檔案路徑設定
# =========================

IMAGE_PATH = "img/pedestrian.jpg"
OUTPUT_PATH = "img/result_demo.jpg"
CAR_XML_PATH = "cars.xml"


# =========================
# 工具函式
# =========================

def check_file(path, error_message):
    if not os.path.exists(path):
        print(error_message)
        exit(1)


def load_image(image_path, width=400):
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: 圖片讀取失敗：{image_path}")
        exit(1)

    # 照 Lab11 sample.py：以寬度 400 為基準縮放
    image = imutils.resize(image, width=width)
    return image


def create_people_detector():
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return hog


def create_car_detector(car_xml_path):
    car_classifier = cv2.CascadeClassifier(car_xml_path)

    if car_classifier.empty():
        print("Error: 車子偵測 XML 讀取失敗")
        exit(1)

    return car_classifier


# =========================
# 偵測函式
# =========================

def detect_people(image, hog):
    rects, weights = hog.detectMultiScale(
        image,
        winStride=(4, 4),
        padding=(8, 8),
        scale=1.05
    )

    print(f"Original detected people: {len(rects)}")

    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    people_pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

    print(f"Final detected people after NMS: {len(people_pick)}")

    return people_pick


def detect_cars(image, car_classifier):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    cars = car_classifier.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(50, 50)
    )

    print(f"Detected cars: {len(cars)}")

    return cars


# =========================
# 繪圖函式
# =========================

def draw_people(image, people):
    for (xA, yA, xB, yB) in people:
        cv2.rectangle(
            image,
            (xA, yA),
            (xB, yB),
            (0, 255, 0),
            2
        )

        cv2.putText(
            image,
            "Person",
            (xA, max(yA - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )


def draw_cars(image, cars):
    for (x, y, w, h) in cars:
        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (255, 0, 0),
            2
        )

        cv2.putText(
            image,
            "Car",
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )


# =========================
# 主程式
# =========================

def main():
    check_file(IMAGE_PATH, f"Error: 找不到圖片：{IMAGE_PATH}")
    check_file(CAR_XML_PATH, f"Error: 找不到車子偵測模型：{CAR_XML_PATH}")

    image = load_image(IMAGE_PATH)

    hog = create_people_detector()
    car_classifier = create_car_detector(CAR_XML_PATH)

    people = detect_people(image, hog)
    cars = detect_cars(image, car_classifier)

    draw_people(image, people)
    draw_cars(image, cars)

    cv2.imwrite(OUTPUT_PATH, image, [cv2.IMWRITE_JPEG_QUALITY, 98])

    print("Object detection done.")
    print(f"Output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()