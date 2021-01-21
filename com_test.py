# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 11:47:20 2020

@author: miaok
"""
import serial
import serial.tools.list_ports
import binascii
from motor import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog,QMainWindow)
from PyQt5.QtCore import Qt, pyqtSlot
import sys
import re

class Qmymotor(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)   # 调用父类构造函数，创建窗体
        self.ui=Ui_MainWindow()     # 创建UI对象
        self.ui.setupUi(self)      # 构造UI界面

    @pyqtSlot()
    def on_pushButton_3_clicked(self):  # 查询COM口
      print("test_hahah")
      self.ui.plist = list(serial.tools.list_ports.comports())
      port = re.split(' ', str(self.ui.plist[0]))
      port = port[0]
      for i in range(len(self.ui.plist)):
        print(self.ui.plist[i])
      # self.ui.config_path = QFileDialog.getOpenFileName(self, "getOpenFileName","./","All Files (*);;Text Files (*.txt)")    # 获取文本路径本路径
      self.ui.lineEdit_2.clear()
      self.ui.lineEdit_2.setText(port)
      self.ui.com = port

    @pyqtSlot()
    def on_pushButton_2_clicked(self):  # 运动
        #print('heheh')
        num = int(float(self.ui.lineEdit_5.text()))
        print(num)
        step = int(float(self.ui.doubleSpinBox.text())*640) #640pulse对应1mm
        print(step)
        portx = self.ui.com
        bps=9600
        timex=0.5
        pulse = str(hex(step)[2:])
        print(pulse)
        if len(pulse) < 4:  #补0
            pulse = list(pulse)
            for i in range(4 - len(pulse)):
                pulse.insert(0, '0')
        pulse = ''.join(pulse)
        #print('pulse=',pulse)
        #print('01060004' +  pulse + '0D0A')
        text1 = binascii.a2b_hex('01060004' +  pulse + '0D0A')  # 运动指定脉冲数
        #print('text1=',text1)
        text2 = binascii.a2b_hex('0105000200000D0A')  # 正向
        text3 = binascii.a2b_hex('0105000200FF0D0A')  # 反向
        text4 = binascii.a2b_hex('0105000300000D0A')  # 复位，回到本次测试开始位置
        ser = serial.Serial(portx, bps, timeout=timex)

        if int(self.ui.comboBox.currentIndex()) == 1:
            print('positive')
            #direction = 1 # 1:正向 0：反向
            x = ser.readline()
            print('Initial Information=',x)
            ser.write(text3)
            while True:
                x = ser.readline()
                if len(x) > 0:
                    print('Reverse=',x)
                    break
            for i in range(num):
                print('Times=',i)
                ser.write(text1)
                while True:
                    x=ser.readline()
                    if len(x) > 0:
                        print('Info=',x)
                        break
            ser.close()
            print('Finish')
        elif int(self.ui.comboBox.currentIndex()) == 2:
            print('negative')
            #direction = 0 ## 1:正向 0：反向
            x = ser.readline()
            print('Initial Information=', x)
            ser.write(text2)
            while True:
                x = ser.readline()
                if len(x) > 0:
                    print('Reverse=', x)
                    break
            for i in range(num):
                print('Times=', i)
                ser.write(text1)
                while True:
                    x = ser.readline()
                    if len(x) > 0:
                        print('Info=', x)
                        break
            ser.close()
            print('Finish')
        else:
            print('请选择方向')

if  __name__ == "__main__":
   app = QApplication(sys.argv)
   form=Qmymotor()
   form.show()
   sys.exit(app.exec_())
   #app.exec_()