import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
import cv2
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from keras.preprocessing import image
import tensorflow as tf

class MainWindow(object):
    def __init__(self):
        self.models = ["Model1.h5", "Model2.h5"]
        self.model_i = 0
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(580, 650)

        font = QtGui.QFont()
        font.setPointSize(16)

        self.Camera = QtWidgets.QLabel(Dialog)
        self.Camera.setGeometry(QtCore.QRect(50, 50, 480, 480))

        self.Predict = QtWidgets.QPushButton(parent=Dialog)
        self.Predict.setGeometry(QtCore.QRect(50, 540, 101, 41))
        self.Predict.setText("Predict")
        self.Predict.clicked.connect(self.predict)

        self.Swap = QtWidgets.QPushButton(parent=Dialog)
        self.Swap.setGeometry(QtCore.QRect(50, 590, 101, 41))
        self.Swap.setText("swap model")
        self.Swap.clicked.connect(self.swap_model)

        self.Label = QtWidgets.QLabel(Dialog)
        self.Label.setGeometry(QtCore.QRect(160, 540, 500, 41))
        self.Label.setFont(font)
        self.Label.setText("Predicted: Nan")

        self.SwapLabel = QtWidgets.QLabel(Dialog)
        self.SwapLabel.setGeometry(QtCore.QRect(160, 590, 500, 41))
        self.SwapLabel.setFont(font)
        self.SwapLabel.setText(f"{self.models[self.model_i]}")

        self.CaptureVideo = cv2.VideoCapture(0)
        self.timer_object = QtCore.QObject()
        self.timer = QTimer(self.timer_object)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)

    def update_frame(self):
        ret, frame = self.CaptureVideo.read()
        if ret:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, 480, 480, bytes_per_line, QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img)
            self.Camera.setPixmap(pixmap)

    def predict(self):
        # Chụp ảnh từ QLabel và lưu lại
        result_text = ["Không có khẩu trang", "Có khẩu trang"]
        pixmap = self.Camera.pixmap()
        if pixmap:
            img = pixmap.toImage().save("a.jpg")
            result_value = result(self.models[self.model_i])
            self.Label.setText("Predicted Class: " + result_text[result_value])
    
    def swap_model(self):
        self.model_i = (self.model_i + 1) % len(self.models)
        self.model = self.models[self.model_i]
        self.SwapLabel.setText(f"{self.model}")

def result(model_name):
    color_image = cv2.imread('a.jpg')
    resized_image = cv2.resize(color_image, (100, 100))
    img = image.img_to_array(resized_image)
    img = np.expand_dims(img, axis=0)
    img = img / 255
    model = tf.keras.models.load_model(model_name)
    predictions = model.predict(img)
    predicted_class = np.argmax(predictions, axis=1)
    return predicted_class[0]

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = MainWindow()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec())