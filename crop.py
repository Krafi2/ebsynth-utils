import sys
import cv2 as cv
import numpy as np
import subprocess

def edge_detect(img):
    edges = img / np.repeat(np.linalg.norm(img, axis=-1), 3).reshape(np.shape(img)) * 255
    edges = edges.astype(np.uint8)
    green = cv.inRange(edges, (100, 180, 0), (200, 255, 80))
    bright_green = cv.inRange(img, (90, 150, 60), (200, 255, 150))
    edges = cv.bitwise_or(green, bright_green)
    return cv.Canny(edges, 150, 200, apertureSize = 3)


def absdiff(a, b):
    return np.abs(a - b)
    

def is_similar(theta1, theta2, r1, r2):
    # theta_eps = 0.3 * np.pi / 180
    # r_eps = 2
    theta_eps = 1 * np.pi / 180
    r_eps = 5

    return absdiff(theta1, theta2) < theta_eps and absdiff(r1, r2) < r_eps


# A poor outlier detection alg
def filter_lines(lines):
    lines.sort(key=lambda a: a[0])
    result = []

    for i in range(0, len(lines)):
        r1, theta1 = lines[i]

        if i > 0:
            r2, theta2  = lines[i - 1]
            if is_similar(theta1, theta2, r1, r2):
                result.append(lines[i])
                continue

        if i < len(lines) - 1:
            r2, theta2 = lines[i + 1]
            if is_similar(theta1, theta2, r1, r2):
                result.append(lines[i])
                continue

    return result

    
def hough_intersect_y(theta, r, y):
    c = np.cos(theta)
    s = np.sin(theta)
    return (r - y * s) / c
    

def hough_intersect_x(theta, r, x):
    c = np.cos(theta)
    s = np.sin(theta)
    return (r - x * c) / s


def detect_lines(img):
    horizontal = []
    vertical = []

    edges = edge_detect(img)
    lines = cv.HoughLines(edges, 1, np.pi/180/4, 180)

    if lines is None:
        lines = []

    # Filter out lines which arent vertical or horizontal
    for line in lines:
        eps = 5 * np.pi / 180
        _, theta = line[0]

        if theta > np.pi / 2:
            theta = np.pi - theta

        if theta < eps:
            vertical.append(line[0])

        elif theta > np.pi / 2 - eps:
            horizontal.append(line[0])

    return horizontal, vertical
    
    
def main():
    input = sys.argv[1]
    output = sys.argv[2]

    vertical = []
    horizontal = []

    vid = cv.VideoCapture(input, apiPreference=cv.CAP_FFMPEG)

    frames = int(vid.get(cv.CAP_PROP_FRAME_COUNT))
    width = int(vid.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    for i in range(frames):
        ok, img = vid.read()
        if not ok:
            print(f"Error while decoding frame {i}")
            continue

        if i % (frames // 4) == 0:
            v, h = detect_lines(img)
            vertical += v
            horizontal += h

    vertical = filter_lines(vertical)
    horizontal = filter_lines(horizontal)

    x1 = 0
    x2 = width
    y1 = 0
    y2 = height
    
    for r, theta in vertical:
        a = int(hough_intersect_y(theta, r, 0))
        b = int(hough_intersect_y(theta, r, height))
        for x in [a, b]:
            if x < width / 2:
                x1 = max(x1, x)
            else:
                x2 = min(x2, x)

    for r, theta in horizontal:
        a = int(hough_intersect_x(theta, r, x1))
        b = int(hough_intersect_x(theta, r, x2))
        for y in [a, b]:
            if y < height / 2:
                y1 = max(y1, y)
            else:
                y2 = min(y2, y)
                
    w = x2 - x1
    h = y2 - y1
    subprocess.run(["ffmpeg", "-i", input, "-filter:v", f"crop={w}:{h}:{x1}:{y1}", output])


if __name__ == "__main__":
    main()
