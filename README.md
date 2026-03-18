
<div align="center">
	<img src="https://img.icons8.com/color/96/000000/hand-sign.png" width="80"/>
  
	<h1>🤟 EmoSign</h1>
	<p><b>Real-time Sign Language Learning & Translation App</b></p>
	<p>
		<img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white"/>
		<img src="https://img.shields.io/badge/PySide6-Qt-green?logo=qt&logoColor=white"/>
		<img src="https://img.shields.io/badge/MediaPipe-vision-orange?logo=google&logoColor=white"/>
		<img src="https://img.shields.io/badge/Keras-ML-red?logo=keras&logoColor=white"/>
	</p>
	<sub>Hybrid ML (heuristics + Keras static/dynamic models)</sub>
</div>


---

## ✨ Features

🎥 <b>Live Camera Translation</b> — auto-detects letters, words, and sentence patterns<br>
🧑‍🎓 <b>Study & Quiz Modes</b> — with image/video prompts<br>
⏰ <b>Smart Review Scheduler</b> — spaced repetition for weak/due signs<br>
📖 <b>Tutorial Flows</b> & in-app <b>Features Guide</b><br>
⚙️ <b>Unified Settings</b> — account & appearance<br>
📊 <b>Analytics, Streaks, Achievements</b>, export, and history<br>
🔊 <b>Optional Voice Output</b> for translations


## 🛠️ Tech Stack

- <img src="https://img.icons8.com/color/24/qt.png"/> <b>UI:</b> PySide6 (Qt)
- <img src="https://img.icons8.com/color/24/opencv.png"/> <b>Vision:</b> MediaPipe + OpenCV
- <img src="https://img.icons8.com/color/24/keras.png"/> <b>ML:</b> Keras (static MLP + dynamic LSTM), heuristic fallback
- <img src="https://img.icons8.com/color/24/sqlite.png"/> <b>Backend/Data:</b> SQLite + JSON analytics


## 📁 Project Structure

<details>
<summary>Click to expand</summary>

- <b>main.py</b> — app entry point
- <b>ui/</b> — window, pages, widgets, styling
- <b>ml/</b> — classifiers, gesture pipeline, trainers
- <b>detector/</b> — camera, hand/face tracking, feature extraction
- <b>core/</b> — translation engine, analytics, scheduler, exports, voice
- <b>backend/</b> — DB services
- <b>assets/</b> — reference images/videos for learning and quiz
- <b>models/</b> — pretrained hand/gesture models

</details>


## 🚀 Quick Start

<ol>
	<li><b>Install dependencies</b></li>
</ol>

```bash
pip install -r requirements.txt
```

<ol start="2">
	<li><b>Run the app</b></li>
</ol>

```bash
python main.py
```


## 📝 Key Product Notes

- 🛠️ <b>Settings + Profile merged</b> into one sidebar tab: <code>Settings</code>
- 🆕 Added new sidebar tab: <code>Features</code>
- 🔕 Notification action removed from Settings account actions
- 📧 Help dialog contact email/GitHub lines removed
- 😊 Live emotion display is a readable, non-blinking badge
- 🖼️ In-frame emotion text overlay is disabled for cleaner Live UI
- ✋ Z/J false triggers reduced with stricter movement gating in <code>ml/gesture_pipeline.py</code>


## 💡 Tips for Best Recognition

🤚 <b>Keep hand fully visible and well lit</b><br>
🖼️ <b>Avoid busy backgrounds</b><br>
✋ <b>Hold static signs briefly before switching</b><br>
🔄 <b>Use deliberate motion for dynamic signs (like J/Z)</b>

---

<div align="center">
	<img src="https://img.icons8.com/color/48/000000/american-sign-language-interpreting.png"/>
	<br><b>Happy Signing!</b>
</div>

