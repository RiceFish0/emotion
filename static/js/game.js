// static/js/game.js 最終打磨版

let currentVideoFile = "";
let currentTask = "";
let isGameEnded = false;
let storyLoop = null;
let activeClones = []; 

// 音樂全局解鎖與修復機制
document.body.addEventListener('click', function() {
    let bgm = document.getElementById('bgm');
    if (bgm.paused && !isGameEnded) { bgm.play().catch(e=>{}); }
});

document.getElementById('start-btn').addEventListener('click', function() {
    document.getElementById('cover-page').style.opacity = '0';
    setTimeout(() => { document.getElementById('cover-page').style.display = 'none'; }, 1000);
    let bgm = document.getElementById('bgm');
    // 💡 修正 1：把初始音量從 0.25 調大到 0.6，一開始就能清楚聽見！
    bgm.volume = 0.6; 
    bgm.play().catch(e=>{});
    fetchStory();
    storyLoop = setInterval(fetchStory, 1000);
});

// --- 點擊「我畫好了」按鈕邏輯 ---
document.getElementById('finish-draw-btn').addEventListener('click', function() {
    let fullDataUrl = canvas.toDataURL('image/png'); // 給後端算橋用的全畫面
    let cropData = getCroppedImage(canvas, ctx);     // 💡 取得裁切後的新圖片與原始座標
    
    let artworkImg = document.getElementById('user-artwork');
    artworkImg.src = cropData.url; 
    
    // 💡 關鍵設定：解除全螢幕限制，並將圖片放在小朋友剛畫完的真實位置！
    artworkImg.style.width = "auto";
    artworkImg.style.height = "auto";
    artworkImg.style.left = cropData.cx + "px";
    artworkImg.style.top = cropData.cy + "px";
    artworkImg.style.transform = "translate(-50%, -50%) scale(1)";
    artworkImg.style.transition = "none";
    
    ctx.clearRect(0, 0, canvas.width, canvas.height); 
    canvas.style.display = "none"; 
    
    let uiPanel = document.getElementById('ui-panel');
    let storyText = document.getElementById('story-text');
    storyText.innerHTML = "✨ 魔法生成中...請稍候...";
    document.getElementById('finish-draw-btn').style.display = "none";

    if (storyLoop) { clearInterval(storyLoop); storyLoop = null; }

    fetch('/complete_drawing', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: fullDataUrl }) // 後端需要全螢幕資訊
    })
    .then(response => response.json())
    .then(data => {
        uiPanel.style.display = "none"; 
        document.getElementById('next-chapter-btn').style.display = "block"; 

        if (data.play_action_video) {
            let videoPlayer = document.getElementById('bg-video');
            videoPlayer.onerror = function() { document.getElementById('next-chapter-btn').click(); };

            videoPlayer.src = "/static/videos/" + data.play_action_video;
            artworkImg.classList.remove("anim-mic");

            videoPlayer.play().then(() => {
                if (data.completed_state !== "draw_bridge") {
                    artworkImg.style.display = "block"; 
                    void artworkImg.offsetWidth; 
                    
                    // 💡 開啟全屬性轉場，包含 left 和 top 也會平滑飛行 
                    
                    if (data.completed_state === "draw_torch") {
                        // 火把：絕對位置 (例如畫面的右方 75%，上方 35%)
                        artworkImg.style.transition = "all 1.0s ease-out";
                        artworkImg.style.left = "65vw";
                        artworkImg.style.top = "25vh";
                        artworkImg.style.transform = "translate(-50%, -50%) scale(0.6)";
                        
                    } else if (data.completed_state === "draw_umbrella") {
                        // 雨傘：絕對位置 (例如畫面正中央，上方 30%)
                        artworkImg.style.transition = "all 1.0s ease-out";
                        artworkImg.style.left = "50vw";
                        artworkImg.style.top = "40vh";
                        artworkImg.style.transform = "translate(-50%, -50%) scale(1.0)";
                        
                    } else if (data.completed_state === "draw_mic") {
                        // 麥克風：絕對位置 (小帕右手前)
                        artworkImg.style.transition = "none";
                        artworkImg.style.left = "38vw";
                        artworkImg.style.top = "55vh";
                        artworkImg.style.transform = "translate(-50%, -50%) scale(0.9)";
                        artworkImg.classList.add("anim-mic");
                        
                    } else if (data.completed_state === "draw_note") {
                        artworkImg.style.display = "none"; 
                        
                        const positions = [
                            { left: "10vw", top: "30vh", delay: "0s" },
                            { left: "28vw", top: "5vh", delay: "0s" },
                            { left: "75vw", top: "15vh", delay: "0s" }
                        ];

                        positions.forEach(pos => {
                            let clone = document.createElement('img');
                            clone.src = cropData.url; // 使用裁切後的大圖
                            clone.className = 'note-clone';
                            clone.style.left = pos.left;
                            clone.style.top = pos.top;
                            clone.style.animationDelay = pos.delay;
                            // 💡 巨大化設定：將分身寬度設為螢幕的 18%！
                            clone.style.width = "15vw"; 
                            
                            document.getElementById('game-container').appendChild(clone);
                            activeClones.push(clone);
                        });
                    }
                } else {
                    artworkImg.style.display = "none";
                }
            });

            videoPlayer.onended = function() {
                artworkImg.style.display = "none";
                artworkImg.classList.remove("anim-mic");
                videoPlayer.onended = null;
                videoPlayer.onerror = null;
            };
        } else {
            document.getElementById('next-chapter-btn').click();
        }
    })
    .catch(err => { document.getElementById('next-chapter-btn').click(); });
});

// --- 點擊「下一關」按鈕邏輯 ---
document.getElementById('next-chapter-btn').addEventListener('click', function() {
    document.getElementById('next-chapter-btn').style.display = "none";
    // 💡 修正 3：刪除了這裡的 uiPanel 顯示指令，把顯示的決定權交給後面的 fetchStory

    activeClones.forEach(clone => clone.remove());
    activeClones = [];

    fetch('/next_chapter', { method: 'POST' })
        .then(() => {
            if (!storyLoop) storyLoop = setInterval(fetchStory, 1000);
            fetchStory(); 
        });
});

document.getElementById('story-card').addEventListener('dblclick', function() {
    if (currentTask === "voice_shout") { fetch('/complete_voice', { method: 'POST' }).then(() => fetchStory()); }
});

// 畫布基礎設定
const canvas = document.getElementById('drawing-canvas');
const ctx = canvas.getContext('2d');
function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
window.addEventListener('resize', resizeCanvas); resizeCanvas();

let isDrawing = false;
function getPos(e) {
    let clientX = e.clientX || (e.touches && e.touches[0].clientX);
    let clientY = e.clientY || (e.touches && e.touches[0].clientY);
    return { x: clientX, y: clientY };
}
function startPosition(e) { isDrawing = true; const pos = getPos(e); ctx.beginPath(); ctx.moveTo(pos.x, pos.y); ctx.strokeStyle = '#FF5722'; ctx.lineWidth = 15; ctx.lineCap = 'round'; }
function draw(e) { if (!isDrawing) return; const pos = getPos(e); ctx.lineTo(pos.x, pos.y); ctx.stroke(); }
function endPosition() { isDrawing = false; }

canvas.addEventListener('mousedown', startPosition); canvas.addEventListener('mousemove', draw); canvas.addEventListener('mouseup', endPosition);
canvas.addEventListener('touchstart', startPosition); canvas.addEventListener('touchmove', draw); canvas.addEventListener('touchend', endPosition);

// 語音辨識驅動
let recognition = null;
try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-TW'; recognition.continuous = true; recognition.interimResults = true;
        
        recognition.onend = function() {
            if (currentTask === "voice_shout" && !isGameEnded) {
                try { recognition.start(); } catch(e) {}
            }
        };

        recognition.onresult = function(event) {
            const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
            if (currentTask === "voice_shout") {
                if (transcript.includes("開門") || transcript.includes("測試") || transcript.includes("帕") || transcript.includes("唱") || transcript.includes("一二三") || transcript.includes("嗨") || transcript.includes("test")) {
                    fetch('/complete_voice', { method: 'POST' }).then(() => fetchStory());
                }
            }
        };
    }
} catch(e) {}

function triggerEndPage() {
    if(isGameEnded) return;
    isGameEnded = true;
    if(storyLoop) { clearInterval(storyLoop); storyLoop = null; }
    
    // 大結局時，確保字卡強制隱藏
    document.getElementById('ui-panel').style.display = "none";
    
    let endPage = document.getElementById('end-page');
    let endVideo = document.getElementById('end-bg-video');
    endPage.style.display = 'flex';
    endPage.style.zIndex = "99999"; 
    setTimeout(() => { endPage.style.opacity = '1'; }, 100);
    endVideo.play().catch(e=>{});
}

// 監聽後端故事狀態
function fetchStory() {
    if(isGameEnded) return;
    fetch('/get_story')
        .then(response => response.json())
        .then(data => {
            if (data.task === "none") { triggerEndPage(); return; }

            // 💡 修正 3：系統確定這關「不是大結局」後，才把字卡顯示出來，解決閃爍問題！
            document.getElementById('ui-panel').style.display = "block";

            document.getElementById('story-title').innerText = data.title;
            document.getElementById('story-text').innerHTML = data.content;
            
            if(data.video !== currentVideoFile) {
                currentVideoFile = data.video;
                let videoPlayer = document.getElementById('bg-video');
                videoPlayer.src = "/static/videos/" + currentVideoFile;
                videoPlayer.load();
                videoPlayer.play().catch(e=>{});
            }

            let btn = document.getElementById('finish-draw-btn');
            let camera = document.getElementById('camera-box');
            let uiPanel = document.getElementById('ui-panel');
            let voiceIndicator = document.getElementById('voice-indicator');
            let artworkImg = document.getElementById('user-artwork');

            if (data.task !== currentTask) {
                currentTask = data.task;
                
                artworkImg.style.transition = "none";
                artworkImg.style.transform = "translate(0px, 0px) scale(1)";
                artworkImg.style.display = "none";

                if (currentTask.startsWith("draw")) {
                    canvas.style.display = "block"; btn.style.display = "block"; camera.style.display = "none";
                    uiPanel.style.bottom = "auto"; uiPanel.style.top = "30px";
                    voiceIndicator.style.display = "none"; 
                    // 💡 核心修復：進入繪畫關卡時，必須立刻強制關閉並釋放麥克風，背景音樂才會瞬間恢復大聲！
                    if (recognition) { try { recognition.stop(); } catch(e) {}}
                } else if (currentTask === "voice_shout") {
                    voiceIndicator.style.display = "block";
                    if (recognition) { try { recognition.start(); } catch(e) {} }
                } else {
                    canvas.style.display = "none"; btn.style.display = "none"; voiceIndicator.style.display = "none";
                    camera.style.display = "block"; uiPanel.style.top = "auto"; uiPanel.style.bottom = "40px";
                    if (recognition) { try { recognition.stop(); } catch(e) {} }
                }
            }

            // 💡 修正 1 進階控制：遇到語音關卡時變極小聲 (0.1)，其餘關卡恢復正常音量 (0.6)
            let bgm = document.getElementById('bgm');
            if (currentTask === "voice_shout") {
                bgm.volume = 0.2;
            } else {
                if (bgm.volume !== 0.6 || bgm.paused) {
                    bgm.volume = 0.6;
                    bgm.play().catch(e=>{});
                }
            }
        })
}
// ==========================================
// 💡 神級輔助：自動找出塗鴉真實邊界並裁切 (Auto-Crop)
// ==========================================
function getCroppedImage(canvas, ctx) {
    let w = canvas.width, h = canvas.height;
    let imgData = ctx.getImageData(0, 0, w, h).data;
    let top = h, left = w, right = 0, bottom = 0;
    let hasPixel = false;

    // 掃描所有像素，找出有顏色的上下左右邊界
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            if (imgData[(y * w + x) * 4 + 3] > 0) { 
                hasPixel = true;
                if (x < left) left = x;
                if (x > right) right = x;
                if (y < top) top = y;
                if (y > bottom) bottom = y;
            }
        }
    }
    if (!hasPixel) return { url: canvas.toDataURL(), cx: w/2, cy: h/2 };

    let pad = 15; // 留一點安全邊距
    left = Math.max(0, left - pad);
    top = Math.max(0, top - pad);
    right = Math.min(w, right + pad);
    bottom = Math.min(h, bottom + pad);

    let cropW = right - left, cropH = bottom - top;
    let tempCanvas = document.createElement('canvas');
    tempCanvas.width = cropW;
    tempCanvas.height = cropH;
    tempCanvas.getContext('2d').putImageData(ctx.getImageData(left, top, cropW, cropH), 0, 0);

    return {
        url: tempCanvas.toDataURL('image/png'),
        cx: left + cropW / 2, // 回傳塗鴉中心的 X 座標
        cy: top + cropH / 2   // 回傳塗鴉中心的 Y 座標
    };
}