# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QTableView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(593, 739)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.project_label = QLabel(self.centralwidget)
        self.project_label.setObjectName(u"project_label")

        self.horizontalLayout.addWidget(self.project_label)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.pullButton = QPushButton(self.centralwidget)
        self.pullButton.setObjectName(u"pullButton")

        self.horizontalLayout.addWidget(self.pullButton)

        self.uploadButton = QPushButton(self.centralwidget)
        self.uploadButton.setObjectName(u"uploadButton")

        self.horizontalLayout.addWidget(self.uploadButton)

        self.upgradeButton = QPushButton(self.centralwidget)
        self.upgradeButton.setObjectName(u"upgradeButton")

        self.horizontalLayout.addWidget(self.upgradeButton)

        self.removeButton = QPushButton(self.centralwidget)
        self.removeButton.setObjectName(u"removeButton")

        self.horizontalLayout.addWidget(self.removeButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.projectView = QTableView(self.centralwidget)
        self.projectView.setObjectName(u"projectView")

        self.verticalLayout.addWidget(self.projectView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.task_label = QLabel(self.centralwidget)
        self.task_label.setObjectName(u"task_label")

        self.horizontalLayout_2.addWidget(self.task_label)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.setButton = QPushButton(self.centralwidget)
        self.setButton.setObjectName(u"setButton")

        self.horizontalLayout_2.addWidget(self.setButton)

        self.startButton = QPushButton(self.centralwidget)
        self.startButton.setObjectName(u"startButton")

        self.horizontalLayout_2.addWidget(self.startButton)

        self.pauseButton = QPushButton(self.centralwidget)
        self.pauseButton.setObjectName(u"pauseButton")

        self.horizontalLayout_2.addWidget(self.pauseButton)

        self.removeButton_2 = QPushButton(self.centralwidget)
        self.removeButton_2.setObjectName(u"removeButton_2")

        self.horizontalLayout_2.addWidget(self.removeButton_2)

        self.runButton = QPushButton(self.centralwidget)
        self.runButton.setObjectName(u"runButton")

        self.horizontalLayout_2.addWidget(self.runButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.taskView = QTableView(self.centralwidget)
        self.taskView.setObjectName(u"taskView")
        self.taskView.setAutoFillBackground(False)

        self.verticalLayout.addWidget(self.taskView)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.project_label.setText(QCoreApplication.translate("MainWindow", u"project", None))
        self.pullButton.setText(QCoreApplication.translate("MainWindow", u"pull", None))
        self.uploadButton.setText(QCoreApplication.translate("MainWindow", u"upload", None))
        self.upgradeButton.setText(QCoreApplication.translate("MainWindow", u"upgrade", None))
        self.removeButton.setText(QCoreApplication.translate("MainWindow", u"remove", None))
        self.task_label.setText(QCoreApplication.translate("MainWindow", u"task", None))
        self.setButton.setText(QCoreApplication.translate("MainWindow", u"set", None))
        self.startButton.setText(QCoreApplication.translate("MainWindow", u"start", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", u"pause", None))
        self.removeButton_2.setText(QCoreApplication.translate("MainWindow", u"remove", None))
        self.runButton.setText(QCoreApplication.translate("MainWindow", u"run", None))
    # retranslateUi

