#!/usr/bin/env python3
"""
MediaPipe Flip Monitor
监控手部翻书动作：检测到手出现→消失后截取摄像头帧并发声提示，循环 N 次
依赖：mediapipe, opencv-python
"""
import cv2
import time
import argparse
import subprocess
from pathlib import Path
import mediapipe as mp

mp_hands = mp.solutions.hands


def play_sound():
    """播放系统提示音"""
    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])


def parse_args():
    parser = argparse.ArgumentParser(description='MediaPipe 翻书监控')
    parser.add_argument('--max-count', type=int, default=5, help='最大截图次数')
    parser.add_argument('--shots-dir', type=str, default='shots', help='截图保存目录')
    parser.add_argument('--min-detect-conf', type=float, default=0.5, help='检测置信度阈值')
    parser.add_argument('--min-track-conf', type=float, default=0.5, help='跟踪置信度阈值')
    return parser.parse_args()


def main():
    args = parse_args()
    shots_dir = Path(args.shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print('无法打开摄像头，请检查权限')
        return
    
    state = 0  # 0: WAIT_HAND, 1: HAND_ON
    count = 0
    print(f'启动翻书监控，目标截图 {args.max_count} 次，按 Ctrl+C 退出')

    with mp_hands.Hands(max_num_hands=1,
                       min_detection_confidence=args.min_detect_conf,
                       min_tracking_confidence=args.min_track_conf) as hands:
        try:
            while count < args.max_count:
                ret, frame = cap.read()
                if not ret:
                    break
                # 转RGB处理
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(img)
                has_hand = bool(results.multi_hand_landmarks)

                # 状态机
                if state == 0 and has_hand:
                    state = 1
                elif state == 1 and not has_hand:
                    # 手离开后延时2秒再截图
                    time.sleep(2)
                    ret2, frame2 = cap.read()
                    if not ret2:
                        frame2 = frame
                    count += 1
                    shot_path = shots_dir / f'shot_{count}.png'
                    cv2.imwrite(str(shot_path), frame2)
                    print(f'[{count}/{args.max_count}] 延时截图已保存: {shot_path}')
                    play_sound()
                    # 重置状态，等待下一次手部出现
                    state = 0
                # 显示实时画面并检测退出按键
                cv2.imshow('Flip Monitor', frame)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC 退出
                    print('用户按 ESC，退出监控')
                    break
                # 降低帧率
                time.sleep(0.05)
        except KeyboardInterrupt:
            print('手动终止')
    cap.release()
    cv2.destroyAllWindows()
    print(f'任务完成，共截图 {count} 次')


if __name__ == '__main__':
    main() 