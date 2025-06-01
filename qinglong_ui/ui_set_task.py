# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'set_task.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_setTask(object):
    def setupUi(self, setTask):
        if not setTask.objectName():
            setTask.setObjectName("setTask")
        setTask.resize(423, 197)
        self.verticalLayout = QVBoxLayout(setTask)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_3 = QLabel(setTask)
        self.label_3.setObjectName("label_3")
        self.label_3.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_4.addWidget(self.label_3)

        self.nameEdit = QLineEdit(setTask)
        self.nameEdit.setObjectName("nameEdit")

        self.horizontalLayout_4.addWidget(self.nameEdit)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(setTask)
        self.label.setObjectName("label")
        self.label.setMinimumSize(QSize(40, 0))

        self.horizontalLayout.addWidget(self.label)

        self.cmdEdit = QLineEdit(setTask)
        self.cmdEdit.setObjectName("cmdEdit")

        self.horizontalLayout.addWidget(self.cmdEdit)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_4)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QLabel(setTask)
        self.label_2.setObjectName("label_2")
        self.label_2.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.cronEdit = QLineEdit(setTask)
        self.cronEdit.setObjectName("cronEdit")

        self.horizontalLayout_2.addWidget(self.cronEdit)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.cancelButton = QPushButton(setTask)
        self.cancelButton.setObjectName("cancelButton")

        self.horizontalLayout_3.addWidget(self.cancelButton)

        self.okButton = QPushButton(setTask)
        self.okButton.setObjectName("okButton")

        self.horizontalLayout_3.addWidget(self.okButton)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(setTask)

        QMetaObject.connectSlotsByName(setTask)

    # setupUi

    def retranslateUi(self, setTask):
        setTask.setWindowTitle(QCoreApplication.translate("setTask", "Dialog", None))
        self.label_3.setText(QCoreApplication.translate("setTask", "name", None))
        self.label.setText(QCoreApplication.translate("setTask", "cmd", None))
        self.label_2.setText(QCoreApplication.translate("setTask", "cron", None))
        self.cancelButton.setText(QCoreApplication.translate("setTask", "cancel", None))
        self.okButton.setText(QCoreApplication.translate("setTask", "ok", None))

    # retranslateUi
