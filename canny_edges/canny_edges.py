from krita import Krita, Extension

from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import QByteArray

from .dialog import CannyDialog
from .canny_helpers import *

class CannyEdgesExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "canny_edge_detector",
            "Canny Edge Detector",
            "tools/scripts"
        )
        action.triggered.connect(self.action_triggered)

    def action_triggered(self):
        app = Krita.instance()
        doc = app.activeDocument()
        
        if doc is None:
            QMessageBox.information(None, "Canny Edge Detector", "No active document.")
            return

        node = doc.activeNode()
        if node is None:
            QMessageBox.information(None, "Canny Edge Detector", "No active layer.")
            return

        dialog = CannyDialog()
        if dialog.exec_() != QDialog.Accepted:
            return

        params = dialog.params()

        width = doc.width()
        height = doc.height()

        try:

            ba = node.pixelData(0, 0, width, height)

            src_bytes = bytes(ba)

            gray = to_gray(src_bytes, width, height)
            gk = gaussian_kernel(params['kernel_size'], params['sigma'])
            blurred = convolve(gray, gk)
            mag, ang = sobel(blurred)
            nms = non_max_suppression(mag, ang)
            edges = double_threshold_and_hysteresis(nms, low_ratio=params['low_ratio'], high_ratio=params['high_ratio'])
            out_bytes = edges_to_BGRA(edges)

            # create output layer
            out_node = doc.createNode("Canny Edges", "canny")

            parent = node.parentNode()
            if parent is None:
                parent = doc.rootNode()

            added = parent.addChildNode(out_node, node)
            if not added:
                QMessageBox.critical(None, "Canny Edge Detector", 
                    "failed to add output layer"
                    )
                return

            ret = out_node.setPixelData(QByteArray(out_bytes), 0, 0, width, height)

            if ret is False:
                QMessageBox.critical(None, "Canny Edge Detector",
                    "setPixelData failed"
                )
                return

            doc.setActiveNode(out_node)
            doc.refreshProjection()
            doc.waitForDone()

        except Exception as e:
            QMessageBox.critical(None, "Canny Edge Detector", f"Error: {e}")