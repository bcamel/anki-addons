# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'selectdialog.ui'
#
# Created: Tue Jul  1 10:14:21 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_selectDialog(object):
    def setupUi(self, sentenceDialog):
        sentenceDialog.setObjectName(_fromUtf8("sentenceDialog"))
        sentenceDialog.resize(612, 582)
        sentenceDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(sentenceDialog)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setMargin(12)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.listWidget = QtGui.QListWidget(sentenceDialog)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout.addWidget(self.listWidget)
        self.buttonBox = QtGui.QDialogButtonBox(sentenceDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(sentenceDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), sentenceDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), sentenceDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(sentenceDialog)

    def retranslateUi(self, SentenceDialog):
        SentenceDialog.setWindowTitle(_translate("sentenceDialog", "Choose an example sentence", None))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        self.listWidget.setSortingEnabled(__sortingEnabled)

