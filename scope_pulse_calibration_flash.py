import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d
import math
import re
from cali import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QMainWindow)
from PyQt5.QtCore import Qt, pyqtSlot
import sys


class Qmycali(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)   # 调用父类构造函数，创建窗体
        self.ui=Ui_MainWindow()     # 创建UI对象
        self.ui.setupUi(self)      # 构造UI界面

    @pyqtSlot()
    def on_pushButton_clicked(self):
      #print("test")
      self.ui.directory = QFileDialog.getExistingDirectory(self, "getExistingDirectory", "./")
      print(self.ui.directory)
      self.ui.lineEdit.clear()
      self.ui.lineEdit.setText(str(self.ui.directory))

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
      #print("test_hahah")
      self.ui.config_path = QFileDialog.getOpenFileName(self, "getOpenFileName","./","All Files (*);;Text Files (*.txt)")    # 获取文本路径本路径
      self.ui.lineEdit_2.clear()
      self.ui.lineEdit_2.setText(str(self.ui.config_path))

    @pyqtSlot()
    def on_pushButton_2_clicked(self):  #
        path = self.ui.directory
        inf = re.split('/', path)
        Device = inf[-2][-4:]
        channel_enable = np.ones(64).tolist()
        file = open(str(self.ui.config_path[0]))
        count = 0
        for line in file:
            count += 1
            line_mod = line.replace(' ', '')
            if count < 65:
                oneline = re.split('=|\n', line_mod)
                channel_enable[count - 1] = int(oneline[1])
        #Device = '0517'
        #path = 'D:/Work/tanway/raw_data/8_1/low_crosstalk_1'    # calibration数据存储txt文件路径
        #channel_enable =[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        count2dis = 0.004574468994
        udp_count = 0                      #
        frame_count = 0                         # 按帧截断不起作用
        channel_number = 64

        ############# get calibration raw data################
        txt_list = []
        if not os.path.exists(path + '/result'):
            os.mkdir(path + '/result')
        for file in os.listdir(path):
            if file.endswith(".txt"):
                txt_list.append(file)
        txt_list = sorted(txt_list, key=lambda x: int(x[:-4]))
        T = np.arange(len(txt_list))
        raw_distance = []  # calibration raw distance data
        raw_pulse = []  # calibration raw pulse width data
        filter_pulse = []
        filter_distance = []

        for i in range(len(txt_list)):
            raw_distance.append([])
            raw_pulse.append([])
            filter_pulse.append([])
            filter_distance.append([])
            for j in range(channel_number):
                raw_distance[i].append([])
                raw_pulse[i].append([])
                filter_distance[i].append([])
                filter_pulse[i].append([])
        for i in range(len(txt_list)):
            rawdata_textname = txt_list[i]
            rawdata_textname = path + '/' + rawdata_textname
            file = open(rawdata_textname)
            for line in file:
                oneline = re.split(' ', line)
                channel = int(oneline[1])
                angle = float(oneline[3])
                distance = float(oneline[5])
                pulse = float(oneline[7])
                if 1.5 < distance < 8 and 0 < pulse < 100:
                    raw_distance[i][channel - 1].append(distance)
                    raw_pulse[i][channel - 1].append(pulse)

        filter_distance_mean = []
        filter_distance_std = []
        filter_pulse_mean = []
        filter_pulse_std = []
        for i in range(channel_number):
            filter_distance_mean.append([])
            filter_distance_std.append([])
            filter_pulse_mean.append([])
            filter_pulse_std.append([])
        for i in range(len(txt_list)):
            for j in range(channel_number):
                pulse_mean_tem = np.mean(raw_pulse[i][j], axis=0)
                distance_mean_tem = np.mean(raw_distance[i][j], axis=0)
                pulse_std_tem = np.std(raw_pulse[i][j], axis=0, ddof=1)
                distance_std_tem = np.std(raw_distance[i][j], axis=0, ddof=1)
                if distance_std_tem * 3 < 0.015:
                    Outer_d = 0.015
                else:
                    Outer_d = distance_std_tem * 3
                if pulse_std_tem * 3 < 0.015:
                    Outer_p = 0.015
                else:
                    Outer_p = pulse_std_tem * 3
                for k in range(len(raw_pulse[i][j])):
                    if abs(raw_pulse[i][j][k] - pulse_mean_tem) < Outer_p and \
                            abs(raw_distance[i][j][k] - distance_mean_tem) < Outer_d:
                        filter_pulse[i][j].append((raw_pulse[i][j][k]))
                        filter_distance[i][j].append((raw_distance[i][j][k]))
                if np.mean(filter_pulse[i][j]) > 0 and np.mean(filter_distance[i][j]) > 0:
                    filter_pulse_mean[j].append(np.mean(filter_pulse[i][j]))
                    filter_distance_mean[j].append(np.mean(filter_distance[i][j]))
                    filter_pulse_std[j].append(np.std(filter_pulse[i][j], ddof=1))
                    filter_distance_std[j].append(np.std(filter_distance[i][j], ddof=1))
        filter_distance_err = []
        for i in range(channel_number):
            filter_distance_err.append([])
            for j in range(len(filter_distance_mean[i])):
                if filter_distance_mean[i][j] > 0:
                    tem = filter_distance_mean[i][j] - min(filter_distance_mean[i])
                    filter_distance_err[i].append(tem)
                else:
                    filter_distance_err[i].append(np.nan)

        kt_0 = plt.figure(1, figsize=(25, 12))
        for i in range(16):
            guit = kt_0.add_subplot(4, 4, i + 1)
            guit.plot(filter_distance_mean[i], 'b-o')
            # print(min(min(filter_distance_mean)),max(max(filter_distance_mean)))
            plt.ylim(min(min(filter_distance_mean)) - 0.1, max(max(filter_distance_mean)) + 0.1)
            plt.tick_params(labelsize=16)
            guit2 = guit.twinx()
            guit2.plot(filter_pulse_mean[i], 'r-s')
            plt.ylim(0, max(max(filter_pulse_mean)) + 0.2)
            plt.tick_params(labelsize=16)
            guit.grid(True)
            if i == 12 or i == 13 or i == 14 or i == 15:
                guit.set_xlabel('Test Sequence', fontsize=16)
            if i == 0 or i == 4 or i == 8 or i == 12:
                guit.set_ylabel('Distance/m', fontsize=16)
                guit.yaxis.label.set_color('blue')
            if i == 3 or i == 7 or i == 11 or i == 15:
                guit2.set_ylabel('Pulse Width/m', fontsize=16)
                guit2.yaxis.label.set_color('red')
            title = 'Dis & PW vs Test Sequ Ch ' + str(i + 1)
            plt.title(title, fontsize=16)
        plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.3)
        plt.savefig(path + '/result/' + 'Distance & Pulse Width1.png')
        plt.show()
        plt.close()

        kt_1 = plt.figure(2, figsize=(25, 12))
        for i in range(16, 32):
            guit = kt_1.add_subplot(4, 4, i - 15)
            guit.plot(filter_distance_mean[i], 'b-o')
            # print(min(min(filter_distance_mean)),max(max(filter_distance_mean)))
            plt.ylim(min(min(filter_distance_mean)) - 0.1, max(max(filter_distance_mean)) + 0.1)
            plt.tick_params(labelsize=16)
            guit2 = guit.twinx()
            guit2.plot(filter_pulse_mean[i], 'r-s')
            plt.ylim(0, max(max(filter_pulse_mean)) + 0.2)
            plt.tick_params(labelsize=16)
            guit.grid(True)
            if i == 28 or i == 29 or i == 30 or i == 31:
                guit.set_xlabel('Test Sequence', fontsize=16)
            if i == 16 or i == 20 or i == 24 or i == 28:
                guit.set_ylabel('Distance/m', fontsize=16)
                guit.yaxis.label.set_color('blue')
            if i == 19 or i == 23 or i == 27 or i == 31:
                guit2.set_ylabel('Pulse Width/m', fontsize=16)
                guit2.yaxis.label.set_color('red')
            title = 'Dis & PW vs Test Sequ Ch ' + str(i + 1)
            plt.title(title, fontsize=16)
        plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.3)
        plt.savefig(path + '/result/' + 'Distance & Pulse Width2.png')
        plt.show()
        plt.close()

        kt_2 = plt.figure(3, figsize=(25, 12))
        for i in range(32, 48):
            guit = kt_2.add_subplot(4, 4, i - 31)
            guit.plot(filter_distance_mean[i], 'b-o')
            # print(min(min(filter_distance_mean)),max(max(filter_distance_mean)))
            plt.ylim(min(min(filter_distance_mean)) - 0.1, max(max(filter_distance_mean)) + 0.1)
            plt.tick_params(labelsize=16)
            guit2 = guit.twinx()
            guit2.plot(filter_pulse_mean[i], 'r-s')
            plt.ylim(0, max(max(filter_pulse_mean)) + 0.2)
            plt.tick_params(labelsize=16)
            guit.grid(True)
            if i == 44 or i == 45 or i == 46 or i == 47:
                guit.set_xlabel('Test Sequence', fontsize=16)
            if i == 32 or i == 36 or i == 40 or i == 44:
                guit.set_ylabel('Distance/m', fontsize=16)
                guit.yaxis.label.set_color('blue')
            if i == 35 or i == 39 or i == 43 or i == 47:
                guit2.set_ylabel('Pulse Width/m', fontsize=16)
                guit2.yaxis.label.set_color('red')
            title = 'Dis & PW vs Test Sequ Ch ' + str(i + 1)
            plt.title(title, fontsize=16)
        plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.3)
        plt.savefig(path + '/result/' + 'Distance & Pulse Width3.png')
        plt.show()
        plt.close()

        kt_3 = plt.figure(4, figsize=(25, 12))
        for i in range(48, 64):
            guit = kt_3.add_subplot(4, 4, i - 47)
            guit.plot(filter_distance_mean[i], 'b-o')
            # print(min(min(filter_distance_mean)),max(max(filter_distance_mean)))
            plt.ylim(min(min(filter_distance_mean)) - 0.1, max(max(filter_distance_mean)) + 0.1)
            plt.tick_params(labelsize=16)
            guit2 = guit.twinx()
            guit2.plot(filter_pulse_mean[i], 'r-s')
            plt.ylim(0, max(max(filter_pulse_mean)) + 0.2)
            plt.tick_params(labelsize=16)
            guit.grid(True)
            if i == 60 or i == 61 or i == 62 or i == 63:
                guit.set_xlabel('Test Sequence', fontsize=16)
            if i == 48 or i == 52 or i == 56 or i == 60:
                guit.set_ylabel('Distance/m', fontsize=16)
                guit.yaxis.label.set_color('blue')
            if i == 51 or i == 55 or i == 59 or i == 63:
                guit2.set_ylabel('Pulse Width/m', fontsize=16)
                guit2.yaxis.label.set_color('red')
            title = 'Dis & PW vs Test Sequ Ch ' + str(i + 1)
            plt.title(title, fontsize=16)
        plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.3)
        plt.savefig(path + '/result/' + 'Distance & Pulse Width4.png')
        plt.show()
        plt.close()

        #########################################################
        ################fitting and get error ###################
        samples = np.array(filter_pulse_mean) / count2dis  # convert filter_pulse_mean to count and array
        values = np.array(filter_distance_err) / count2dis  # convert filter_distance_err to count and array

        index_start = []
        index_end = []
        index_start_reduce = []
        index_end_reduce = []
        file_new_texname = path + '/result' + '/Fit_' + '.txt'
        file_new_texname = open(file_new_texname, 'w')
        fitting_count = []  # 修正值，整数
        # fit_y_int = [] #拟合函数取整
        fit_y_dis = []
        for i in range(channel_number):
            fitting_count.append([])
            # fit_y_int.append([])
            fit_y_dis.append([])
        for i in range(channel_number):
            samples_sub = samples[i][~np.isnan(samples[i])]
            values_sub = values[i][~np.isnan(values[i])]
            index_start.append(int(math.ceil(min(list(samples_sub)))))
            index_end.append(int(math.floor(max(list(samples_sub)))))
            # print(index_start[-1])
            # print(index_end[-1])
            queries = range(index_start[-1], index_end[-1] + 1)  # 【-1】当前
            slinear_func = interp1d(list(samples_sub), list(values_sub), kind='slinear')
            fit_y = slinear_func(queries)
            # print(fit_y)

            samples_sub_dis = [item * count2dis for item in samples_sub]
            values_sub_dis = [item * count2dis for item in values_sub]
            queries_dis = [item * count2dis for item in queries]
            fit_y_dis[i] = np.rint(fit_y) * count2dis
            # fit_y_int[i] = np.rint(slinear_func(queries)) #四舍五入

            # # save txt
            index_start_reduce.append(math.ceil(index_start[-1] / 8))
            index_end_reduce.append(math.floor(index_end[-1] / 8) - 1)
            index_bias = index_start_reduce[-1] * 8 - index_start[-1]
            length = index_end_reduce[-1] - index_start_reduce[-1] + 1
            for j in range(length):
                fitting_y = int(np.rint(np.mean(fit_y[(8 * j + index_bias):(8 * j + 8 + index_bias)])))  # 8个平均输出一个修正值
                fitting_count[i].append(fitting_y)
                # fitting_y = int(np.rint(np.mean(fit_y[(8 * j ):(8 * j + 8 )])))
            if i < 16:
                kt_4 = plt.figure(5, figsize=(25, 12))
                guit = kt_4.add_subplot(4, 4, i + 1)
                guit.grid(True)
                guit.scatter(samples_sub_dis, values_sub_dis, alpha=1, s=100, c='r', marker='*')
                plt.ylim(min(values[~np.isnan(values)]) - 0.1, max(values[~np.isnan(values)]) + 0.1)
                plt.tick_params(labelsize=16)
                guit.scatter(8 * count2dis * np.arange(index_start_reduce[-1], index_end_reduce[-1] + 1),
                             count2dis * np.array(fitting_count[i]), alpha=0.5, s=50, color='b', marker='.')
                # plt.ylim(-0.1, count2dis * max(max(fitting_count)) + 0.2)
                plt.tick_params(labelsize=16)
                guit.set_xlabel('Pulse Width Output/m', fontsize=12)
                guit.set_ylabel('Compensation Values/m', fontsize=12)
                guit.yaxis.label.set_color('blue')
                title = 'Distance Compensation vs PW CH ' + str(i + 1)
                plt.title(title, fontsize=12)
                # file_new_texname.writelines('Channel:' + str(i + 1) + '\n')
                if i == 15:
                    plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.5)
                    plt.savefig(path + '/result/' + 'Fitting1.png')
                    plt.show()
                    plt.close()
                    continue

            if i > 15 and i < 32:
                kt_5 = plt.figure(6, figsize=(25, 12))
                guit = kt_5.add_subplot(4, 4, i - 15)
                guit.grid(True)
                guit.scatter(samples_sub_dis, values_sub_dis, alpha=1, s=100, c='r', marker='*')
                plt.ylim(min(values[~np.isnan(values)]) - 0.1, max(values[~np.isnan(values)]) + 0.1)
                plt.tick_params(labelsize=16)
                guit.scatter(8 * count2dis * np.arange(index_start_reduce[-1], index_end_reduce[-1] + 1),
                             count2dis * np.array(fitting_count[i]), alpha=0.5, s=50, color='b', marker='.')
                # plt.ylim(-0.1, count2dis * max(max(fitting_count)) + 0.2)
                plt.tick_params(labelsize=16)
                guit.set_xlabel('Pulse Width Output/m', fontsize=12)
                guit.set_ylabel('Compensation Values/m', fontsize=12)
                guit.yaxis.label.set_color('blue')
                title = 'Distance Compensation vs PW CH ' + str(i + 1)
                plt.title(title, fontsize=12)
                # file_new_texname.writelines('Channel:' + str(i + 1) + '\n')
                if i == 31:
                    plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.5)
                    plt.savefig(path + '/result/' + 'Fitting2.png')
                    plt.show()
                    plt.close()
                    continue

            if i > 31 and i < 48:
                kt_6 = plt.figure(7, figsize=(25, 12))
                guit = kt_6.add_subplot(4, 4, i - 31)
                guit.grid(True)
                guit.scatter(samples_sub_dis, values_sub_dis, alpha=1, s=100, c='r', marker='*')
                plt.ylim(min(values[~np.isnan(values)]) - 0.1, max(values[~np.isnan(values)]) + 0.1)
                plt.tick_params(labelsize=16)
                guit.scatter(8 * count2dis * np.arange(index_start_reduce[-1], index_end_reduce[-1] + 1),
                             count2dis * np.array(fitting_count[i]), alpha=0.5, s=50, color='b', marker='.')
                # plt.ylim(-0.1, count2dis * max(max(fitting_count)) + 0.2)
                plt.tick_params(labelsize=16)
                guit.set_xlabel('Pulse Width Output/m', fontsize=12)
                guit.set_ylabel('Compensation Values/m', fontsize=12)
                guit.yaxis.label.set_color('blue')
                title = 'Distance Compensation vs PW CH ' + str(i + 1)
                plt.title(title, fontsize=12)
                # file_new_texname.writelines('Channel:' + str(i + 1) + '\n')
                if i == 47:
                    plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.5)
                    plt.savefig(path + '/result/' + 'Fitting3.png')
                    plt.show()
                    plt.close()
                    continue

            if i > 47:
                kt_7 = plt.figure(8, figsize=(25, 12))
                guit = kt_7.add_subplot(4, 4, i - 47)
                guit.grid(True)
                guit.scatter(samples_sub_dis, values_sub_dis, alpha=1, s=100, c='r', marker='*')
                plt.ylim(min(values[~np.isnan(values)]) - 0.1, max(values[~np.isnan(values)]) + 0.1)
                plt.tick_params(labelsize=16)
                guit.scatter(8 * count2dis * np.arange(index_start_reduce[-1], index_end_reduce[-1] + 1),
                             count2dis * np.array(fitting_count[i]), alpha=0.5, s=50, color='b', marker='.')
                # plt.ylim(-0.1, count2dis * max(max(fitting_count)) + 0.2)
                plt.tick_params(labelsize=16)
                guit.set_xlabel('Pulse Width Output/m', fontsize=12)
                guit.set_ylabel('Compensation Values/m', fontsize=12)
                guit.yaxis.label.set_color('blue')
                title = 'Distance Compensation vs PW CH ' + str(i + 1)
                plt.title(title, fontsize=12)
                # file_new_texname.writelines('Channel:' + str(i + 1) + '\n')
                if i == 63:
                    plt.subplots_adjust(left=0.04, bottom=0.06, right=0.96, top=0.96, wspace=0.25, hspace=0.5)
                    plt.savefig(path + '/result/' + 'Fitting4.png')
                    plt.show()
                    plt.close()
                    continue

        output = []
        for i in range(channel_number):
            output.append([])

        for i in range(channel_number):
            output[i].append(hex(index_start_reduce[i]).replace('0x', '').zfill(2))
            output[i].append(hex(index_end_reduce[i]).replace('0x', '').zfill(2))
            for k in range(0, 254):
                if k < len(fitting_count[i]):
                    output[i].append(hex(fitting_count[i][k]).replace('0x', '').zfill(2))
                else:
                    output[i].append(hex(0).replace('0x', '').zfill(2))

        sumoutput = []
        for i in range(16):
            sumoutput.append(list(zip(output[0 + 4 * i], output[1 + 4 * i], output[2 + 4 * i], output[3 + 4 * i])))
            for j in range(256):
                sumstr = ''.join(sumoutput[i][j])
                file_new_texname.writelines(sumstr + '\n')
        file_new_texname.close()

        print('Finish')

if  __name__ == "__main__":
   app = QApplication(sys.argv)
   form=Qmycali()
   form.show()
   #sys.exit(app.exec_())
   app.exec_()