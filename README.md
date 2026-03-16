# EmoSign

Real-time sign language learning and translation app built with Python, PySide6, MediaPipe, and hybrid ML (heuristics + Keras static/dynamic models).

## Highlights

- Live camera translation with auto-detection (letters, words, sentence patterns)
- Study + Quiz modes with image/video prompts
- Smart quiz review scheduler (spaced repetition for weak/due signs)
- Tutorial flows and a dedicated **Features** in-app guide
- Unified **Settings** page (account + appearance)
- Analytics, streaks, achievements, export, and history
- Optional voice output for translations

## Tech Stack

- **UI:** PySide6 (Qt)
- **Vision:** MediaPipe + OpenCV
- **ML:** Keras (static MLP + dynamic LSTM), heuristic fallback
- **Backend/Data:** SQLite + JSON analytics

## Project Structure

- `main.py` — app entry point
- `ui/` — window, pages, widgets, styling
- `ml/` — classifiers, gesture pipeline, trainers
- `detector/` — camera, hand/face tracking, feature extraction
- `core/` — translation engine, analytics, scheduler, exports, voice
- `backend/` — DB services
- `assets/` — reference images/videos for learning and quiz
- `models/` — pretrained hand/gesture models

## Quick Start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Run the app

```bash
python main.py
```

## Key Product Notes (Current)

- **Settings + Profile merged** into one sidebar tab: `Settings`
- Added new sidebar tab: `Features`
- Notification action removed from Settings account actions
- Help dialog contact email/GitHub lines removed
- Live emotion display is a readable, non-blinking badge
- In-frame emotion text overlay is disabled for cleaner Live UI
- Z/J false triggers reduced with stricter movement gating in `ml/gesture_pipeline.py`

## Tips for Better Recognition

- Keep hand fully visible and well lit
- Avoid busy backgrounds
- Hold static signs briefly before switching
- Use deliberate motion for dynamic signs (like J/Z)

## License

Internal/Project-specific. Add a `LICENSE` file if you plan to open-source.
