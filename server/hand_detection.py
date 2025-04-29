#!/usr/bin/env python3
"""
手部检测模块
使用 MediaPipe 实现手部检测
"""
import cv2
import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, 
                 max_num_hands=1, 
                 min_detection_confidence=0.5, 
                 min_tracking_confidence=0.5):
        """
        初始化手部检测器
        
        参数:
            max_num_hands: 最大检测手数量
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小跟踪置信度
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            static_image_mode=False
        )
        
    def detect(self, image):
        """
        检测图像中是否存在手
        
        参数:
            image: RGB格式图像
            
        返回:
            bool: 是否检测到手
        """
        # 处理图像
        results = self.hands.process(image)
        
        # 检查是否有手部关键点
        return bool(results.multi_hand_landmarks)
    
    def process_image(self, image, draw=True):
        """
        处理图像，检测手部并可选择绘制标记
        
        参数:
            image: RGB格式图像
            draw: 是否在图像上绘制手部关键点
            
        返回:
            processed_image: 处理后的图像（如果draw=True）
            has_hand: 是否检测到手
        """
        # 转换为RGB处理
        if image.shape[2] == 3 and image.dtype == np.uint8:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
            
        # 处理图像
        results = self.hands.process(rgb_image)
        
        # 检查是否有手部关键点
        has_hand = bool(results.multi_hand_landmarks)
        
        # 绘制手部关键点
        if draw and has_hand:
            mp_drawing = mp.solutions.drawing_utils
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        return image, has_hand
    
    def __del__(self):
        """释放资源"""
        self.hands.close() 