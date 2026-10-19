import cv2
import imutils
import argparse

ASCII_CHARS = ' .:-=+*#%@'
' .:-=+*#%@'
def resize_image(image, new_width=80):
    (height, width) = image.shape[:2]
    aspect_ratio = height / float(width)
    new_height = int(aspect_ratio * new_width)
    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image

def convert_to_ascii(image):
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ascii_str = ''
    for row in grayscale_image:
        for pixel in row:
            ascii_str += ASCII_CHARS[pixel // 30]
        ascii_str += '\n'
    return ascii_str

parser = argparse.ArgumentParser()

parser.add_argument('--image', help='path to image file', default='img/Lenna.png')

path = parser.parse_args().image

image = cv2.imread(path)

resized_image = resize_image(image)

ascii_art = convert_to_ascii(resized_image)

print(ascii_art)
