import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
QCoreApplication.setAttribute(Qt.AA_UseOpenGLES)
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
from PyQt5.QtGui import *
from urllib.parse import urlparse
from PyQt5.QtWebEngineWidgets import *



class BrowserTab(QWidget):
    def __init__(self, url):
        super(BrowserTab, self).__init__()

        # Create the browser widget and set the default url
        self.browser = QWebEngineView()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.browser.setUrl(QUrl(url))



        # Set the layout for the tab
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)




        self.browser.page().profile().downloadRequested.connect(self.download)
        self.browser.page().fullScreenRequested.connect(self.FullscreenRequest)
        self.is_fullscreen = False

    def download(self, download_item):
        # Get the suggested file name and the MIME type
        mime_type = download_item.mimeType()
        suggested_file_name = download_item.suggestedFileName()
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        # Set the default file path to the "Downloads" folder
        default_file_path = os.path.join(default_dir, suggested_file_name)
        # Ask the user to select a file name and a save location
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_file_path,
                                                   "{} files (*.{})".format(mime_type, mime_type.split("/")[-1]))

        # Start the download if a file path is selected
        if file_path:
            download_item.setPath(file_path)
            download_item.accept()

            # Add a progress bar to show the download progress
            progress_bar = QProgressBar(self)
            progress_bar.setOrientation(Qt.Horizontal)
            progress_bar.setMaximum(100)
            progress_bar.setMinimum(0)
            progress_bar.setValue(0)
            progress_bar.setTextVisible(True)
            progress_bar.setAlignment(Qt.AlignCenter)
            progress_bar.setFixedWidth(self.width())
            progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                padding: 1px;
                text-align: center;
                font: bold 12px;
            }
            """)
            self.layout().addWidget(progress_bar)

            # Update the progress bar with the download progress
            download_item.downloadProgress.connect(lambda bytes_received, total_bytes:
                                                   progress_bar.setValue(int(100 * bytes_received / total_bytes)))

            # Connect the cancel button click event to the cancellation function
            cancel_button = QPushButton("Cancel", self)
            cancel_button.clicked.connect(lambda: self.cancel_download(download_item, progress_bar, file_path))
            self.layout().addWidget(cancel_button)

            # Remove the progress bar, cancel button, and the downloaded file once the download is complete
            download_item.finished.connect(lambda: self.cleanup_download(progress_bar, cancel_button, file_path))

    def cancel_download(self, download_item, progress_bar, file_path):
        # Cancel the download and remove the progress bar
        download_item.cancel()
        progress_bar.deleteLater()

        # Delete the partially downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    def cleanup_download(self, progress_bar, cancel_button, file_path):
        # Remove the progress bar and cancel button
        progress_bar.deleteLater()
        cancel_button.deleteLater()

        # Delete the downloaded file if it exists and the download was successful
        if os.path.exists(file_path):
            os.remove(file_path)

    def FullscreenRequest(self, request):
        request.accept()
        if request.toggleOn():
            if not self.is_fullscreen:
                self.browser.setParent(None)
                self.browser.showFullScreen()
                self.is_fullscreen = True
        else:
            if self.is_fullscreen:
                self.browser.setParent(self)
                self.layout().addWidget(self.browser)
                self.browser.showNormal()
                self.is_fullscreen = False


class BrowserWindow(QMainWindow):
    def __init__(self):
        super(BrowserWindow, self).__init__()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # Make the tabs closable
        self.tab_widget.tabCloseRequested.connect(
            self.close_tab)  # Connect the tabCloseRequested signal to the close_tab function
        self.tab_widget.addTab(BrowserTab("http://www.google.com"), "Google")
        self.tab_widget.currentChanged.connect(self.current_browser)
        self.setCentralWidget(self.tab_widget)
        self.current_browser().urlChanged.connect(self.update_urlbar)
        self.setWindowTitle("My Web Browser")
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: white;")
        self.current_browser().urlChanged.connect(self.update_urlbar)
        self.tab_widget.currentChanged.connect(self.update_urlbar_and_tab_text)

        # Create the navigation toolbar and add the buttons
        navbar = QToolBar("Navigation")

        navbar.setStyleSheet("""
        QToolBar {
            background-color: #f2f2f2;
            border-bottom: 1px solid #d9d9d9;
            padding: 5px;
        }

        QToolButton {
            background-color: transparent;
            color: #333;
            border: none;
            padding: 8px;
            margin-right: 5px;
            font-weight: bold;
        }

        QToolButton:hover {
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        QToolButton:pressed {
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }

        QToolButton:checked {
            background-color: #008080;
            color: white;
        }
    """)

        self.addToolBar(navbar)
        navbar.setFixedHeight(50)

        back_btn = QAction(QIcon("icons/xb.png"), "", self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        forward_btn = QAction(QIcon("icons/xf.png"), "", self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)

        home_btn = QAction(QIcon("icons/xh.png"), "", self)
        home_btn.triggered.connect(lambda: self.current_browser().setUrl(QUrl("https://www.google.com")))
        navbar.addAction(home_btn)

        reload_btn = QAction(QIcon("icons/x.png"), "", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        reload_btn.setProperty("showDecorationSelected", False)
        navbar.addAction(reload_btn)

        self.httpsicon = QLabel()
        self.httpsicon.setStyleSheet("background-color: #f2f2f2; border-top: 0px solid #d9d9d9;")
        navbar.addWidget(self.httpsicon)

        # Create the address bar and connect to the urlChanged signal
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.urlbar.setFixedHeight(25)
        navbar.addWidget(self.urlbar)
        self.urlbar.setStyleSheet("""
                background-color: #f7f7f7;
                color: black;
                border: 2px solid gray;
                border-radius: 5px;
                """)

        self.current_browser().urlChanged.connect(self.update_urlbar)

        new_tab_btn = QAction(QIcon("icons/yıldız.png"), "", self)
        new_tab_btn.triggered.connect(self.add_tab)
        navbar.addAction(new_tab_btn)

        # Add a button to create a new tab

        # Set some window properties

    def update_tab_text(self, url):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            tab_text = self.get_tab_text_from_url(url)
            tab_text = tab_text.capitalize()  # Baş harfi büyük yapma işlemi
            self.tab_widget.setTabText(current_index, tab_text)

    def update_urlbar_and_tab_text(self):
        current_browser = self.current_browser()
        if current_browser is not None:
            url = current_browser.url()
            self.update_urlbar(url)

    def get_tab_text_from_url(self, url):
        # Extract a meaningful tab text from the URL
        # Example: Get the domain name from the URL
        domain = url.netloc.split("www.")[-1]  # Remove "www." from the domain
        domain = domain.split(".")[0]  # Remove the extension from the domain
        return domain

    def add_tab(self):
        tab = BrowserTab("http://www.google.com")
        self.tab_widget.addTab(tab, "Google")
        self.tab_widget.setCurrentWidget(tab)
        self.current_browser().urlChanged.connect(self.update_urlbar)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            current_widget = self.tab_widget.widget(index)
            current_widget.deleteLater()
            self.tab_widget.removeTab(index)

    def navigate_to_url(self):
        url = self.urlbar.text()
        q = QUrl(url)
        if q.scheme() == "":
            url = "http://" + url
            q = QUrl(url)
        self.current_browser().setUrl(q)

    def update_urlbar(self, q):
        pixmap = (
            QPixmap("icons/ssl.png")
            if q.scheme() == "https"
            else QPixmap("icons/lock.png")
        )
        pixmap_size = pixmap.size()  # Orijinal pixmap'in boyutunu alın
        padding = 15  # Eklemek istediğiniz boşluğun genişliği

        new_pixmap = QPixmap(pixmap_size.width() + padding,
                             pixmap_size.height())  # Yeni bir pixmap oluşturun, genişlikte boşluk ekleyin
        new_pixmap.fill(Qt.transparent)  # Pixmap'i şeffaf bir şekilde doldurun

        painter = QPainter(new_pixmap)
        painter.drawPixmap(padding, 0, pixmap)  # Orijinal pixmap'i boşluğun sağ tarafına çizin
        painter.end()

        self.httpsicon.setPixmap(new_pixmap)

        url = urlparse(q.toString())
        self.urlbar.setText(url.netloc + url.path)
        self.urlbar.setCursorPosition(0)
        self.update_tab_text(url)

    def current_browser(self):
        index = self.tab_widget.currentIndex()
        if index == -1:
            return None
        return self.tab_widget.widget(index).browser


if __name__ == '__main__':
    app = QApplication(sys.argv)

    global_settings = QWebEngineSettings.globalSettings()
    global_settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    global_settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    global_settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)

    window = BrowserWindow()
    window.show()
    sys.exit(app.exec_())
