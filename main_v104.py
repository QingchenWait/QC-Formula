# -*- coding:utf-8 -*-
### QingChen-Formula 主程序
# 版本： v 1.0.4
# 1. 增加了对 pyinstaller 打包的说明
# 2. 修改了部分 PyQt 控件尺寸，使控件在 1920x1080 分辨率屏幕中，也能够以相对正常的尺寸显示
# 3. 使用 configparser 读取配置文件时，编码方式改为 utf-8-sig，避免当配置文件中图片路径存在中文时，程序出现闪退

import sys
import os
import configparser ### 读写配置文件包
from threading import Timer ### 定时器相关
import pyperclip ### 用于将公式复制到剪贴板
import webbrowser
from PyQt5 import QtCore ### PyQt 组件事件处理
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
# 从根目录下文件中调用的类
from Init_Window_v104 import Ui_MainWindow ### PyQt 界面样式
from OCR_iFLY_v104 import get_result ### 讯飞接口
import numpy as np
### 注意：使用 PyInstaller 进行打包时，配置文件路径的定义，与调试时不同。
### 使用 Python IDE 调试时，需要注释掉第二行，使第一行命令生效；而使用 PyInstaller 进行打包时，需要注释掉第一行，使第二行命令生效。
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) ### 用于读写配置文件的全局路径
print(BASE_DIR)
#BASE_DIR = os.path.dirname(sys.executable) ### 用于读写配置文件的全局路径

class MainWindow(QMainWindow):
    # 初始化主交互界面
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowCloseButtonHint|Qt.WindowMinimizeButtonHint) # 窗口尺寸固定，禁止最大化按钮
        # 读取配置文件，将 API 配置项的值写入设置中
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        self.ui.Input_APPID.setText(self.conf.get('API_iFLY', 'APPID'))
        self.ui.Input_APISecret.setText(self.conf.get('API_iFLY', 'APISecret'))
        self.ui.Input_APIKey.setText(self.conf.get('API_iFLY', 'APIKey'))
        self.ui.Copy_Status_Label.setText("")
        self.ui.DOCPage_LoadButton_clipboard.clicked.connect(self.img_Load_From_Clipboard)


    # 定义槽函数：从本地请求图片地址
    def img_Load_From_Doc(self):
        # 调用一个文件选择框，获取文件路径
        path_Read = QFileDialog.getOpenFileName(self, "选择文件", ".", "公式图片 (*.png *.bmp *.jpg)")
        self.img_path = path_Read[0]
        print(self.img_path)
        # 将文件路径写入数据库
        self.conf = configparser.ConfigParser() # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR ,'config.ini'),encoding="utf-8-sig") # 从全局路径读取配置文件
        IMG_Last_Time = self.conf.get('img_Location','DOC') # 写在配置文件中的上一次读取路径
        if IMG_Last_Time == self.img_path:
            print("路径重复")
        elif self.img_path == '':  # 若没有选择任何路径，则使用上一次使用的图片
                self.img_path = IMG_Last_Time
        elif os.path.exists(self.img_path) == False: # 若无法读取文件，则使用初始图片
            self.img_path = 'Examples/01.png'
            self.ui.plainTextEdit.setPlainText("错误：无法读取目标图片，请重新选择图片")
        else:
            self.conf.set('img_Location', 'DOC', self.img_path)
            ### 确定写入配置文件
            with open("config.ini", "w+") as f:
                self.conf.write(f)
            print("IMG LOAD SUCCESS")

    def img_Load_From_Clipboard(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        self.img_Display_In_Doc_Label_Clipboard(image)

    def img_Display_In_Doc_Label_Clipboard(self,image):
        # 在 QLabel 中绘制图片
        image = QPixmap.fromImage(image)
        self.ui.DOCPage_ImageLabel.setPixmap(image)
        self.ui.DOCPage_ImageLabel.setScaledContents(True)  # 自适应QLabel大小
        # 保存照片
        image_path = os.path.join(BASE_DIR,'Examples','temp.png')
        image.save(image_path)
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        try:
            self.conf.set('img_Location', 'DOC', image_path)
            ### 确定写入配置文件
            with open("config.ini", "w+") as f:
                self.conf.write(f)
            print("IMG LOAD SUCCESS")
        except:
            pass

        # 定义槽函数：从互联网请求图片地址
    def img_Load_From_Internet(self):
        return 0 ### 等待后续开发...

    # 定义槽函数：使用 QLabel 展示图片
    def img_Display_In_Doc_Label(self):
        # 读取配置文件，找到图片路径
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        self.img_path = self.conf.get('img_Location', 'DOC')  # 写在配置文件中的上一次读取路径
        # 在 QLabel 中绘制图片
        image = QPixmap(self.img_path)
        self.ui.DOCPage_ImageLabel.setPixmap(image)
        self.ui.DOCPage_ImageLabel.setScaledContents(True) # 自适应QLabel大小

        return 0

    # 定义槽函数：显示图片信息
    def Get_img_Info(self):
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        self.img_path = self.conf.get('img_Location', 'DOC')
        self.ui.plainTextEdit.appendPlainText("图片位置：" + self.img_path)

    # 调用讯飞接口执行公式识别
    def Formula_OCR_Execute_iFLY(self):
        # 示例:  host="rest-api.xfyun.cn"域名形式
        host = "rest-api.xfyun.cn"
        # 执行请求
        self.gClass = get_result(host)
        try:
            output_formula = self.gClass.call_url()
        except FileNotFoundError: # 防止以下操作引起的程序崩溃：在关闭程序后，删除图片，重新打开程序，并直接点击公式识别按钮
            output_formula = "错误：无法找到上一次使用的公式图片，请重新选择"
        self.ui.plainTextEdit.setPlainText(output_formula) # 将结果显示在底部文本框中

    # 定义槽函数：复制公式识别结果到剪贴板
    def Copy_Formula_Result(self):
        pyperclip.copy(self.ui.plainTextEdit.toPlainText())
        self.ui.Copy_Status_Label.setText("复制成功！")
        def Status_Label_Clear():
            self.ui.Copy_Status_Label.setText("")
        t = Timer(3.0,Status_Label_Clear)
        t.start()
        return 0

    # 定义槽函数：输入 API 信息
    def Setting_API_Values(self):
        # 将 API 信息写入配置文件
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        self.conf.set('API_iFLY', 'APPID', self.ui.Input_APPID.text())
        self.conf.set('API_iFLY', 'APISecret', self.ui.Input_APISecret.text())
        self.conf.set('API_iFLY', 'APIKey', self.ui.Input_APIKey.text())
        with open("config.ini", "w+") as f:
            self.conf.write(f)
        self.ui.plainTextEdit.setPlainText("API 配置完成！")

    # 定义槽函数：显示 API 获取方法教程
    def Get_API_Tutorial(self):
        self.ui.plainTextEdit.setPlainText("API 获取教程：详见软件代码仓库 \n    - 码云地址：https://gitee.com/qingchen1995/qc-formula \n    - GitHub 地址：https://github.com/QingchenWait/QC-Formula \n可以点击左上角的 '帮助菜单' 一键直达。 \n \n欢迎访问青尘工作室官网：https://qingchen1995.gitee.io")

    # 定义槽函数：访问青尘工作室官网
    def Link_To_Official_Site(self):
        official_site = 'https://qingchen1995.gitee.io'
        webbrowser.open_new_tab(official_site)

    # 定义槽函数：访问 Gitee 教程
    def Link_To_Gitee_Tutorial(self):
        Gitee_site = 'https://gitee.com/qingchen1995/qc-formula'
        webbrowser.open_new_tab(Gitee_site)

    # 定义槽函数：访问 GitHub 教程
    def Link_To_Github_Tutorial(self):
        Github_site = 'https://github.com/QingchenWait/QC-Formula'
        webbrowser.open_new_tab(Github_site)

    # 定义槽函数：显示关于软件
    def About_Software(self):
        self.ui.plainTextEdit.setPlainText("QingChen Formula - 青尘公式 OCR \n    - 版本：v1.0.3\n    - 开发者：青尘工作室\n    - 工作室官网：https://qingchen1995.gitee.io")

if __name__ == '__main__':
    ### 加载 UI 界面
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling) # 添加高分辨率缩放支持
    app = QApplication(sys.argv)
    MainInterface = MainWindow()
    MainInterface.show()

    sys.exit(app.exec_())