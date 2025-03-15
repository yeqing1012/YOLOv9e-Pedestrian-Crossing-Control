import sys

sys.path.append(r'yolo')
import torch
import warnings
from models.common import DetectMultiBackend
from utils.general import check_img_size, cv2, non_max_suppression
import numpy as np
from utils.torch_utils import select_device
from utils.augmentations import letterbox
import pandas as pd

warnings.filterwarnings("ignore")


class Yolo(object):

    def __init__(self, weights='', imgsz=1280, conf=0.5, iou=0.45):
        self.weights = weights  # 模型路径或 Triton URL
        self.imgsz = (imgsz, imgsz)  # 推理图片尺寸 (高, 宽)
        self.conf_thres = conf  # 置信度阈值
        self.iou_thres = iou  # 非极大值抑制（NMS）的 IOU 阈值
        self.max_det = 1000  # 每张图片的最大检测数
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.classes = None  # 根据类过滤结果：--class 0 或 --class 0 2 3
        self.agnostic_nms = False  # 是否使用类无关的 NMS
        self.augment = False  # 是否使用增强推理
        self.visualize = False  # 是否可视化特征
        self.half = False  # 是否使用 FP16 半精度推理
        self.dnn = False  # 是否使用 OpenCV DNN 进行 ONNX 推理
        self.vid_stride = 1  # 视频帧率步长

        self.model = self.load_mode()
        self.stride, names, self.pt = self.model.stride, self.model.names, self.model.pt  # 获取模型步长、类别名和是否为 PyTorch 模型

        self.img_size = check_img_size(self.imgsz, s=self.stride)  # 检查并调整图像大小

    def load_mode(self):
        # 加载模型
        device = select_device(self.device)
        model = DetectMultiBackend(self.weights, device=device, dnn=self.dnn, fp16=self.half)  # 加载模型
        return model

    def filter_detections_by_area(self, detections, area, car):
        """
        过滤掉不在指定区域内的框。
        :param car:
        :param detections: 检测框的结果，格式为 [x1, y1, x2, y2, confidence, class_id]
        :param area: 目标区域，格式为 [x1, y1, x2, y2]
        :return: 匹配目标区域的检测框列表
        """
        filtered_detections = []
        area_x1, area_y1, area_x2, area_y2 = area  # 目标区域的坐标
        for det in detections:
            # print(det)
            x1, y1, x2, y2, confidence, class_id = det  # 解析检测框的坐标和其他信息
            if not (x2 < area_x1 or x1 > area_x2 or y2 < area_y1 or y1 > area_y2):
                # 如果检测框和目标区域有重叠，保留该框
                if car:
                    if class_id != 0.0:
                        filtered_detections.append(det)
                else:
                    if class_id == 0.0:
                        filtered_detections.append(det)
        return filtered_detections

    def cv(self, img_bit, box):
        # 加载数据
        cv2_img = cv2.imdecode(np.frombuffer(img_bit, np.uint8), cv2.IMREAD_COLOR)
        im, ratio, _ = letterbox(cv2_img, self.img_size, stride=self.stride)  # padded resize
        im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        im = np.ascontiguousarray(im)  # contiguous

        self.model.warmup(imgsz=(1 if self.pt or self.model.triton else 1, 3, *self.imgsz))

        im = torch.from_numpy(im).to(self.model.device)
        im = im.half() if self.model.fp16 else im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]
        # 推理过程
        pred = self.model(im, augment=self.augment, visualize=self.visualize)  # 进行推理
        pred = pred[0][1]  # 提取预测结果

        # 非极大值抑制（NMS）
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, self.classes, self.agnostic_nms,
                                   max_det=self.max_det)  # NMS 操作
        for det in pred:  # 每张图片的预测结果
            if len(det):
                det[:, [0, 2]] = det[:, [0, 2]] / ratio[0]  # 还原x框的尺寸
                det[:, [1, 3]] = det[:, [1, 3]] / ratio[1]  # 还原y框的尺寸
        pred = pred[0].cpu().numpy().tolist()
        car_b = self.filter_detections_by_area(pred, box[0], True)
        person1_b = self.filter_detections_by_area(pred, box[1], False)
        person2_b = self.filter_detections_by_area(pred, box[2], False)
        pred = car_b + person1_b + person2_b
        # 画框
        for det in pred:  # 每张图片的预测结果
            # 在图像上画框
            x1, y1, x2, y2, conf, cls = det
            label = f'{self.model.names[int(cls)]} {conf:.2f}'
            self.plot_one_box(x1, y1, x2, y2, cv2_img, label=label, color=(0, 255, 0), line_thickness=1)
        return cv2.imencode('.jpg', cv2_img)[1].tobytes(), self.pred_to_dataframe(pred, self.model)

    @staticmethod
    def pred_to_dataframe(pred, model):
        # 存储每个检测框的结果
        results = []

        # 遍历每一张图片的预测结果
        for det in pred:  # pred 是一个包含多个检测框的列表
            if len(det):
                x1, y1, x2, y2, conf, cls = det
                # 获取坐标、置信度和类别
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                label = model.names[int(cls)]  # 获取标签
                results.append([x1, y1, x2, y2, conf, label])  # 将数据添加到结果列表
        print(results)
        # 将结果转换为 DataFrame
        df = pd.DataFrame(results, columns=["x1", "y1", "x2", "y2", "confidence", "class"])

        return df

    @staticmethod
    def plot_one_box(x1, y1, x2, y2, im0, color=(0, 255, 0), label=None, line_thickness=1):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        if label.split(' ')[0] == 'person':
            cv2.rectangle(im0, (x1, y1), (x2, y2), (255, 255, 0), thickness=line_thickness)
            if label:
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(im0, label, (x1, y1 - 5), font, 1, (255, 255, 0), 1, cv2.LINE_AA)
        else:
            cv2.rectangle(im0, (x1, y1), (x2, y2), (0, 255, 0), thickness=line_thickness)
            if label:
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(im0, label, (x1, y1 - 5), font, 1, (0, 255, 0), 1, cv2.LINE_AA)
