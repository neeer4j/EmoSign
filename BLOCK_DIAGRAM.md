# EmoSign v3.0 - System Block Diagram
*Sign Language Translator - High-Level Architecture*

---

## System Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Main Window │  │ Live Trans. │  │ Video Trans.│  │  Learning   │        │
│  │   (PySide6) │  │    Page     │  │    Page     │  │    Pages    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼─────────────────┼───────────────┼───────────────┘
          │                │                 │               │
          ▼                ▼                 ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DETECTION LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Camera    │  │    Video    │  │    Hand     │  │  Feature    │        │
│  │   Handler   │◄─┤   Handler   │──┤   Tracker   │──┤  Extractor  │        │
│  └──────┬──────┘  └─────────────┘  └─────────────┘  └──────┬──────┘        │
│         │                (MediaPipe)                        │               │
└─────────┼───────────────────────────────────────────────────┼───────────────┘
          │                                                   │
          ▼                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BUSINESS LOGIC LAYER                             │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐  ┌─────────────┐
│  │  Gesture Pipeline │  │  Sequence Buffer  │  │  Sentence   │  │   Gesture   │
│  │ (MLP/LSTM/Heuristic)│──┤ (Majority Vote)   │──┤    Mapper   │──┤  Dictionary │
│  └─────────┬─────────┘  └───────────────────┘  └─────────────┘  └─────────────┘
│            │                                                                   │
│  ┌─────────┴─────────┐                                                       │
│  │  Translation Engine │                                                       │
│  └─────────┬─────────┘                                                       │
└─────────────┼─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               DATA LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   SQLite    │  │  ML Models  │  │   Assets    │                         │
│  │  Database   │  │  (.keras)   │  │   (Media)   │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Presentation Layer (UI)
| Component | Technology | Purpose |
|-----------|------------|---------|
| Main Window | PySide6 | Application shell & navigation |
| Live Translation | PySide6 | Real-time camera translation |
| Video Translation | PySide6 | Video file processing |
| Learning Pages | PySide6 | Tutorials & sign library |

### Detection Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Camera Handler | OpenCV | Webcam frame capture |
| Video Handler | OpenCV | Video file processing |
| Hand Tracker | MediaPipe | Hand landmark detection |
| Feature Extractor | NumPy | Extract 63D feature vectors |

### Business Logic Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Gesture Pipeline | Python/Keras | Orchestrates ML/heuristic classification |
| Sequence Buffer | Python | Majority-vote smoothing (5 frames) |
| Sentence Mapper | Python | Map gestures to sentences |
| Translation Engine | Python | Coordinate translation pipeline |

### Data Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| SQLite Database | SQLite3 | User data & translation history |
| ML Models | Keras | Trained classifier models (.keras) |
| Assets | Various | Images, sounds, media files |

---

## Data Flow Summary

```plantuml
@startuml
participant UI as "UI Layer"
participant Cam as "Camera Widget"
participant Track as "Hand Tracker"
participant Norm as "Landmark Normalizer"
participant Pipe as "Gesture Pipeline"
participant MLP as "Keras MLP"
participant LSTM as "Keras LSTM"
participant Eng as "Translation Engine"
participant Buf as "Sequence Buffer"
participant Map as "Sentence Mapper"
participant Voice as "Voice Output"
participant DB as "Database"

User->>UI: Click Start Translation
UI->>Cam: start()

loop Every Frame
    Cam->>Track: process_frame(frame)
    Track->>Track: detect_hands()
    Track-->>Norm: hand_landmarks
    Norm->>Norm: normalize(wrist, palm)
    Norm-->>Pipe: 63-feature vector

    alt Movement < Threshold (Static Sign)
        Pipe->>MLP: predict(frame)
        MLP-->>Pipe: label, conf
    else Movement >= Threshold (Dynamic Sign)
        Pipe->>Pipe: buffer(30 frames)
        Pipe->>LSTM: predict(sequence)
        LSTM-->>Pipe: label, conf
    end

    Pipe->>Pipe: majority_vote(5 frames)
    Pipe-->>Eng: final_label, confidence
    Eng->>Buf: add_gesture(label)
    Buf->>Buf: check_for_sentence_completion()
    Buf-->>Map: completed_sequence
    Map->>Map: map_to_sentence()
    Map-->>UI: translated_text
    UI->>Voice: speak(translated_text)
    UI->>DB: save_translation(translated_text)
end

User->>DB: Login/Register
DB->>DB: authenticate_user()
DB-->>UI: session_token
@enduml
```

---

## Key Technologies

- **GUI Framework**: PySide6 (Qt for Python)
- **Computer Vision**: OpenCV, MediaPipe
- **Machine Learning**: TensorFlow 2.x, Keras
- **Database**: SQLite3
- **Text-to-Speech**: pyttsx3

---

*Generated for EmoSign v3.0 - Sign Language Translator*
