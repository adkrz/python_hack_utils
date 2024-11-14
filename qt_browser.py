"""
Example how to run web browser based on chromium engine from Qt5 WebEngine.
Includes: how to run dev tools (open another browser on localhost:999) and setup a proxy server.
Note: if the proxy uses MITM certificate, add its root CA to global trust store for user (certmgr.msc in Windows).
"""
import os
import sys

from PyQt5 import QtNetwork
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://www.google.com"))

        self.setCentralWidget(self.browser)

        self.show()


os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "999"
app = QApplication(sys.argv)

proxy = QtNetwork.QNetworkProxy()
proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
proxy.setHostName("127.0.0.1")
proxy.setPort(8080)
QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

window = MainWindow()

app.exec_()
