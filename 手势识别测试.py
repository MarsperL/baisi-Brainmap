import mediapipe as mp
import cv2

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
    handconstyle = draw.DrawingSpec(color=(255, 255, 255), thickness=2)  # 线的风格
    # 需要mp寻找视频流中的手部位置，并且将所有特征点提取出来
    results = hands.process(imgRGB)
    # 若找到手，则画出特征点
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            draw.draw_landmarks(img, handLms, mp.solutions.hands.HAND_CONNECTIONS,
                                handlmsstyle, handconstyle)
    return results.multi_hand_landmarks

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

# 获取hands，draw初始化的材象
hands = mp.solutions.hands.Hands()
draw = mp.solutions.drawing_utils
# 用opencv中的函数，打开摄像头
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 调用摄像头
img_shape = (800, 650)  # 显示图像的尺寸
count = 0 # 计数器
while True:
    # 不停的读取每一帧图像
    ret, img = cap.read()
    img = cv2.resize(img, img_shape)
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
        cv2.imshow("marsperL", img)  # 打开窗口
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '): # 如果按下空格键
            count += 1 # 计数器加1
            cv2.imwrite(f'gesture{count}.jpg', img) # 保存手势图片
            print(f'Gesture {count} saved!')
        elif key == ord('q'): # 如果按下q键
            break # 退出程序

    cv2.waitKey(1)
    if cv2.getWindowProperty('marsperL', cv2.WND_PROP_VISIBLE) < 1:
        break
cap.release()