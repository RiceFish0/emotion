# 愛探險的小帕 — 快速使用說明

簡短說明：本專案為以 Flask 提供前端互動介面的多模態情緒繪本示範，結合 OpenCV 與 DeepFace 做影像/情緒辨識。此 README 聚焦於「如何快速在本機上執行」與常見問題排除。

**環境需求**
- **Python**: 建議使用 Python 3.8 以上。
- **作業系統**: 開發建議在 Windows 10/11 或任何能執行 Python 的系統。

**重要檔案**
- 專案啟動器： [app.py](app.py)
- 前端頁面： [templates/index.html](templates/index.html)
- 相依套件： `requirements.txt`（若不存在，請參考下方安裝指令）

**快速開始（最小步驟）**
1. 建議先建立虛擬環境：

```powershell
python -m venv venv
# Windows（PowerShell）
venv\Scripts\Activate
```

2. 安裝套件：

如果 repository 已包含 `requirements.txt`：

```powershell
pip install -r requirements.txt
```

若沒有，請先安裝最小套件：

```powershell
pip install Flask opencv-python deepface
```

3. 啟動伺服器：

```powershell
python app.py
# 或使用 flask run（若已設定 FLASK_APP）
```

4. 開啟瀏覽器並前往： http://127.0.0.1:5000

**在不同作業系統的環境變數（可選）**
- Windows CMD： `set FLASK_APP=app.py`，然後 `flask run`
- macOS / Linux： `export FLASK_APP=app.py`，然後 `flask run`

**常見問題與排除**
- 相機無法啟動：請確認瀏覽器有允許相機權限，並在系統層級允許該應用程式使用相機。
- 麥克風/語音辨識失敗：建議使用 Google Chrome，並確認系統預設麥克風可用。
- DeepFace 初次下載模型很慢或失敗：DeepFace 會在第一次執行時下載權重，請保持網路連線；若網路受限，可考慮預先下載模型或在不同網路環境重試。

**建議的下一步（非必要）**
- 建立 `requirements.txt`（鎖定目前所需版本）。
- 若希望我為你生成 `requirements.txt`，或把 `app.py` 改成更「可打包執行」的範例（包含 CLI 與 config），我可以替你完成。

---
若需我直接幫你產生 `requirements.txt` 或把專案整理成可直接執行的範例，請回覆要我執行哪一項。
