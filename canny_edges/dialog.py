from krita import Krita
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QDialogButtonBox,
    QCheckBox, QLabel
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

from .canny_helpers import *

class CannyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Canny Edge Detection")

        self._src_qimage_buf = None
        self._out_qimage_buf = None

        layout = QFormLayout(self)

        self.blur_size = QSpinBox()
        self.blur_size.setRange(3, 31)
        self.blur_size.setSingleStep(2)
        self.blur_size.setValue(5)

        self.sigma = QDoubleSpinBox()
        self.sigma.setRange(0.1, 10.0)
        self.sigma.setDecimals(2)
        self.sigma.setValue(1.40)

        self.high_ratio = QDoubleSpinBox()
        self.high_ratio.setRange(0.01, 1.0)
        self.high_ratio.setDecimals(2)
        self.high_ratio.setValue(0.20)

        self.low_ratio = QDoubleSpinBox()
        self.low_ratio.setRange(0.01, 1.0)
        self.low_ratio.setDecimals(2)
        self.low_ratio.setValue(0.50)

        self.preview = QLabel("Preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(360, 360)

        layout.addRow("Gaussian kernel size", self.blur_size)
        layout.addRow("Gaussian sigma", self.sigma)
        layout.addRow("High threshold ratio", self.high_ratio)
        layout.addRow("Low ratio", self.low_ratio)
        layout.addRow("Preview", self.preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.update_preview)

        def schedule():
            self._timer.start(150)

        self.blur_size.valueChanged.connect(schedule)
        self.sigma.valueChanged.connect(schedule)
        self.high_ratio.valueChanged.connect(schedule)
        self.low_ratio.valueChanged.connect(schedule)

        schedule()

    def params(self) -> dict:
        return {
            "kernel_size": int(self.blur_size.value()),
            "sigma": float(self.sigma.value()),
            "high_ratio": float(self.high_ratio.value()),
            "low_ratio": float(self.low_ratio.value()),
        }

    def update_preview(self):
        
        app = Krita.instance()
        doc = app.activeDocument()
        
        if doc is None:
            self.preview.setText("No active document.")
            return
        
        node = doc.activeNode()

        if node is None:
            self.preview.setText("No active layer.")
            return

        W, H = doc.width(), doc.height()
        params = self.params()

        byte_array = node.pixelData(0, 0, W, H)

        src_bytes = bytes(byte_array)

        self._src_qimage_buf = src_bytes
        img = QImage(self._src_qimage_buf, W, H, 4 * W, QImage.Format_ARGB32)

        max_side = max(64, min(self.preview.width(), self.preview.height()))
        img_small = img.scaled(max_side, max_side, Qt.KeepAspectRatio, Qt.FastTransformation)

        ptr = img_small.bits()
        ptr.setsize(img_small.byteCount())
        small_bytes = bytes(ptr)
        sw, sh = img_small.width(), img_small.height()

        gray = to_gray(small_bytes, sw, sh)
        gk = gaussian_kernel(params['kernel_size'], params['sigma'])
        blurred = convolve(gray, gk)
        mag, ang = sobel(blurred)
        nms = non_max_suppression(mag, ang)
        edges = double_threshold_and_hysteresis(nms, low_ratio=params['low_ratio'], high_ratio=params['high_ratio'])
        out_bytes = edges_to_BGRA(edges)

        self._out_qimage_buf = out_bytes
        out_img = QImage(self._out_qimage_buf, sw, sh, 4 * sw, QImage.Format_ARGB32)
        pix = QPixmap.fromImage(out_img)
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.FastTransformation))