from yolo.detect import Yolo
import io
import tkinter as tk
from PIL import Image, ImageTk
import threading
import cv2
import time


class ImageDisplayUI:
    def __init__(self, root):
        # 创建主窗口
        self.root = root
        self.root.title("SP2")

        # 固定窗口尺寸，16:18的比例，宽度640
        self.window_height = 400
        self.window_width = int(self.window_height * 16 / 9) * 2

        # 获取屏幕的宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 计算窗口的起始位置，使其居中
        position_top = (screen_height // 2) - (self.window_height // 2)
        position_left = (screen_width // 2) - (self.window_width // 2)

        # 设置窗口的大小和位置
        self.root.geometry(f"{self.window_width}x{self.window_height}+{position_left}+{position_top}")

        # 禁止缩放
        self.root.resizable(False, False)

        # 初始化实时展示目标检测效果的展示标签
        self.image_label_yolo = tk.Label(self.root, bg="lightgray")
        self.image_label_yolo.place(x=0, y=0, width=self.window_width // 2, height=self.window_height)

        # 初始化模拟交通信号动画底图
        self.image_label1 = tk.Label(self.root, bg='#d3d3d3')
        self.image_label1.place(x=self.window_width // 2, y=int(self.window_height * 0.2), width=self.window_width // 2,
                                height=self.window_height * 0.8)
        # 设置车辆通行底图
        img_main_c = Image.open('static/img/main_c.jpg')
        img_main_c = img_main_c.resize((self.window_width // 2, int(self.window_height * 0.8)),
                                       Image.Resampling.LANCZOS)
        self.img_tk_c = ImageTk.PhotoImage(img_main_c)

        # 设置行人同行底图
        img_main_p = Image.open('static/img/main_p.jpg')
        img_main_p = img_main_p.resize((self.window_width // 2, int(self.window_height * 0.8)),
                                       Image.Resampling.LANCZOS)
        self.img_tk_p = ImageTk.PhotoImage(img_main_p)
        self.set_signal()

        # 设置车辆数量
        self.label_text_car_number = tk.Label(self.root, text='Car:0',
                                              font=("Arial", 24, "bold"))
        self.label_text_car_number.place(x=self.window_width // 2, y=int(self.window_height * 0.05))

        self.label_text_countdown = tk.Label(self.root, text='Vehicle traffic light countdown:10s',
                                             font=("Arial", 24, "bold"))
        self.label_text_countdown.place(x=self.window_width // 2 + 150, y=int(self.window_height * 0.05))

    def display_image(self, img_bytes):
        """
        展示图片
        :param img_bytes: 传入图片的字节流数据
        """
        try:
            # 将字节流转换成Image对象
            img = Image.open(io.BytesIO(img_bytes))

            # 获取上半部分的尺寸
            top_width = self.window_width // 2
            top_height = self.window_height

            # 调整图片尺寸，铺满上半部分
            img = img.resize((top_width, top_height), Image.Resampling.LANCZOS)
            print(top_width, top_height)

            # 将图片转换成Tkinter支持的格式
            img_tk = ImageTk.PhotoImage(img)

            # 更新标签中的图片
            self.image_label_yolo.config(image=img_tk)
            self.image_label_yolo.image = img_tk  # 保持对图片的引用
        except Exception as e:
            print(f"加载图片时发生错误: {e}")

    def set_signal(self, state=0):
        if state == 0:
            self.image_label1.config(image=self.img_tk_p)
            self.image_label1.image = self.img_tk_p
        else:
            self.image_label1.config(image=self.img_tk_c)
            self.image_label1.image = self.img_tk_c

    def count_down(self, state):
        t = [i + 1 for i in range(1, 30)]
        t.reverse()
        for i in t:
            time.sleep(1)
            self.label_text_countdown['text'] = f'Vehicle traffic light countdown:{i + 1}'

        self.set_signal(1)  # 车辆通过

        t = [i + 1 for i in range(1, 60)]
        t.reverse()
        for i in t:
            time.sleep(1)
            self.label_text_countdown['text'] = f'Vehicle traffic light countdown:{i + 1}'
        self.set_signal(0)  # 车辆不通过
        state[0] = True


def cv(app):
    state = [True]
    yolo = Yolo('yolo/mode_file/v9e_daytime_dy2024_030.pt')
    while True:
        cap = cv2.VideoCapture(input('输入视频地址：'))
        # 检查摄像头是否成功打开
        if not cap.isOpened():
            print("无法打开视频")
        else:
            break
    while True:
        ret, frame = cap.read()

        if not ret:
            print("无法读取图像")
            exit()
        img_bit, box = yolo.cv(cv2.imencode('.jpg', frame)[1].tobytes())
        app.display_image(img_bit)
        box = box[box['class'] != 'person']
        app.label_text_car_number['text'] = f'Car:{len(box)}'

        if len(box) != 0 and state[0]:  # 有车
            state[0] = False
            threading.Thread(target=app.count_down, args=(state,)).start()


def main():
    # 创建根窗口
    root = tk.Tk()

    # 创建UI实例
    app = ImageDisplayUI(root)

    t = threading.Thread(target=cv, daemon=True, args=(app,))
    t.start()
    # 运行主循环
    root.mainloop()


if __name__ == '__main__':
    main()
