# -*- coding: utf-8 -*-
from flask import Flask, render_template, Response, jsonify, request
import cv2
from deepface import DeepFace
import time
import numpy as np
import atexit

app = Flask(__name__)
cap = cv2.VideoCapture(0)

SCENES = {
    "start": {"title": "第一章：音樂會之約", "content": "今天是森林大日子！小帕要舉辦一場音樂會。請對著鏡頭露出『開心的微笑』，我們出發吧！", "video": "scene01_start.mp4", "task": "emotion_happy", "next": "fog"},
    "fog": {"title": "第二章：迷霧森林", "content": "🌟 笑容真好看！<br><br>剛出發就起了大霧，看不見路了！請對著鏡頭『用力揮動雙手』，把迷霧吹散！", "video": "scene02_fog.mp4", "task": "motion_wave", "next": "magic_door"},
    "magic_door": {"title": "第三章：沉睡的石門", "content": "🌟 霧散開了！<br><br>前面有一扇巨大的魔法門擋住去路。請對著麥克風大喊『芝麻開門』來喚醒它！", "video": "scene03_door.mp4", "task": "voice_shout", "next": "dark_cave"},
    "dark_cave": {"title": "第四章：黑暗山洞", "content": "🌟 門打開了！<br><br>山洞裡好黑好可怕，小帕有點想哭... 請對鏡頭『皺起眉頭 (難過)』，陪他一起度過恐懼。", "video": "scene04_cave.mp4", "task": "emotion_sad", "next": "draw_torch"},
    "draw_torch": {"title": "第五章：點亮希望", "content": "🌟 謝謝你的陪伴！<br><br>我們需要一點光！請用滑鼠在畫面上『畫一把火炬』，照亮前面的路！", "video": "scene05_dark.mp4", "task": "draw_torch", "next": "bats"},
    "bats": {"title": "第六章：蝙蝠驚魂", "content": "🌟 亮起來了！<br><br>哇！突然飛出一大群蝙蝠！請對著鏡頭『張大嘴巴 (驚訝)』，把它們嚇跑！", "video": "scene06_bats.mp4", "task": "emotion_surprise", "next": "river"},
    "river": {"title": "第七章：地下暗河", "content": "🌟 蝙蝠飛走了！<br><br>糟糕，前面有一條又急又深的地底河流... 請在畫面上『畫出一座橋』幫助他過河！", "video": "scene07_river.mp4", "task": "draw_bridge", "next": "out_cave"},
    "out_cave": {"title": "第八章：重見光明", "content": "🌟 順利過河！<br><br>終於走出山洞了，外面的陽光好溫暖！請對著鏡頭露出『大大的微笑』！", "video": "scene08_sun.mp4", "task": "emotion_happy", "next": "lost_map"},
    "lost_map": {"title": "第九章：樂譜飛走了", "content": "🌟 繼續前進！<br><br>哎呀！一陣狂風把最重要的樂譜吹到了半空中！請趕快對著鏡頭『用力揮手』把它抓回來！", "video": "scene09_wind.mp4", "task": "motion_wave", "next": "find_instrument"},
    "find_instrument": {"title": "第十章：尋找樂器", "content": "🌟 抓到樂譜了！<br><br>現在小帕需要一個最棒的樂器來表演。小朋友，請在畫面上『畫一個麥克風』！", "video": "scene10_search.mp4", "task": "draw_mic", "next": "rain"},
    "rain": {"title": "第十一章：突如其來的大雨", "content": "🌟 麥克風真帥！<br><br>怎麼突然下大雨了？小帕淋成了落湯雞，好氣餒... 請對鏡頭『皺起眉頭 (難過)』幫他想辦法。", "video": "scene11_rain.mp4", "task": "emotion_sad", "next": "draw_umbrella"},
    "draw_umbrella": {"title": "第十二章：創造雨傘", "content": "🌟 不能放棄！<br><br>我們來幫小帕擋雨吧！請在畫面上『畫一把大雨傘』保護他和麥克風！", "video": "scene12_wet.mp4", "task": "draw_umbrella", "next": "family_rescue"},
    "family_rescue": {"title": "第十三章：家人的溫暖", "content": "🌟 畫得太好了！<br><br>家人們也帶著大雨傘趕來幫忙了，雨停了！請對著鏡頭露出『開心的笑容』謝謝家人！", "video": "scene13_family.mp4", "task": "emotion_happy", "next": "mic_test"},
    "mic_test": {"title": "第十四章：舞台測試", "content": "🌟 終於抵達舞台！<br><br>準備開始囉！請對著麥克風大喊一聲『Test Test！』，確認音響有沒有問題！", "video": "scene14_stage.mp4", "task": "voice_shout", "next": "concert"},
    "concert": {"title": "第十五章：浪漫R&B之夜", "content": "🌟 聲音很完美！<br><br>小帕唱起了帶有輕快 R&B 節奏的迷人旋律！請在畫面上『畫一個大音符』，讓氣氛嗨到最高點！", "video": "scene15_sing.mp4", "task": "draw_note", "next": "game_over"},
    "game_over": {"title": "冒險終點", "content": "精彩的冒險結束囉！", "video": "scene15_sing.mp4", "task": "none", "next": "none"}
}

current_state = "start"
last_trigger_time = 0

def advance_story():
    global current_state, last_trigger_time
    next_state = SCENES[current_state]["next"]
    if next_state != "none":
        current_state = next_state
        # 💡 修正 2：進入新章節時，強制把時間重置，給予 4 秒的「閱讀保護期」，避免 AI 秒殺過關
        last_trigger_time = time.time() 
        print(f"移動到最新狀態: {current_state}")

def generate_frames():
    global current_state, last_trigger_time
    prev_gray = None 
    while True:
        success, frame = cap.read()
        if not success: break
            
        frame = cv2.flip(frame, 1)
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        current_task = SCENES[current_state]["task"]
        oval_color = (255, 255, 255)
        
        if current_task.startswith("emotion"):
            try:
                results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                emotion_scores = results[0]['emotion']
                if current_task == "emotion_happy" and emotion_scores['happy'] > 60:
                    oval_color = (0, 200, 100)
                    if time.time() - last_trigger_time > 4:  # 等待 4 秒保護期結束後才放行
                        advance_story()
                elif current_task == "emotion_sad" and emotion_scores['sad'] > 60:
                    oval_color = (255, 100, 100)
                    if time.time() - last_trigger_time > 4:
                        advance_story()
                elif current_task == "emotion_surprise" and emotion_scores['surprise'] > 60:
                    oval_color = (200, 100, 255) 
                    if time.time() - last_trigger_time > 4:
                        advance_story()
            except: pass

        elif current_task == "motion_wave":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                motion_level = cv2.countNonZero(thresh)
                if motion_level > 15000: 
                    oval_color = (0, 255, 255) 
                    if time.time() - last_trigger_time > 4:
                        advance_story()
            prev_gray = gray

        cv2.ellipse(frame, (center_x, center_y), (120, 160), 0, 0, 360, oval_color, 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index(): 
    global current_state, last_trigger_time
    current_state = "start"  
    last_trigger_time = time.time()
    return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_story')
def get_story(): return jsonify(SCENES[current_state])

@app.route('/complete_drawing', methods=['POST'])
def complete_drawing():
    advance_story() 
    return jsonify({"status": "success"})

@app.route('/complete_voice', methods=['POST'])
def complete_voice():
    advance_story() 
    return jsonify({"status": "success"})

# 💡 效能救星 5：優雅關機機制，保證程式結束時徹底釋放攝影機與記憶體
def cleanup():
    print("\n正在關閉攝影機與釋放 AI 資源...")
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    print("資源釋放完畢，安全下線！")

# 註冊這個函數，只要程式一關閉就會自動執行
atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, port=5000)