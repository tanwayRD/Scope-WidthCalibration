import serial
import binascii
import socket
import os
import sys
from meas import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QMainWindow)
from PyQt5.QtCore import Qt, pyqtSlot
import re

class Qmymeas(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)   # 调用父类构造函数，创建窗体
        self.ui=Ui_MainWindow()     # 创建UI对象
        self.ui.setupUi(self)      # 构造UI界面

    @pyqtSlot()
    def on_pushButton_3_clicked(self):  # 读取配置文件
      #print("test_hahah")
      self.ui.config_path = QFileDialog.getOpenFileName(self, "getOpenFileName","./","All Files (*);;Text Files (*.txt)")    # 获取文本路径本路径
      self.ui.lineEdit_2.clear()
      self.ui.lineEdit_2.setText(str(self.ui.config_path))

    @pyqtSlot()
    def on_pushButton_2_clicked(self):  # 开始测试
        #print("test_hahah")
        file = open(str(self.ui.config_path[0]))
        for line in file:
            line_mod = line.replace(' ','')
            if 'COM' in line_mod:
                oneline = re.split('=|\n', line_mod)
                ports = 'COM' + oneline[1]
            elif 'save_path' in line:
                oneline = re.split('=|\n', line_mod)
                path = oneline[1]  #标定数据文件存储路径/
        #ports = 'COM6'
        #path = 'D:/Work/tanway/raw_data/8_1/low_crosstalk_1'
        step = 640
        num = 80
        bps = 9600
        timex = 0.5
        ser = serial.Serial(ports, bps, timeout=timex)
        ip = '192.168.111.204'
        port = 5600
        iteration = 6000    #20帧，每帧300包
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建套接字
        udp_socket.bind((ip, port))  # 绑定本地的相关信息

        if not os.path.exists(path):
            os.makedirs(path)
            os.chdir(path)
        else:
            print("目录已存在")
            os.chdir(path)

        pulse = str(hex(step)[2:])
        if len(pulse) < 4:
            pulse = list(pulse)
            for i in range(4-len(pulse)):
                pulse.insert(0,'0')
        pulse = ''.join(pulse)

        text1 = binascii.a2b_hex('01060004' +  pulse + '0D0A')  # 运动指定脉冲数
        text2 = binascii.a2b_hex('0105000200000D0A')  # 正向
        text3 = binascii.a2b_hex('0105000200FF0D0A')  # 反向
        text4 = binascii.a2b_hex('0105000300000D0A')  # 复位，回到本次测试开始位置

        x = ser.readline()
        print('Initial Information=',x)
        ser.write(text3)
        while True:
            x = ser.readline()
            if len(x) > 0:
                print('Reverse=',x)
                break

        for i in range(num):
            print('Sequence=',i+1)
            ser.write(text1)
            while True:
                x=ser.readline()
                if len(x)>0:
                    print('Info=',x)
                    break
            file = open(str(i+1) + '.txt', 'w')
            data = []
            for n in range(iteration):
                sock_data, server_addr = udp_socket.recvfrom(1500)  # UDP接收
                data.append(sock_data)
            for n in range(iteration):
                sock = data[n]  # 1个UDP包1120B
                for i in range(8):  # 2个角度，8根16线单元；每跟16线单元140Byte
                    sub_sock = sock[140 * i:140 * i + 140]
                    flag_sock = sub_sock[136]
                    # print(type(flag_sock))
                    hor_angle_tem = sub_sock[128:132]
                    hor_angle = int.from_bytes(hor_angle_tem, byteorder='big', signed=False) / 100000
                    if 91 >= hor_angle >= 89:
                        if flag_sock == 0:
                            # print(flag_sock)
                            for j in range(16):
                                width_tem = sub_sock[2 + j * 8:4 + j * 8]
                                # print(width_tem)
                                distance_tem = sub_sock[0 + j * 8:2 + j * 8]
                                width = int.from_bytes(width_tem, byteorder='big', signed=False) * 0.004574468
                                distance = float(
                                    format(int.from_bytes(distance_tem, byteorder='big', signed=False) * 0.004574468,
                                           '.5f'))
                                file.writelines(
                                    'Channel: ' + str(j + 1) + ' Angle: ' + str(hor_angle) + ' Distance: ' + str(
                                        distance) + ' PulseWidth: ' + str(
                                        width) + ' Temp: 0.7 HighV: 92.7 SubV: 384' + '\n')
                        elif flag_sock == 64:
                            # print(flag_sock)
                            for j in range(16):
                                width_tem = sub_sock[2 + j * 8:4 + j * 8]
                                distance_tem = sub_sock[0 + j * 8:2 + j * 8]
                                width = int.from_bytes(width_tem, byteorder='big', signed=False) * 0.004574468
                                distance = float(
                                    format(int.from_bytes(distance_tem, byteorder='big', signed=False) * 0.004574468,
                                           '.5f'))
                                file.writelines('Channel: ' + str(j + 17) + ' Angle: ' + str(hor_angle) + ' Distance: ' \
                                                + str(distance) + ' PulseWidth: ' + str(
                                    width) + ' Temp: 0.7 HighV: 92.7 SubV: 384' + '\n')
                        elif flag_sock == 128:
                            # print(flag_sock)
                            for j in range(16):
                                width_tem = sub_sock[2 + j * 8:4 + j * 8]
                                distance_tem = sub_sock[0 + j * 8:2 + j * 8]
                                width = int.from_bytes(width_tem, byteorder='big', signed=False) * 0.004574468
                                distance = float(
                                    format(int.from_bytes(distance_tem, byteorder='big', signed=False) * 0.004574468,
                                           '.5f'))
                                file.writelines('Channel: ' + str(j + 33) + ' Angle: ' + str(hor_angle) + ' Distance: ' \
                                                + str(distance) + ' PulseWidth: ' + str(
                                    width) + ' Temp: 0.7 HighV: 92.7 SubV: 384' + '\n')
                        elif flag_sock == 192:
                            # print(flag_sock)
                            for j in range(16):
                                width_tem = sub_sock[2 + j * 8:4 + j * 8]
                                distance_tem = sub_sock[0 + j * 8:2 + j * 8]
                                width = int.from_bytes(width_tem, byteorder='big', signed=False) * 0.004574468
                                distance = float(
                                    format(int.from_bytes(distance_tem, byteorder='big', signed=False) * 0.004574468,
                                           '.5f'))
                                file.writelines('Channel: ' + str(j + 49) + ' Angle: ' + str(hor_angle) + ' Distance: ' \
                                                + str(distance) + ' PulseWidth: ' + str(
                                    width) + ' Temp: 0.7 HighV: 92.7 SubV: 384' + '\n')
            file.close()
        ser.write(text4)
        while True:
            x = ser.readline()
            if len(x) > 0:
                print('Reset=',x)
                break
        ser.close()
        udp_socket.close()
        print('Finish')

if  __name__ == "__main__":
   app = QApplication(sys.argv)
   form=Qmymeas()
   form.show()
   sys.exit(app.exec_())
   #app.exec_()