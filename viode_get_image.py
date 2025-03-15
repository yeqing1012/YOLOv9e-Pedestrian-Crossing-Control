import cv2
import os

# 输入视频路径
video_path = r'D:/Senior2/test.mp4'
# 设置保存图片的文件夹路径
output_folder = 'frames_output'

# 如果文件夹不存在，则创建
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 打开视频文件
cap = cv2.VideoCapture(video_path)

# 获取视频的帧率
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps * 3)  # 2秒抽一帧

frame_count = 0  # 帧的计数器
saved_count = 0  # 保存的帧计数器

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 每隔2秒抽取一帧
    if frame_count % frame_interval == 0:
        # 保存帧
        frame_filename = os.path.join(output_folder, f'frame_{saved_count + 1}_1.jpg')
        cv2.imwrite(frame_filename, frame)
        saved_count += 1

    frame_count += 1

# 释放视频捕捉对象
cap.release()

print(f"抽取完成，共保存了 {saved_count} 张帧。")
