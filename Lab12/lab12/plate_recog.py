import os
import cv2
import numpy as np
import time
import argparse


def get_largest_rect_contour(image):
    contours, _ = cv2.findContours(
        image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    rect_contour = None
    for c in contours:
        p = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * p, True)
        if len(approx) == 4:
            rect_contour = approx
            break

    if rect_contour is None:
        raise Exception("No rect found")
    return rect_contour


def get_ordered_rect_points(contour):
    # the order is, bottom-left, bottom-right, top-right, top-left
    rect = np.zeros((4, 2), dtype="float32")
    s = contour.sum(axis=2)
    rect[0] = contour[np.argmin(s)]
    rect[2] = contour[np.argmax(s)]
    diff = np.diff(contour, axis=2)
    rect[1] = contour[np.argmin(diff)]
    rect[3] = contour[np.argmax(diff)]
    return rect


def deskew(src_img, base_rect, skewed_rect):
    M = cv2.getPerspectiveTransform(skewed_rect, base_rect)
    dest_img = cv2.warpPerspective(
        src_img, M, (int(base_rect[2][0]), int(base_rect[2][1])))
    return dest_img


def get_n_largest_components(image, n):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        image, connectivity=8)

    areas = stats[:, cv2.CC_STAT_AREA]
    sorted_areas_indices = np.argsort(-areas)

    component_images = []
    component_image_x = []

    for i in range(1, n + 1):
        largest_component = sorted_areas_indices[i]

        x = stats[largest_component, cv2.CC_STAT_LEFT]
        y = stats[largest_component, cv2.CC_STAT_TOP]
        width = stats[largest_component, cv2.CC_STAT_WIDTH]
        height = stats[largest_component, cv2.CC_STAT_HEIGHT]

        component_image = np.zeros_like(image)
        component_image[labels == largest_component] = 255
        component_image = component_image[y:y+height, x:x+width]
        component_images.append(component_image)
        component_image_x.append(x)

    # Sort the components by x position
    component_images = [x for _, x in sorted(
        zip(component_image_x, component_images))]

    return component_images


def get_templates(dir_path):
    templates = {}
    for file in os.listdir(dir_path):
        if file.endswith(".jpg"):
            template_image = cv2.imread(os.path.join(dir_path, file), 0)
            filename = os.path.splitext(file)[0]
            templates[filename] = template_image
    # key: filename, value, template_image
    return templates


def draw_result(img, rect_contour, plate_str, output_path="result/plate_boarder_img.jpg"):
    res_img = img.copy()
    points = rect_contour.reshape(4, 2)
    h, w = res_img.shape[:2]

    # 1. 先畫綠色框
    cv2.drawContours(res_img, [rect_contour], -1, (0, 255, 0), 2)

    # 2. 再畫四個座標點與文字
    for i, (x, y) in enumerate(points):
        x = int(x)
        y = int(y)

        cv2.circle(res_img, (x, y), 4, (0, 0, 255), -1)

        label = f"P{i+1}:({x},{y})"

        text_x = x + 5
        text_y = y - 5

        if text_x > w - 120:
            text_x = x - 110

        if text_y < 15:
            text_y = y + 18

        if text_y > h - 10:
            text_y = y - 10

        cv2.putText(res_img, label,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (0, 0, 255), 1)

        print(f"P{i+1}: x={x}, y={y}")

    # 3. 畫車牌辨識結果
    cv2.putText(res_img, plate_str, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255, 0, 0), 2)

    # 4. 存到 result 資料夾
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, res_img)

    print(f"Saved {output_path}")

def print_runtime(start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time

    print("=" * 40)
    print(f"Program runtime: {elapsed_time:.4f} seconds")
    print("=" * 40)

def normalize_char_image(image, size=(18, 36)):
    # 統一轉成灰階
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 統一大小
    image = cv2.resize(image, size)

    # 統一二值化，降低亮度差異影響
    _, image = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return image

def rotate_image(image, angle):
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0
    )

    return rotated

def get_plate_str_improved(images, templates, logs=False):
    plate_str = ""

    angles = [-10, -5, 0, 5, 10]
    scales = [0.9, 1.0, 1.1]
    target_size = (18, 36)

    for idx, parts in enumerate(images):
        best_match = None
        best_match_value = -1

        part_img = normalize_char_image(parts, target_size)

        for key, template in templates.items():

            # 前 3 碼只允許英文字母
            if idx < 3 and not key.isalpha():
                continue

            # 後 4 碼只允許數字
            if idx >= 3 and not key.isdigit():
                continue

            template_img = normalize_char_image(template, target_size)

            for scale in scales:
                scaled_w = int(target_size[0] * scale)
                scaled_h = int(target_size[1] * scale)

                scaled_template = cv2.resize(template_img, (scaled_w, scaled_h))
                scaled_template = cv2.resize(scaled_template, target_size)

                for angle in angles:
                    rotated_template = rotate_image(scaled_template, angle)

                    result = cv2.matchTemplate(
                        part_img,
                        rotated_template,
                        cv2.TM_CCOEFF_NORMED
                    )

                    _, max_val, _, _ = cv2.minMaxLoc(result)

                    if max_val > best_match_value:
                        best_match = key
                        best_match_value = max_val

        plate_str += best_match

        if logs:
            print(f"char {idx+1}: best match: {best_match}, value: {best_match_value}")

    return plate_str

def main():

    start_time = time.time()

    parser = argparse.ArgumentParser()

    parser.add_argument("--image_path", type=str,
                        help="path to image file", default="img/plate1.jpg")
    parser.add_argument("--template_path", type=str,
                        help="path to template folder", default="template")
    parser.add_argument("--show_image", type=bool,
                        help="show image, Value: True or False", default=False)

    img = cv2.imread(parser.parse_args().image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    edge = cv2.Canny(filtered, 30, 200)

    rect_contour = get_largest_rect_contour(edge)

    ordered_rect_points = get_ordered_rect_points(rect_contour)

    plate_size_match = (int(320), int(150))
    base_plate_points = np.array([[0, 0], [plate_size_match[0], 0], [plate_size_match[0], plate_size_match[1]], [
        0, plate_size_match[1]]], dtype="float32")

    plate = deskew(gray, base_plate_points, ordered_rect_points)

    _, plate = cv2.threshold(
        plate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    plate = cv2.bitwise_not(plate)

    kernel = np.ones((3, 3), np.uint8)
    plate = cv2.erode(plate, kernel, iterations=1)
    plate = cv2.dilate(plate, kernel, iterations=1)

    num_of_digits = 7

    component_images = get_n_largest_components(plate, num_of_digits)

    template_size = (18, 36)

    for i in range(num_of_digits):
        component_images[i] = cv2.resize(component_images[i], template_size)

    templates = get_templates(parser.parse_args().template_path)
    
    plate_str = get_plate_str_improved(component_images, templates, logs=True)
    print(f"plate number: {plate_str}")

    #畫框和座標 
    draw_result(img, rect_contour, plate_str)

    #結束
    print_runtime(start_time)

    # cv2.waitKey(0)

if __name__ == "__main__":
    main()
