from ultralytics import YOLO
import cv2
import math
import shutil
import time
import os
import sqlite3
from datetime import datetime


class ProcVideo:
    def __init__(self):
        self.right_wrist = 10
        self.left_wrist = 9
        self.right_elbow = 8
        self.left_elbow = 7
        self.right_shoulder = 6
        self.left_shoulder = 5
        self.nose = 0
        self.model = YOLO('yolov8s-pose.pt')
        self.model2 = YOLO(f'v8s.pt')

    def cos_angle(self, shoulder, elbow, wrist):
        if shoulder[0] == 0 or elbow[0] == 0 or wrist[0] == 0:
            return 0
        dx_a = shoulder[0] - elbow[0]
        dy_a = shoulder[1] - elbow[1]
        dx_b = wrist[0] - elbow[0]
        dy_b = wrist[1] - elbow[1]

        dot_product = dx_a * dx_b + dy_a * dy_b

        length_a = math.sqrt(dx_a ** 2 + dy_a ** 2)
        length_b = math.sqrt(dx_b ** 2 + dy_b ** 2)

        return dot_product / (length_a * length_b)

    def elbow_flexion_detect(self, skeletons, boxes):
        elbow_flexion = []
        if skeletons.shape == (1, 0, 2):
            return elbow_flexion
        for i in range(len(skeletons)):
            cos_l = self.cos_angle(skeletons[i][self.left_shoulder],
                              skeletons[i][self.left_elbow],
                              skeletons[i][self.left_wrist])
            cos_r = self.cos_angle(skeletons[i][self.right_shoulder],
                              skeletons[i][self.right_elbow],
                              skeletons[i][self.right_wrist])
            if 0.5 <= cos_l < 1:
                elbow_flexion.append([int(boxes[i].xyxy[0][0]),  # x_min
                                      skeletons[i][self.left_wrist][1],  # y_min
                                      int(boxes[i].xyxy[0][2]),  # x_max
                                      skeletons[i][self.nose][1]])       # y_max
            if 0.5 <= cos_r < 1:
                elbow_flexion.append([int(boxes[i].xyxy[0][0]),  # x_min
                                      skeletons[i][self.right_wrist][1],  # y_min
                                      int(boxes[i].xyxy[0][2]),  # x_max
                                      skeletons[i][self.nose][1]])       # y_max
        return elbow_flexion

    def cigarettes_boxes(self, width, height, source):
        bounding_boxes = []
        labels_path = "runs/detect/predict/labels/" + source.split('.')[0] + ".txt"
        try:
            with open(labels_path, "r") as file:
                lines = file.readlines()
            for line in lines:
                parts = line.strip().split()
                bounding_boxes.append((float(parts[1]) * width,    # x_min
                                       float(parts[2]) * height,   # y_min
                                       float(parts[3]) * width,    # width
                                       float(parts[4]) * height))  # height
        except:
            pass
        return bounding_boxes

    def crossing(self, man, cigarette):
        centre_x = cigarette[0] + cigarette[2] / 2
        centre_y = cigarette[1] + cigarette[3] / 2
        if (man[0] <= centre_x <= man[2]) and (man[3] <= centre_y <= man[1]):
            print("cross")
            return True
        else:
            return False

    def smoking_recognition(self, elbow_flexion, cigarettes_bounds):
        smoking = []
        for man in elbow_flexion:
            for cigarette in cigarettes_bounds:
                if self.crossing(man, cigarette):
                    smoking.append(man)
                    break
        return smoking

    def save_image(self, image, camera_id):
        if not os.path.exists('detected'):
            os.makedirs('detected')

        cam_folder = f'detected/cam_{camera_id}'
        if not os.path.exists(cam_folder):
            os.makedirs(cam_folder)

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'{current_time}.jpg'

        index = 0
        while os.path.exists(os.path.join(cam_folder, filename)):
            index += 1
            filename = f'{current_time}_{index}.jpg'

        cv2.imwrite(os.path.join(cam_folder, filename), image)
        height, width, _ = image.shape
        print(height, width)

        return os.path.join(cam_folder, filename)

    def add_record_to_database(self, camera_id, image_path):
        conn = sqlite3.connect('smoking_pics.db')
        cursor = conn.cursor()

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        cursor.execute('''INSERT INTO фотографии (id_camera, date, time, path) VALUES (?, ?, ?, ?)''',
                       (camera_id, current_date, current_time, image_path))

        conn.commit()
        conn.close()

    def paint(self, im1, smoking, cigarettes_bounds, results):
        image = results[0].plot()
        for behaviour in smoking:
            x_min, y_min, x_max, y_max = [int(coord) for coord in behaviour]
            purple_color = (255, 0, 255)  # фиолетовый
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), purple_color, 2)  # 2 пикселя
            cv2.rectangle(im1, (x_min, y_min), (x_max, y_max), purple_color, 2)
        for box in cigarettes_bounds:
            x_min, y_min, width, height = [int(coord) for coord in box]
            green_color = (0, 255, 0)
            cv2.rectangle(image, (x_min, y_min), (x_min + width, y_min + height), green_color, 2)
        if len(smoking) > 0:
            print("smoking")
            path = self.save_image(im1, 0)
            self.add_record_to_database(0, path)

        return image

    def frame(self, source):
        if os.path.exists('runs/detect/predict'):
            shutil.rmtree('runs/detect/predict')
        if os.path.exists('runs/detect/predict2'):
            shutil.rmtree('runs/detect/predict2')
        results = self.model(source, conf=0.5, save=False)
        people = results[0].keypoints.xy.cpu().numpy()
        boxes = results[0].boxes
        elbow_flexion = self.elbow_flexion_detect(people, boxes)
        if len(elbow_flexion) > 0:
            print("elbow")

        self.model2.predict(source=source, conf=0.3, save=False, save_txt=True)

        image = cv2.imread(source)
        height, width, _ = image.shape
        cigarettes_bounds = self.cigarettes_boxes(width, height, source)
        if len(cigarettes_bounds) > 0:
            print("cigarette")
        smoking = self.smoking_recognition(elbow_flexion, cigarettes_bounds)

        return self.paint(image, smoking, cigarettes_bounds, results)

    def videofun(self):
        cap = cv2.VideoCapture(0)
        while True:
            _, kadr = cap.read()
            cv2.imwrite("frame.jpg", kadr)
            start_time = time.time()
            res = self.frame("frame.jpg")
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Время выполнения функции: {execution_time} секунд")
            cv2.imshow("cam", res)

            if cv2.waitKey(30) == ord('q'):
                break


if __name__ == "__main__":
    procv = ProcVideo()
    procv.videofun()
