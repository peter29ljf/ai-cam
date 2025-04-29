#!/usr/bin/env python3
"""
手部检测测试脚本
测试 HandDetector 类的功能
"""
import cv2
import numpy as np
from hand_detection import HandDetector

def test_hand_detector():
    """测试 HandDetector 类"""
    # 初始化检测器
    detector = HandDetector()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    print("手部检测测试开始，按 ESC 退出...")
    while True:
        # 读取一帧
        ret, frame = cap.read()
        if not ret:
            break
        
        # 处理图像
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        processed_frame, has_hand = detector.process_image(frame, draw=True)
        
        # 显示状态
        status = "检测到手" if has_hand else "未检测到手"
        cv2.putText(processed_frame, status, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 显示图像
        cv2.imshow("Hand Detection Test", processed_frame)
        
        # 按 ESC 键退出
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("测试结束")

if __name__ == "__main__":
    test_hand_detector() 