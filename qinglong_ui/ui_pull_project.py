# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pull_project.ui'
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
    QCheckBox,
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


class Ui_pullProject(object):
    def setupUi(self, pullProject):
        if not pullProject.objectName():
            pullProject.setObjectName("pullProject")
        pullProject.resize(414, 217)
        self.verticalLayout_2 = QVBoxLayout(pullProject)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_4 = QLabel(pullProject)
        self.label_4.setObjectName("label_4")
        self.label_4.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_6.addWidget(self.label_4)

        self.nameEdit = QLineEdit(pullProject)
        self.nameEdit.setObjectName("nameEdit")

        self.horizontalLayout_6.addWidget(self.nameEdit)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)

        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_3 = QLabel(pullProject)
        self.label_3.setObjectName("label_3")
        self.label_3.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_5.addWidget(self.label_3)

        self.urlEdit = QLineEdit(pullProject)
        self.urlEdit.setObjectName("urlEdit")

        self.horizontalLayout_5.addWidget(self.urlEdit)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_7)

        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.oneFileCheckBox = QCheckBox(pullProject)
        self.oneFileCheckBox.setObjectName("oneFileCheckBox")

        self.verticalLayout_2.addWidget(self.oneFileCheckBox)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)

        self.cancelButton = QPushButton(pullProject)
        self.cancelButton.setObjectName("cancelButton")

        self.horizontalLayout_4.addWidget(self.cancelButton)

        self.okButton = QPushButton(pullProject)
        self.okButton.setObjectName("okButton")

        self.horizontalLayout_4.addWidget(self.okButton)

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.retranslateUi(pullProject)

        QMetaObject.connectSlotsByName(pullProject)

    # setupUi

    def retranslateUi(self, pullProject):
        pullProject.setWindowTitle(QCoreApplication.translate("pullProject", "Dialog", None))
        self.label_4.setText(QCoreApplication.translate("pullProject", "name", None))
        self.label_3.setText(QCoreApplication.translate("pullProject", "url", None))
        self.oneFileCheckBox.setText(QCoreApplication.translate("pullProject", "one_file", None))
        self.cancelButton.setText(QCoreApplication.translate("pullProject", "cancel", None))
        self.okButton.setText(QCoreApplication.translate("pullProject", "ok", None))

    # retranslateUi
