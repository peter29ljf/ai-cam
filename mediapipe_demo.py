#!/usr/bin/env python3
"""
MediaPipe Hands 实时示例
按 ESC 键退出
依赖：mediapipe, opencv-contrib-python
"""
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
if not cap.isOpened():
    print('无法打开摄像头，请检查权限')
    exit(1)

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:
    print('按 ESC 键退出')
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # 转 RGB 并处理
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        # 绘制手部关键点
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, handLms, mp_hands.HAND_CONNECTIONS)
        cv2.imshow('MediaPipe Hands Demo', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows() 