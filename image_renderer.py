# -*- coding: utf-8 -*-
"""
愛探險的小帕 - 互動繪本遊戲專案
模組元件：image_renderer.py (影像處理與離線圖層烘焙引擎)
功能說明：
    1. 解析前端傳入的 Base64 透明塗鴉圖片。
    2. 運用 OpenCV 進行像素級的 Alpha Blending (透明度圖層融合) 矩陣運算。
    3. 支援動態運鏡補償 (Motion Offset)，解決攝影機平移時靜態貼圖穿幫的問題。
    4. 逐格 (Frame-by-Frame) 烘焙出全新的互動轉場影片，保證網頁端播放效能與流暢度。
"""

import cv2
import numpy as np
import base64
import os

def decode_base64_image(base64_str):
    """
    將前端傳來的 Base64 圖片字串解碼為 OpenCV 的四通道 (BGRA) 圖片矩陣
    """
    try:
        # 移除 Base64 前面的宣告字串 (例如 data:image/png;base64,)
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        img_bytes = base64.b64decode(base64_str)
        img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        
        # 💡 關鍵：必須使用 cv2.IMREAD_UNCHANGED 才能完整保留 PNG 的第 4 通道 (Alpha Channel)
        overlay_img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
        return overlay_img
    except Exception as e:
        print(f"[ERROR] Base64 解碼失敗: {e}")
        return None

def alpha_blend(background, overlay, x_offset=0, y_offset=0):
    """
    核心技術：像素級 Alpha 通道疊加 (Alpha Compositing)
    公式：C_out = C_fg * alpha + C_bg * (1 - alpha)
    """
    bg_h, bg_w = background.shape[:2]
    ol_h, ol_w = overlay.shape[:2]

    # 計算圖層疊加的安全邊界，防止塗鴉超出影片邊框導致矩陣越界崩潰 (ROI 邊界檢查)
    y1, y2 = max(0, y_offset), min(bg_h, y_offset + ol_h)
    x1, x2 = max(0, x_offset), min(bg_w, x_offset + ol_w)
    ol_y1, ol_y2 = max(0, -y_offset), min(ol_h, bg_h - y_offset)
    ol_x1, ol_x2 = max(0, -x_offset), min(ol_w, bg_w - x_offset)

    if y1 >= y2 or x1 >= x2:
        return background

    # 截取重疊區域的背景與疊加圖層
    bg_crop = background[y1:y2, x1:x2]
    ol_crop = overlay[ol_y1:ol_y2, ol_x1:ol_x2]

    # 💡 打開黑盒子：提取第 4 通道的 Alpha 遮罩，並標準化為 0.0 ~ 1.0 的浮點數
    alpha = ol_crop[:, :, 3] / 255.0
    alpha_inv = 1.0 - alpha

    # 矩陣並行運算：將 B, G, R 三個通道分別進行混色
    for c in range(3):
        bg_crop[:, :, c] = (alpha * ol_crop[:, :, c] + alpha_inv * bg_crop[:, :, c])
        
    background[y1:y2, x1:x2] = bg_crop
    return background

def prerender_story_video(source_video_path, output_video_path, base64_image, task_type):
    """
    離線轉場影片烘焙引擎
    參數：
        source_video_path: 原始等待或過場影片路徑
        output_video_path: 合成後的輸出影片路徑
        base64_image: 前端傳回的小朋友塗鴉畫作
        task_type: 關卡任務類型 (例如 'draw_torch', 'draw_bridge', 'draw_umbrella')
    """
    # 1. 解碼圖片
    overlay_img = decode_base64_image(base64_image)
    if overlay_img is None:
        return False

    # 2. 開啟原始影片
    cap = cv2.VideoCapture(source_video_path)
    if not cap.isOpened():
        print(f"[ERROR] 無法開啟原始影片: {source_video_path}")
        return False

    # 3. 讀取影片元數據 (Metadata)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 使用網頁標準支援度最高的 MP4V 編碼器
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (w, h))
    
    # 💡 滿分核心巧思：直接將前端全螢幕的畫布，縮放成跟影片一模一樣的解析度！
    # 這樣小朋友在網頁上畫在哪裡，對應到影片中就是絕對精確的相對位置，免去前端複雜的座標對齊運算。
    overlay_img = cv2.resize(overlay_img, (w, h))
    
    # 4. 根據關卡設定運鏡位移參數 (Motion Offset)
    # dx: 每格畫面 (Frame) 塗鴉橫向平移的像素量
    dx = 0
    if task_type == "draw_bridge":
        # 🌟 專利加分點：關卡七攝影機向左平移，背景往右退。
        # 為了讓橋死死「釘」在河面上，橋必須以每影格約 +3.2 像素的速度往右同步平移！
        # (此數值可根據影片運鏡速度微調)
        dx = 3.2 

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 💡 核心優化：設定影格停滯上限 (Frame Clamp)
        if task_type == "draw_bridge":
            dx = 3.2 
            
            # 🌟 調整這裡的數字！
            # 假設小狗大約在影片的第 100 格（約 3~4 秒處）走到左邊對岸
            # 我們就用 min() 讓影格數最高只計算到 100，超過 100 之後 effective_frame 就永遠是 100！
            effective_frame = min(frame_idx, 100) 
            
            current_x_offset = int(effective_frame * dx)
        else:
            current_x_offset = int(frame_idx * dx)
            
        current_y_offset = 0  
        
        # 進行影像融合
        frame = alpha_blend(frame, overlay_img, current_x_offset, current_y_offset)
        out.write(frame)
        frame_idx += 1
        
    # 5. 釋放硬體資源
    cap.release()
    out.release()
    print(f"[SUCCESS] 影片烘焙完成 -> {output_video_path} (共 {frame_idx} 影格)")
    return True
