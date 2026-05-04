from krita import Krita, Extension
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import QByteArray

from .dialog import AffineDialog
from .affine_helpers import build_affine_matrix, apply_affine_bgra_u8

class AffineTransform(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "affine_transform",
            "Affine Transform",
            "tools/scripts"
        )
        action.triggered.connect(self.action_triggered)

    def action_triggered(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            QMessageBox.information(None, "Affine Transform", "No active document.")
            return

        node = doc.activeNode()
        if node is None:
            QMessageBox.information(None, "Affine Transform", "No active layer.")
            return

        # learning: len RGBA/U8 (RGBA (Red, Green, Blue, Alpha), U8 (unsigned 8-bit))
        if node.colorModel() != "RGBA" or node.colorDepth() != "U8":
            QMessageBox.warning(
                None, "Affine Transform",
                "This learning plugin supports only RGBA + U8 (8-bit) layers."
            )
            return

        dlg = AffineDialog()
        if dlg.exec_() != QDialog.Accepted:
            return

        p = dlg.params()
        w = doc.width()
        h = doc.height()

        try:
            # iba 1 vrstva: pixelData (nie projectionPixelData)
            ba = node.pixelData(0, 0, w, h)
            src_bytes = bytes(ba)

            a, b, tx, c, d, ty = build_affine_matrix(
                mode=p["mode"],
                w=w, h=h,
                dx=p["dx"], dy=p["dy"],
                angle_deg=p["angle_deg"],
                sx=p["sx"], sy=p["sy"],
                shx=p["shx"], shy=p["shy"]
            )

            out_bytes = apply_affine_bgra_u8(
                src_bytes=src_bytes,
                w=w, h=h,
                a=a, b=b, tx=tx,
                c=c, d=d, ty=ty,
                background_transparent=p["transparent_bg"]
            )

            out_node = doc.createNode("Affine Result", "paintlayer")

            parent = node.parentNode()
            if parent is None:
                parent = doc.rootNode()

            added = parent.addChildNode(out_node, node)
            if not added:
                QMessageBox.critical(None, "Affine Transform", "Failed to add output layer.")
                return

            # pozor: niektoré verzie vracajú None (nie bool); kontroluj len explicitné False
            ret = out_node.setPixelData(QByteArray(out_bytes), 0, 0, w, h)
            if ret is False:
                QMessageBox.critical(None, "Affine Transform", "setPixelData returned False.")
                return

            doc.setActiveNode(out_node)
            doc.refreshProjection()
            doc.waitForDone()

        except Exception as e:
            QMessageBox.critical(None, "Affine Transform", f"Error: {e}")
