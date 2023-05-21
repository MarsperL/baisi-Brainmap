import autopy
import numpy as np
import pyautogui
import cv2

import math

from login.win.close_dialog import close_dialog
from PyQt5.QtWidgets import QApplication
from cv2 import WINDOW_NORMAL
from pyqt5_plugins.examplebuttonplugin import QtGui

import mainwindow
from HandTrackingModule import handDetector, mp

# 如果两个特征点小于这个阈值，就认为这两个特征点重叠一起
dist_thresh = 100
dist_thresh1 = 80
dist_thresh2 = 120


# 找出图像中是否有手
def findHands(img, hands, draw):
    """找出图像中的手，并画出手部所有特征点
    img 视频流中每一帧图片
    hands mediapipe的手部solution对象
    draw  mediapipe的画图solution对象
    retur 手部的所有特征点
    """
    # 将图像由BGR转化为RGB
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # 定义轮廓的画图风格
    handlmsstyle = draw.DrawingSpec(color=(0, 0, 255), thickness=5)
    handconstyle = draw.DrawingSpec(color=(255, 255, 255), thickness=5)  # 线的风格
    # 需要mp寻找视频流中的手部位置，并且将所有特征点提取出来
    results = hands.process(imgRGB)
    # 若找到手，则画出特征点
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            draw.draw_landmarks(img, handLms, mp.solutions.hands.HAND_CONNECTIONS,
                                handlmsstyle, handconstyle)
    return results.multi_hand_landmarks


started_feature: bool = True  # 判断是否开始进行手势识别的标志


# 根据手势识别数字
def detectNumber(hand_landmarks, img):
    """设别数字
    hand_landmarks 手部特征
    img  图像
    return  返回识别的数字，没有识别到数字，返回-1
    """
    # 图片的宽和高取出
    h, w, c = img.shape
    # 找到第一只手的特征，并提取出来
    myHand = hand_landmarks[0]
    hand_landmarks = myHand.landmark
    # print(myHand)
    # 找出所需手指特征点
    thumb_tip_id = 4
    index_finger_tip_id = 8
    middle_finger_mcp_id = 9
    middle_finger_tip_id = 12
    ring_finger_tip_id = 16
    pinky_tip_id = 20
    pinky_mcp_id = 17

    # 提取上述所有的特征点X坐标和y坐标
    # 提取y坐标
    thumb_tip_y = hand_landmarks[thumb_tip_id].y * h
    index_finger_tip_y = hand_landmarks[index_finger_tip_id].y * h
    middle_finger_tip_y = hand_landmarks[middle_finger_tip_id].y * h
    middle_finger_mcp_y = hand_landmarks[middle_finger_mcp_id].y * h
    ring_finger_tip_y = hand_landmarks[ring_finger_tip_id].y * h
    pinky_tip_y = hand_landmarks[pinky_tip_id].y * h
    pinky_mcp_y = hand_landmarks[pinky_mcp_id].y * h
    # 提取x坐标
    thumb_tip_x = hand_landmarks[thumb_tip_id].x * w
    index_finger_tip_x = hand_landmarks[index_finger_tip_id].x * w
    middle_finger_tip_x = hand_landmarks[middle_finger_tip_id].x * w
    middle_finger_mcp_x = hand_landmarks[middle_finger_mcp_id].x * w
    ring_finger_tip_x = hand_landmarks[ring_finger_tip_id].x * w
    pinky_tip_x = hand_landmarks[pinky_tip_id].x * w
    pinky_mcp_x = hand_landmarks[pinky_mcp_id].x * w

    # 计算大拇指到所有其他点的距离
    dist_thumb2index = math.sqrt((thumb_tip_x - index_finger_tip_x) ** 2
                                 + (thumb_tip_y - index_finger_tip_y) ** 2)  # 食指
    dist_thumb2middle = math.sqrt((thumb_tip_x - middle_finger_tip_x) ** 2
                                  + (thumb_tip_y - middle_finger_tip_y) ** 2)  # 中指
    dist_thumb2ring = math.sqrt((thumb_tip_x - ring_finger_tip_x) ** 2
                                + (thumb_tip_y - ring_finger_tip_y) ** 2)  # 无名指
    dist_thumb2pinky = math.sqrt((thumb_tip_x - pinky_tip_x) ** 2
                                 + (thumb_tip_y - pinky_tip_y) ** 2)  # 小指
    dist_thumb2pinkymcp = math.sqrt((thumb_tip_x - pinky_mcp_x) ** 2
                                    + (thumb_tip_y - pinky_mcp_y) ** 2)  # 小指的第四节点

    # 计算中指的第四节处与其他节点的距离
    dist_thumb1tip = math.sqrt((middle_finger_mcp_x - thumb_tip_x) ** 2
                               + (middle_finger_mcp_y - thumb_tip_y) ** 2)  # 拇指
    dist_thumb3index = math.sqrt((middle_finger_mcp_x - index_finger_tip_x) ** 2
                                 + (middle_finger_mcp_y - index_finger_tip_y) ** 2)  # 食指
    dist_thumb3middle = math.sqrt((middle_finger_mcp_x - middle_finger_tip_x) ** 2
                                  + (middle_finger_mcp_y - middle_finger_tip_y) ** 2)  # 中指
    dist_thumb3ring = math.sqrt((middle_finger_mcp_x - ring_finger_tip_x) ** 2
                                + (middle_finger_mcp_y - ring_finger_tip_y) ** 2)  # 无名指
    dist_thumb3pinky = math.sqrt((middle_finger_mcp_x - pinky_tip_x) ** 2
                                 + (middle_finger_mcp_y - pinky_tip_y) ** 2)  # 小指
    dist_thumb3pinkymcp = math.sqrt((middle_finger_mcp_x - pinky_mcp_x) ** 2
                                    + (middle_finger_mcp_y - pinky_mcp_y) ** 2)  # 小指的第四节点
    # print(dist_thumb1tip, dist_thumb3index, dist_thumb3middle, dist_thumb3ring, dist_thumb3pinky,dist_thumb3pinkymcp)
    # print(dist_thumb2index, dist_thumb2middle,dist_thumb2ring, dist_thumb2pinky,dist_thumb2pinkymcp)

    global started_feature
    # 手势是否开始的标志
    gesture_str = None
    # 在窗口上显示的数字字符串

    if hand_landmarks:
        # 判断手势识别是否开始
        # 识别数字5,开始进行手势识别
        if dist_thumb2pinky > dist_thresh and dist_thumb2index > dist_thresh and \
                dist_thumb2middle > dist_thresh and dist_thumb2ring > dist_thresh and \
                dist_thumb2pinkymcp > dist_thresh:
            gesture_str = "5:start"
            started_feature = True

        # 识别数字6,关闭手势识别
        elif dist_thresh < dist_thumb1tip and dist_thresh > dist_thumb3index and \
                dist_thresh > dist_thumb3middle and dist_thresh > dist_thumb3ring and \
                dist_thresh < dist_thumb3pinky:
            gesture_str = "6:stop"
            started_feature = False

        # 若开启手势识别，可用数字控制脑图相关功能
        if (started_feature == True):
            # 识别数字1
            if dist_thumb2pinky < dist_thresh and dist_thumb2index > dist_thresh and \
                    dist_thumb2middle < dist_thresh and dist_thumb2ring < dist_thresh:
                gesture_str = "1"
                pyautogui.hotkey('alt', 'z')  # 主题

            # 识别数字2
            elif dist_thumb2pinky < dist_thresh and dist_thumb2index > dist_thresh and \
                    dist_thumb2middle > dist_thresh and dist_thumb2ring < dist_thresh:
                gesture_str = "2"
                pyautogui.hotkey('alt', 'k')  # 子主题

            # 识别数字3
            elif dist_thumb2pinky < dist_thresh and dist_thumb2index > dist_thresh and \
                    dist_thumb2middle > dist_thresh and dist_thumb2ring > dist_thresh:
                gesture_str = "3"
                pyautogui.click(button='right')  # 右键菜单

            # 识别数字4
            elif dist_thumb2pinky > dist_thresh and dist_thumb2index > dist_thresh and \
                    dist_thumb2middle > dist_thresh and dist_thumb2ring > dist_thresh and \
                    dist_thumb2pinkymcp < dist_thresh:
                gesture_str = "4"
                pyautogui.click(clicks=2, button='left')  # 双击鼠标左键

            # 识别数字0
            elif dist_thumb2pinky < dist_thresh and dist_thumb2index < dist_thresh and \
                    dist_thumb2middle < dist_thresh and dist_thumb2ring < dist_thresh:
                gesture_str = "0"
                # quit() #关闭手势识别窗口

            # 识别数字7
            elif dist_thumb1tip < dist_thresh1 and dist_thumb3index > dist_thresh1 and dist_thumb3middle < \
                    dist_thresh1 and dist_thumb3ring < dist_thresh1 and dist_thumb3pinky > dist_thresh1 and \
                    dist_thumb3pinkymcp < dist_thresh1:
                gesture_str = "7"
                pyautogui.hotkey('win', 'h')  # 语音输入调用

            # 识别数字8
            elif dist_thumb2index > dist_thresh2 and dist_thumb2middle < dist_thresh2 and dist_thumb2ring > \
                    dist_thresh2 and dist_thumb2pinky > dist_thresh2 and dist_thumb2pinkymcp > dist_thresh2:
                gesture_str = "8"
                pyautogui.hotkey('ctrl', 'shift', 's')  # 另存为

                # 识别数字9
            elif dist_thumb2index < dist_thresh1 and dist_thumb2middle > dist_thresh1 and dist_thumb2ring > \
                    dist_thresh1 and dist_thumb2pinky > dist_thresh1 and dist_thumb2pinkymcp > dist_thresh1:
                gesture_str = "9"
                pyautogui.hotkey('delete')  # 删除

            # 识别数字10
            elif dist_thumb2index < dist_thresh1 and dist_thumb2middle > dist_thresh1 and dist_thumb2ring < \
                    dist_thresh1 and dist_thumb2pinky < dist_thresh1 and dist_thumb2pinkymcp < dist_thresh1:
                gesture_str = "10"
                pyautogui.hotkey('ctrl', 'z')  # 撤销

    return gesture_str

wCam, hCam = 648, 480
frameR = 100
smoothening = 7
cap = cv2.VideoCapture(0)  # 若使用笔记本自带摄像头则编号为0  若使用外接摄像头 则更改为1或其他编号
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
wScr, hScr = autopy.screen.size()
cTime = 0
detector = handDetector()

# 获取hands，draw初始化的材象
hands = mp.solutions.hands.Hands()
draw = mp.solutions.drawing_utils
# 用opencv中的函数，打开摄像头
# img_shape = (800, 650)  # 显示图像的尺寸
while True:
    # 不停的读取每一帧图像
    ret, img = cap.read()
    # img = cv2.resize(img, img_shape)
    img = detector.findHands(img)  # 检测手势并画上骨架信息
    lmList = detector.findPosition(img)  # 获取得到坐标点的列表
    close_mouse = False  # 停用鼠标的判断标志
    if (started_feature == True):  # 默认识别数字手势
        # 读取摄像数据图像
        if ret:
            hand_landmarks = findHands(img, hands, draw)
            if hand_landmarks:
                # 调用detectNumber函数识别手势数字
                detect_Number = detectNumber(hand_landmarks, img)
                if detect_Number:
                    # print(detect_Number)
                    cv2.putText(img, str(detect_Number),
                                (50, 200), 0, 4, (72, 118, 255), 3)
    elif (started_feature == False):  # 若手势为6，则停用数字手势识别，转化为使用鼠标
        # 启用虚拟鼠标
        if len(lmList) != 0:
            x0, y0 = lmList[4][1:]  # 拇指指尖的x，y坐标
            x1, y1 = lmList[8][1:]  # 食指尖的x，y坐标
            x2, y2 = lmList[12][1:]  # 中指尖的x，y坐标
            x3, y3 = lmList[16][1:]  # 无名指尖的x，y坐标
            x4, y4 = lmList[20][1:]  # 无名指尖的x，y坐标
            # 检查是否有手指竖起
            fingers = detector.fingersUp()
            cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                          (0, 255, 0), 2)  # 鼠标移动范围窗口
            # 3. 若只有食指伸出 则进入移动模式
            if fingers[1] == 1 and fingers[2] == 0:
                # 4. 坐标转换： 将食指在窗口坐标转换为鼠标在桌面的坐标
                # 鼠标坐标
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                # 平滑值
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening

                autopy.mouse.move(wScr - clocX, clocY)  # 移动鼠标
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)  # 为食指尖标一个大的点
                plocX, plocY = clocX, clocY

            # 5. 若是食指和中指都伸出 则检测指头距离 距离够短则对应鼠标点击
            if fingers[1] == 1 and fingers[2] == 1:
                length, img, pointInfo = detector.findDistance(8, 12, img)
                if length < 40:
                    cv2.circle(img, (pointInfo[4], pointInfo[5]),
                               15, (0, 255, 0), cv2.FILLED)
                    autopy.mouse.click()
            # 若五指全都伸出，则启动数字手势识别，停用鼠标
            if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and \
                    fingers[3] == 1 and fingers[4] == 1:
                cv2.circle(img, (x0, y0), 15, (255, 0, 255), cv2.FILLED)  # 为姆指尖标一个大的点
                cv2.circle(img, (x3, y3), 15, (255, 0, 255), cv2.FILLED)  # 为无名指尖标一个大的点
                cv2.circle(img, (x4, y4), 15, (255, 0, 255), cv2.FILLED)  # 为小指尖标一个大的点
                close_mouse = True  # 停用鼠标
        if close_mouse == True:  # 鼠标成功停用，则转化为数字手势识别
            started_feature = True
    cv2.namedWindow('marsperL',cv2.WINDOW_FREERATIO)#创建窗口，自适应窗口比例    # cv2.resizeWindow("marsperL", 800, 650);#设置窗口的固定大小
    cv2.imshow("marsperL", img)  # 打开窗口
    key = cv2.waitKey(1) & 0xFF
    cv2.waitKey(1)
    if cv2.getWindowProperty('marsperL', cv2.WND_PROP_VISIBLE) < 1:
        break
cap.release()
