// static/js/game.js 最終完美整合版

let currentVideoFile = "";
let currentTask = "";
let isGameEnded = false;
let storyLoop = null;
let activeClones = []; // 用來管理第十五關音符分身的陣列

// 音樂全局解鎖與修復機制
document.body.addEventListener('click', function() {
    let bgm = document.getElementById('bgm');
    if (bgm.paused && !isGameEnded) { bgm.play().catch(e=>{}); }
});

document.getElementById('start-btn').addEventListener('click', function() {
    document.getElementById('cover-page').style.opacity = '0';
    setTimeout(() => { document.getElementById('cover-page').style.display = 'none'; }, 1000);
    let bgm = document.getElementById('bgm');
    bgm.volume = 0.25; 
    bgm.play().catch(e=>{});
    fetchStory();
    storyLoop = setInterval(fetchStory, 1000);
});

// --- 點擊「我畫好了」按鈕邏輯 ---
document.getElementById('finish-draw-btn').addEventListener('click', function() {
    let drawingDataUrl = canvas.toDataURL('image/png');
    let artworkImg = document.getElementById('user-artwork');
    
    // 設定圖片來源
    artworkImg.src = drawingDataUrl;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height); 
    canvas.style.display = "none"; // 隱藏畫布
    
    let uiPanel = document.getElementById('ui-panel');
    let storyText = document.getElementById('story-text');
    storyText.innerHTML = "✨ 魔法生成中...請稍候...";
    document.getElementById('finish-draw-btn').style.display = "none";

    if (storyLoop) { clearInterval(storyLoop); storyLoop = null; }

    // 將圖片資料發送給後端
    fetch('/complete_drawing', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: drawingDataUrl })
    })
    .then(response => response.json())
    .then(data => {
        uiPanel.style.display = "none"; // 隱藏文字字卡
        document.getElementById('next-chapter-btn').style.display = "block"; // 顯示下一關按鈕

        if (data.play_action_video) {
            let videoPlayer = document.getElementById('bg-video');
            videoPlayer.onerror = function() { document.getElementById('next-chapter-btn').click(); };

            // 切換成成功展示影片
            videoPlayer.src = "/static/videos/" + data.play_action_video;
            
            // 💡 初始化：清除所有動態特效與類別
            artworkImg.style.transition = "none";
            artworkImg.style.transform = "translate(0px, 0px) scale(1)";
            artworkImg.classList.remove("anim-mic");

            videoPlayer.play().then(() => {
                // 🌟 混合架構：判斷關卡執行對應的前端固定位置位移
                if (data.completed_state !== "draw_bridge") {
                    artworkImg.style.display = "block"; // 顯示塗鴉圖層
                    void artworkImg.offsetWidth; // 強制網頁重繪
                    
                    // 設定 1 秒的平滑動態效果
                    artworkImg.style.transition = "transform 1.0s ease-out"; 
                    
                    // =============================================================
                    // 🎯 絕對固定位置調整區 (VW = 螢幕寬度百分比, VH = 螢幕高度百分比)
                    // =============================================================
                    if (data.completed_state === "draw_torch") {
                        // 關卡五火把：直接指定移到火炬上方的絕對位置
                        // (範例：往右移 25% 螢幕寬，往上移 15% 螢幕高，並縮小成 0.4 倍)
                        artworkImg.style.transform = "translate(10vw, -20vh) scale(0.4)"; 
                        
                    } else if (data.completed_state === "draw_umbrella") {
                        // 關卡十二雨傘：直接指定移到小帕頭頂的絕對位置
                        // (範例：水平不移動保持置中，往上移 18% 螢幕高，並縮小成 0.8 倍)
                        artworkImg.style.transform = "translate(0vw, -18vh) scale(0.8)";
                        
                    } else if (data.completed_state === "draw_mic") {
                        // 關卡十麥克風：移到小帕手部位置，並掛載晃動特效
                        artworkImg.style.transform = "translate(-10vw, 15vh) scale(0.5)";
                        setTimeout(() => { artworkImg.classList.add("anim-mic"); }, 1000);
                        
                    } else if (data.completed_state === "draw_note") {
                        // 關卡十五音符：隱藏原本的大圖，改用多重分身術在固定位置左右搖擺
                        artworkImg.style.display = "none"; 
                        
                        const positions = [
                            { left: "20vw", top: "15vh", delay: "0s" },
                            { left: "50vw", top: "10vh", delay: "0.5s" },
                            { left: "80vw", top: "20vh", delay: "1s" }
                        ];

                        positions.forEach(pos => {
                            let clone = document.createElement('img');
                            clone.src = drawingDataUrl;
                            clone.className = 'note-clone';
                            clone.style.left = pos.left;
                            clone.style.top = pos.top;
                            clone.style.animationDelay = pos.delay;
                            clone.style.width = "300px"; 
                            
                            document.getElementById('game-container').appendChild(clone);
                            activeClones.push(clone);
                        });
                    }
                } else {
                    // 關卡七 (橋)：使用後端 OpenCV 烘焙好的影片，前端圖片保持隱藏
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
    document.getElementById('ui-panel').style.display = "block"; 
    
    // 清除第十五關產生的音符分身
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
    
    // 💡 補上這一行：進入大結局時，強制把畫面上方的字卡徹底隱藏！
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
                
                // 更換任務時，重置所有前端塗鴉圖層
                artworkImg.style.transition = "none";
                artworkImg.style.transform = "translate(0px, 0px) scale(1)";
                artworkImg.style.display = "none";

                if (currentTask.startsWith("draw")) {
                    canvas.style.display = "block"; btn.style.display = "block"; camera.style.display = "none";
                    uiPanel.style.bottom = "auto"; uiPanel.style.top = "30px";
                    voiceIndicator.style.display = "none"; 
                } else if (currentTask === "voice_shout") {
                    voiceIndicator.style.display = "block";
                    if (recognition) { try { recognition.start(); } catch(e) {} }
                } else {
                    canvas.style.display = "none"; btn.style.display = "none"; voiceIndicator.style.display = "none";
                    camera.style.display = "block"; uiPanel.style.top = "auto"; uiPanel.style.bottom = "40px";
                    if (recognition) { try { recognition.stop(); } catch(e) {} }
                }
            }

            // 💡 【核心音訊 Bug 修復】：只要當前不是第 14 關語音大喊任務，就強迫恢復 BGM 音量
            // 這樣能徹底解決離開第 14 關進入第 15 關時，背景音樂被瀏覽器扣留的靈異現象！
            if (currentTask !== "voice_shout") {
                let bgm = document.getElementById('bgm');
                if (bgm.volume !== 0.25 || bgm.paused) {
                    bgm.volume = 0.25;
                    bgm.play().catch(e=>{});
                }
            }
        })
}