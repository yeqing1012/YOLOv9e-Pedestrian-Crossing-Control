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

        # 加载图片
        # self.img = Image.open("test.jpg")  # 这里替换成你的图片路径
        # self.img_tk = ImageTk.PhotoImage(self.img)
        self.img_tk = None
        # 创建Canvas来显示图片
        self.canvas = tk.Canvas(root)
        self.canvas.place(x=0, y=0, width=self.window_width // 2, height=self.window_height)

        # 将图片放到Canvas上
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

        # 初始化框选相关变量
        self.rects = [
            {"x1": 50, "y1": 50, "x2": 200, "y2": 150, "text": "Car"},
            {"x1": 100, "y1": 200, "x2": 250, "y2": 300, "text": "Person"},
            {"x1": 300, "y1": 100, "x2": 450, "y2": 200, "text": "Person"}
        ]

        # 为每个框和文字创建矩形和文本
        for rect in self.rects:
            rect["id"] = self.canvas.create_rectangle(rect["x1"], rect["y1"], rect["x2"], rect["y2"], outline="red",
                                                      width=2)
            rect["text_id"] = self.canvas.create_text(rect["x1"] + 5, rect["y1"] + 5, text=rect["text"], anchor=tk.NW,
                                                      font=("Arial", 14), fill="red")

        # 当前选中的框（用于拖动或调整大小）
        self.selected_rect = None
        self.selected_edge = None  # 选中哪一条边来调整大小
        self.mouse_x = None
        self.mouse_y = None

        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # -----------------------------------------------------------------------------------------------------------------

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

        self.label_text_countdown = tk.Label(self.root, text='Time:90s',
                                             font=("Arial", 24, "bold"))
        self.label_text_countdown.place(x=self.window_width // 2 + 550, y=int(self.window_height * 0.05))

    def box_x_y(self, h, w):
        zoom_w = w / (self.window_width // 2)  # w的缩放比例
        zoom_h = h / self.window_height  # h的缩放比例
        car_box = [self.rects[0]["x1"] * zoom_w, self.rects[0]["y1"] * zoom_h, self.rects[0]["x2"] * zoom_w,
                   self.rects[0]["y2"] * zoom_h]
        person1_box = [self.rects[1]["x1"] * zoom_w, self.rects[1]["y1"] * zoom_h, self.rects[1]["x2"] * zoom_w,
                       self.rects[1]["y2"] * zoom_h]

        person2_box = [self.rects[2]["x1"] * zoom_w, self.rects[2]["y1"] * zoom_h, self.rects[2]["x2"] * zoom_w,
                       self.rects[2]["y2"] * zoom_h]
        return car_box, person1_box, person2_box

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

            # 将图片转换成Tkinter支持的格式
            self.img_tk = ImageTk.PhotoImage(img)

            # 更新标签中的图片
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk
                                     )
            for rect in self.rects:
                rect["id"] = self.canvas.create_rectangle(rect["x1"], rect["y1"], rect["x2"], rect["y2"], outline="red",
                                                          width=2)
                rect["text_id"] = self.canvas.create_text(rect["x1"] + 5, rect["y1"] + 5, text=rect["text"],
                                                          anchor=tk.NW, font=("Arial", 14), fill="red")
            # self.image_label_yolo.image = img_tk  # 保持对图片的引用
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
        t = [i + 1 for i in range(1, 90)]
        t.reverse()
        for i in t:
            time.sleep(1)
            self.label_text_countdown['text'] = f'Time:{i + 1}'

        self.set_signal(1)  # 车辆通过

        t = [i + 1 for i in range(1, 60)]
        t.reverse()
        for i in t:
            time.sleep(1)
            self.label_text_countdown['text'] = f'Time:{i + 1}'
        self.set_signal(0)  # 车辆不通过
        state[0] = True

    def on_button_press(self, event):
        for rect in self.rects:
            # 检查是否点击了矩形框本身
            if rect["x1"] <= event.x <= rect["x2"] and rect["y1"] <= event.y <= rect["y2"]:
                # 判断是否点击了矩形的边缘进行大小调整
                if abs(event.x - rect["x1"]) < 5:  # 左边缘
                    self.selected_rect = rect
                    self.selected_edge = "left"
                elif abs(event.x - rect["x2"]) < 5:  # 右边缘
                    self.selected_rect = rect
                    self.selected_edge = "right"
                elif abs(event.y - rect["y1"]) < 5:  # 上边缘
                    self.selected_rect = rect
                    self.selected_edge = "top"
                elif abs(event.y - rect["y2"]) < 5:  # 下边缘
                    self.selected_rect = rect
                    self.selected_edge = "bottom"
                else:  # 点击矩形框内部，允许移动矩形
                    self.selected_rect = rect
                    self.mouse_x = event.x
                    self.mouse_y = event.y
                    self.selected_edge = None  # 不在边缘，进行拖动
                break

    def on_mouse_drag(self, event):
        if self.selected_rect:  # 拖动框
            if self.selected_edge:  # 调整大小
                if self.selected_edge == "left":
                    new_x1 = event.x
                    if new_x1 < self.selected_rect["x2"]:  # 防止超出右边界
                        self.canvas.coords(self.selected_rect["id"], new_x1, self.selected_rect["y1"],
                                           self.selected_rect["x2"], self.selected_rect["y2"])
                        self.canvas.coords(self.selected_rect["text_id"], new_x1 + 5, self.selected_rect["y1"] + 5)
                        self.selected_rect["x1"] = new_x1
                elif self.selected_edge == "right":
                    new_x2 = event.x
                    if new_x2 > self.selected_rect["x1"]:  # 防止超出左边界
                        self.canvas.coords(self.selected_rect["id"], self.selected_rect["x1"], self.selected_rect["y1"],
                                           new_x2, self.selected_rect["y2"])
                        self.canvas.coords(self.selected_rect["text_id"], self.selected_rect["x1"] + 5,
                                           self.selected_rect["y1"] + 5)
                        self.selected_rect["x2"] = new_x2
                elif self.selected_edge == "top":
                    new_y1 = event.y
                    if new_y1 < self.selected_rect["y2"]:  # 防止超出下边界
                        self.canvas.coords(self.selected_rect["id"], self.selected_rect["x1"], new_y1,
                                           self.selected_rect["x2"], self.selected_rect["y2"])
                        self.canvas.coords(self.selected_rect["text_id"], self.selected_rect["x1"] + 5, new_y1 + 5)
                        self.selected_rect["y1"] = new_y1
                elif self.selected_edge == "bottom":
                    new_y2 = event.y
                    if new_y2 > self.selected_rect["y1"]:  # 防止超出上边界
                        self.canvas.coords(self.selected_rect["id"], self.selected_rect["x1"], self.selected_rect["y1"],
                                           self.selected_rect["x2"], new_y2)
                        self.canvas.coords(self.selected_rect["text_id"], self.selected_rect["x1"] + 5,
                                           self.selected_rect["y1"] + 5)
                        self.selected_rect["y2"] = new_y2
            else:  # 拖动框本身
                delta_x = event.x - self.mouse_x
                delta_y = event.y - self.mouse_y
                # 更新矩形的坐标
                new_x1 = self.selected_rect["x1"] + delta_x
                new_y1 = self.selected_rect["y1"] + delta_y
                new_x2 = self.selected_rect["x2"] + delta_x
                new_y2 = self.selected_rect["y2"] + delta_y
                # 更新矩形和文字的位置
                self.canvas.coords(self.selected_rect["id"], new_x1, new_y1, new_x2, new_y2)
                self.canvas.coords(self.selected_rect["text_id"], new_x1 + 5, new_y1 + 5)
                # 更新矩形坐标
                self.selected_rect["x1"] = new_x1
                self.selected_rect["y1"] = new_y1
                self.selected_rect["x2"] = new_x2
                self.selected_rect["y2"] = new_y2

            self.mouse_x = event.x
            self.mouse_y = event.y

    def on_button_release(self, event):
        # 松开鼠标时，停止拖动或调整大小
        self.selected_rect = None
        self.selected_edge = None
        self.mouse_x = None
        self.mouse_y = None


def cv(app):
    state = [True]
    yolo = Yolo('yolo/mode_file/v9e_daytime_dy2024_030.pt')
    cap = cv2.VideoCapture(1)
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("无法打开摄像头")
        exit()
    while True:
        ret, frame = cap.read()

        if not ret:
            print("无法读取图像")
            exit()

        img_bit, box = yolo.cv(cv2.imencode('.jpg', frame)[1].tobytes(), app.box_x_y(*frame.shape[:2]))
        # 更新ui上目标检测效果图
        app.root.after(0, lambda: app.display_image(img_bit))
        app.label_text_car_number[  # 更新ui上人和车的数量
            'text'] = f'Car: {len(box[box["class"] != "person"])} Person: {len(box[box["class"] == "person"])}'
        if (not box.empty) and state[0]:  # 人车都没有就行人长绿
            if len(box[box['class'] != 'person']) > 3 and len(box[box['class'] == 'person']) < 10:  # 有车
                state[0] = False
                threading.Thread(target=app.count_down, args=(state,)).start()
            elif len(box[box['class'] != 'person']) > 0 and len(box[box['class'] == 'person']) < 1:
                state[0] = False
                threading.Thread(target=app.count_down, args=(state,)).start()
            elif len(box[box['class'] != 'person']) > 6:
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
