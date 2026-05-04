from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QDoubleSpinBox, QCheckBox
)

class AffineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Affine Transform (Learning)")

        layout = QFormLayout(self)

        self.mode = QComboBox()
        self.mode.addItems(["translate", "rotate", "scale", "shear"])

        self.dx = QDoubleSpinBox()
        self.dx.setRange(-5000, 5000)
        self.dx.setDecimals(1)
        self.dx.setValue(0.0)

        self.dy = QDoubleSpinBox()
        self.dy.setRange(-5000, 5000)
        self.dy.setDecimals(1)
        self.dy.setValue(0.0)

        self.angle = QDoubleSpinBox()
        self.angle.setRange(-360.0, 360.0)
        self.angle.setDecimals(2)
        self.angle.setValue(0.0)

        self.sx = QDoubleSpinBox()
        self.sx.setRange(0.01, 10.0)
        self.sx.setDecimals(3)
        self.sx.setValue(1.0)

        self.sy = QDoubleSpinBox()
        self.sy.setRange(0.01, 10.0)
        self.sy.setDecimals(3)
        self.sy.setValue(1.0)

        self.shx = QDoubleSpinBox()
        self.shx.setRange(-5.0, 5.0)
        self.shx.setDecimals(3)
        self.shx.setValue(0.0)

        self.shy = QDoubleSpinBox()
        self.shy.setRange(-5.0, 5.0)
        self.shy.setDecimals(3)
        self.shy.setValue(0.0)

        self.transparent_bg = QCheckBox("Background transparent (Alpha = 0 outside)")
        self.transparent_bg.setChecked(True)

        layout.addRow("Mode", self.mode)
        layout.addRow("dx", self.dx)
        layout.addRow("dy", self.dy)
        layout.addRow("Angle (degrees)", self.angle)
        layout.addRow("Scale sx", self.sx)
        layout.addRow("Scale sy", self.sy)
        layout.addRow("Shear shx", self.shx)
        layout.addRow("Shear shy", self.shy)
        layout.addRow(self.transparent_bg)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # voliteľne: môžeš si tu spraviť enable/disable podľa mode
        self.mode.currentTextChanged.connect(self._update_enabled)
        self._update_enabled(self.mode.currentText())

    def _update_enabled(self, mode: str):
        is_translate = (mode == "translate")
        is_rotate = (mode == "rotate")
        is_scale = (mode == "scale")
        is_shear = (mode == "shear")

        self.dx.setEnabled(is_translate)
        self.dy.setEnabled(is_translate)

        self.angle.setEnabled(is_rotate)

        self.sx.setEnabled(is_scale)
        self.sy.setEnabled(is_scale)

        self.shx.setEnabled(is_shear)
        self.shy.setEnabled(is_shear)

    def params(self) -> dict:
        return {
            "mode": self.mode.currentText(),
            "dx": float(self.dx.value()),
            "dy": float(self.dy.value()),
            "angle_deg": float(self.angle.value()),
            "sx": float(self.sx.value()),
            "sy": float(self.sy.value()),
            "shx": float(self.shx.value()),
            "shy": float(self.shy.value()),
            "transparent_bg": bool(self.transparent_bg.isChecked()),
        }
