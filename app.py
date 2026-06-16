# -*- coding: utf-8 -*-
from flask import Flask, render_template, Response, jsonify, request
import cv2
import time
import atexit

# 載入我們的兩大引擎
from image_renderer import prerender_story_video
from emotion_detector import VisionController

app = Flask(__name__)
cap = cv2.VideoCapture(0)
vision = VisionController()

SCENES = {
    "start": {"title": "第一章：音樂會之約", "content": "今天是森林大日子！小帕要舉辦一場音樂會。請對著鏡頭露出『開心的微笑』，我們出發吧！", "video": "scene01_start.mp4", "task": "emotion_happy", "next": "fog"},
    "fog": {"title": "第二章：迷霧森林", "content": "🌟 笑容真好看！<br><br>剛出發就起了大霧，看不見路了！請對著鏡頭『用力揮動雙手』，把迷霧吹散！", "video": "scene02_fog.mp4", "task": "motion_wave", "next": "magic_door"},
    "magic_door": {"title": "第三章：沉睡的石門", "content": "🌟 霧散開了！<br><br>前面有一扇巨大的魔法門擋住去路。請對著麥克風大喊『芝麻開門』來喚醒它！", "video": "scene03_door.mp4", "task": "voice_shout", "next": "dark_cave"},
    "dark_cave": {"title": "第四章：黑暗山洞", "content": "🌟 門打開了！<br><br>山洞裡好黑好可怕，小帕有點想哭... 請對鏡頭『皺起眉頭 (難過)』，陪他一起度過恐懼。", "video": "scene04_cave.mp4", "task": "emotion_sad", "next": "draw_torch"},
    "draw_torch": {"title": "第五章：點亮希望", "content": "🌟 謝謝你的陪伴！<br><br>我們需要一點光！請用滑鼠在畫面上『畫一把火』，點亮火炬照亮前面的路！", "video": "scene05_wait.mp4", "task": "draw_torch", "next": "bats"},
    "bats": {"title": "第六章：蝙蝠驚魂", "content": "🌟 亮起來了！<br><br>哇！突然飛出一大群蝙蝠！請對著鏡頭『張大嘴巴 (驚訝)』，把它們嚇跑！", "video": "scene06_bats.mp4", "task": "emotion_surprise", "next": "river"},
    "river": {"title": "第七章：地下暗河", "content": "🌟 蝙蝠飛走了！<br><br>糟糕，前面有一條又急又深的地底河流... 請在畫面上『畫出一座橋』幫助他過河！", "video": "scene07_wait.mp4", "task": "draw_bridge", "next": "out_cave"},
    "out_cave": {"title": "第八章：重見光明", "content": "🌟 順利過河！<br><br>終於走出山洞了，外面的陽光好溫暖！請對著鏡頭露出『大大的微笑』！", "video": "scene08_sun.mp4", "task": "emotion_happy", "next": "lost_map"},
    "lost_map": {"title": "第九章：樂譜飛走了", "content": "🌟 繼續前進！<br><br>哎呀！一陣狂風把最重要的樂譜吹到了半空中！請趕快對著鏡頭『用力揮手』把它抓回來！", "video": "scene09_wind.mp4", "task": "motion_wave", "next": "find_instrument"},
    "find_instrument": {"title": "第十章：尋找樂器", "content": "🌟 抓到樂譜了！<br><br>現在小帕需要一個最棒的樂器來表演。小朋友，請在畫面上『畫一個麥克風』！", "video": "scene10_search.mp4", "task": "draw_mic", "next": "rain"},
    "rain": {"title": "第十一章：突如其來的大雨", "content": "🌟 麥克風真帥！<br><br>怎麼突然下大雨了？小帕淋成了落湯雞，好氣餒... 請對鏡頭『皺起眉頭 (難過)』幫他想辦法。", "video": "scene11_rain.mp4", "task": "emotion_sad", "next": "draw_umbrella"},
    "draw_umbrella": {"title": "第十二章：創造雨傘", "content": "🌟 不能放棄！<br><br>我們來幫小帕擋雨吧！請在畫面上『畫一把大雨傘』保護小帕！", "video": "scene12_wait.mp4", "task": "draw_umbrella", "next": "family_rescue"},
    "family_rescue": {"title": "第十三章：家人的溫暖", "content": "🌟 畫得太好了！<br><br>家人們也帶著大雨傘趕來幫忙了，雨停了！請對著鏡頭露出『開心的笑容』謝謝家人！", "video": "scene13_family.mp4", "task": "emotion_happy", "next": "mic_test"},
    "mic_test": {"title": "第十四章：舞台測試", "content": "🌟 終於抵達舞台！<br><br>準備開始囉！請對著麥克風大喊一聲『Test Test！』，確認音響有沒有問題！", "video": "scene14_stage.mp4", "task": "voice_shout", "next": "concert"},
    "concert": {"title": "第十五章：浪漫R&B之夜", "content": "🌟 聲音很完美！<br><br>小帕唱起了帶有輕快 R&B 節奏的迷人旋律！請在畫面上『畫一個大音符』，讓氣氛嗨到最高點！", "video": "scene15_sing.mp4", "task": "draw_note", "next": "game_over"},
    "game_over": {"title": "冒險終點", "content": "精彩的冒險結束囉！", "video": "scene15_sing.mp4", "task": "none", "next": "none"}
}

ACTION_VIDEOS = {
    "draw_torch": "scene05_action.mp4",    # 關卡五
    "draw_bridge": "scene07_walk.mp4",     # 關卡七 (需要烘焙)
    "draw_mic": "scene10_found.mp4",      # 關卡十 (前端瞬移)
    "draw_umbrella": "scene12_happy.mp4",  # 關卡十二
    "draw_note": "scene15_sing.mp4"        # 關卡十五
}

current_state = "start"
last_trigger_time = 0

def advance_story():
    global current_state, last_trigger_time
    next_state = SCENES[current_state]["next"]
    if next_state != "none":
        current_state = next_state
        last_trigger_time = time.time() 

def generate_frames():
    global current_state, last_trigger_time
    while True:
        success, frame = cap.read()
        if not success: break
            
        frame = cv2.flip(frame, 1)
        current_task = SCENES[current_state]["task"]
        
        # 呼叫大腦處理影像
        processed_frame, should_advance = vision.process_frame(frame, current_task, last_trigger_time)
        
        if should_advance:
            advance_story()

        ret, buffer = cv2.imencode('.jpg', processed_frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index(): 
    global current_state, last_trigger_time
    current_state = "start"  
    last_trigger_time = time.time()
    return render_template('index.html')

@app.route('/video_feed')
def video_feed(): 
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_story')
def get_story(): 
    return jsonify(SCENES[current_state])

@app.route('/complete_drawing', methods=['POST'])
def complete_drawing():
    global current_state
    
    # 接收前端數據
    data = request.json
    base64_str = data.get('image_data', '')
    current_task = SCENES[current_state]["task"]
    
    # 取得對應的成功展示影片路徑
    action_video_filename = ACTION_VIDEOS.get(current_task, "")
    action_video_api_path = "" # 這是要交給前端播放的 API 路徑

    if action_video_filename:
        # 💡 核心邏輯：區分是否需要「後端烘焙」
        if current_task == "draw_bridge":
            # 🌟 只有第七關(橋)需要後端 OpenCV 離線算圖，解決鏡頭平移
            source_path = f"static/videos/{action_video_filename}"
            output_filename = f"generated_{action_video_filename}"
            output_path = f"static/videos/{output_filename}"
            
            # 執行耗時的算圖工作
            prerender_story_video(source_path, output_path, base64_str, current_task)
            
            # 回傳生成的影片檔名，加上時間戳記防快取
            action_video_api_path = f"{output_filename}?t={int(time.time())}"
        else:
            # 🌟 其他關卡 (火把、雨傘、音符) 攝影機沒動，回傳「原始影片」即可！
            # 後續交給前端 CSS 進行 0 延遲位移與縮放。
            action_video_api_path = action_video_filename

    return jsonify({
        "status": "success", 
        "play_action_video": action_video_api_path,
        "completed_state": current_task
    })
    
@app.route('/next_chapter', methods=['POST'])
def next_chapter():
    advance_story()
    return jsonify({"status": "success"})

@app.route('/complete_voice', methods=['POST'])
def complete_voice():
    advance_story() 
    return jsonify({"status": "success"})

def cleanup():
    print("\n正在關閉攝影機與釋放資源...")
    if cap.isOpened(): cap.release()
    cv2.destroyAllWindows()

atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, port=5000)