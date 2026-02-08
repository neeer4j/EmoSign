# EmoSign v3.0 - System Diagrams
*Sign Language Translator - Technical Documentation*

---

## 1. Entity Relationship (ER) Diagram

```mermaid
erDiagram
    USERS {
        string id PK
        string email UK
        string password_hash
        string salt
        timestamp created_at
    }
    
    SESSIONS {
        string id PK
        string user_id FK
        string token UK
        timestamp created_at
        timestamp expires_at
    }
    
    TRANSLATIONS {
        string id PK
        string user_id FK
        string sign_label
        float confidence
        string gesture_type
        timestamp created_at
    }
    
    USERS ||--o{ SESSIONS : "has"
    USERS ||--o{ TRANSLATIONS : "creates"
```

---

## 2. Use Case Diagram

```mermaid
flowchart TB
    subgraph Actors
        U((User))
        A((Admin))
        G((Guest))
    end
    
    subgraph "Authentication"
        UC1[Sign Up]
        UC2[Login]
        UC3[Logout]
        UC4[Change Password]
    end
    
    subgraph "Core Translation"
        UC5[Live Camera Translation]
        UC6[Video File Translation]
        UC7[Text to Sign]
        UC8[View Translation History]
        UC9[Export Translation]
    end
    
    subgraph "Learning"
        UC10[View Tutorials]
        UC11[Browse Sign Library]
        UC12[Train Custom Gestures]
    end
    
    subgraph "Settings & Analytics"
        UC13[View Analytics]
        UC14[Configure Settings]
        UC15[Toggle Theme]
    end
    
    subgraph "Admin Functions"
        UC16[Manage Users]
        UC17[View System Stats]
    end
    
    U --> UC1 & UC2 & UC3 & UC4
    U --> UC5 & UC6 & UC7 & UC8 & UC9
    U --> UC10 & UC11 & UC12
    U --> UC13 & UC14 & UC15
    
    G --> UC5 & UC6 & UC10 & UC11
    
    A --> UC16 & UC17
    A --> UC2 & UC3
```

---

## 3. Data Flow Diagram (DFD) - Level 0

```mermaid
flowchart LR
    U((User)) --> |"Hand Gestures"| P[Sign Language Translator System]
    U --> |"Video File"| P
    U --> |"Text Input"| P
    U --> |"Login Credentials"| P
    
    P --> |"Translation Text"| U
    P --> |"Voice Output"| U
    P --> |"Sign Visualization"| U
    P --> |"Analytics & Stats"| U
    
    P <--> |"User Data"| DB[(SQLite Database)]
    P <--> |"ML Models"| M[(Models)]
```

---

## 4. Data Flow Diagram (DFD) - Level 1

```mermaid
flowchart TB
    subgraph External
        U((User))
        CAM[Camera]
        VID[Video File]
    end
    
    subgraph "1.0 Input Processing"
        P1[Camera Widget]
        P2[Video Player]
        P3[Hand Tracker]
    end
    
    subgraph "2.0 Feature Extraction"
        P4[Feature Extractor]
        P5[Dynamic Gesture Detector]
    end
    
    subgraph "3.0 Recognition"
        P6[ML Classifier]
        P7[Heuristic Classifier]
    end
    
    subgraph "4.0 Translation Engine"
        P8[Sequence Buffer]
        P9[Sentence Mapper]
        P10[Translation Engine]
    end
    
    subgraph "5.0 Output"
        P11[UI Display]
        P12[Voice Output]
        P13[Export Manager]
    end
    
    subgraph Storage
        DB[(Database)]
        ML[(ML Models)]
    end
    
    CAM --> P1 --> P3
    VID --> P2 --> P3
    P3 --> P4 --> P6
    P3 --> P5 --> P10
    P6 --> P10
    P7 --> P10
    ML --> P6
    P10 --> P8 --> P9 --> P11
    P10 --> P12
    P11 --> P13
    P10 --> DB
    U --> P11
```

---

## 5. Activity Diagram - Live Translation Flow

```mermaid
flowchart TD
    A([Start]) --> B{User Logged In?}
    B -->|No| C[Show Login Page]
    C --> D[User Enters Credentials]
    D --> E{Valid Credentials?}
    E -->|No| C
    E -->|Yes| F[Navigate to Dashboard]
    B -->|Yes| F
    
    F --> G[Select Live Translation]
    G --> H[Initialize Camera]
    H --> I{Camera Available?}
    I -->|No| J[Show Error Message]
    J --> F
    I -->|Yes| K[Start Frame Capture]
    
    K --> L[Detect Hand Landmarks]
    L --> M{Hand Detected?}
    M -->|No| K
    M -->|Yes| N[Extract Features]
    
    N --> O[ML Classification]
    O --> P[Add to Sequence Buffer]
    P --> Q{Gesture Stable?}
    Q -->|No| K
    Q -->|Yes| R[Confirm Gesture]
    
    R --> S{Inactivity Timeout?}
    S -->|No| K
    S -->|Yes| T[Map to Sentence]
    
    T --> U[Display Translation]
    U --> V[Speak Output]
    V --> W[Save to History]
    W --> X{Continue?}
    X -->|Yes| K
    X -->|No| Y([End])
```

---

## 6. Sequence Diagram - Translation Process

```mermaid
sequenceDiagram
    actor User
    participant UI as UI Layer
    participant Cam as Camera Widget
    participant Track as Hand Tracker
    participant Feat as Feature Extractor
    participant ML as ML Classifier
    participant Eng as Translation Engine
    participant Buf as Sequence Buffer
    participant Map as Sentence Mapper
    participant Voice as Voice Output
    participant DB as Database

    User->>UI: Click Start Translation
    UI->>Cam: start()
    
    loop Every Frame
        Cam->>Track: process_frame(frame)
        Track->>Track: detect_hands()
        Track-->>Feat: hand_landmarks
        Feat->>Feat: extract_features()
        Feat-->>ML: feature_vector
        ML->>ML: predict()
        ML-->>Eng: label, confidence
        Eng->>Buf: add_gesture(label)
        Buf->>Buf: check_stability()
        
        alt Gesture Confirmed
            Buf-->>Eng: confirmed_gesture
            Eng->>Map: map_sequence()
        end
    end
    
    User->>UI: Click Stop & Translate
    UI->>Eng: finalize()
    Eng->>Map: get_translation()
    Map-->>UI: translation_text
    UI->>Voice: speak(text)
    UI->>DB: save_translation()
    UI-->>User: Display Result
```

---

## 7. Class Diagram - Core Components

```mermaid
classDiagram
    class MainWindow {
        -classifier: Classifier
        -db: DatabaseService
        -user: dict
        +navigate_to(page_id)
        +on_login(user_data)
        +on_logout()
    }
    
    class LiveTranslationPage {
        -engine: SimpleTranslationEngine
        -pipeline: SignLanguagePipeline
        -camera_widget: CameraWidget
        +start_translation()
        +stop_translation()
        +on_features(features)
    }
    
    class CameraWidget {
        -hand_tracker: HandTracker
        -feature_extractor: FeatureExtractor
        +start()
        +stop()
        +features_ready: Signal
        +hand_detected: Signal
    }
    
    class HandTracker {
        -landmarker: HandLandmarker
        +process_frame(frame)
        +get_landmarks()
    }
    
    class Classifier {
        -model: RandomForest
        -labels: list
        +load()
        +predict(features)
        +save()
    }
    
    class SimpleTranslationEngine {
        -buffer: list
        -confirmed_gestures: list
        +add_gesture(label, conf)
        +finalize()
        +get_translation()
    }
    
    class SentenceMapper {
        -gesture_dict: GestureDictionary
        +map_to_sentence(gestures)
        +get_partial_matches()
    }
    
    class DatabaseService {
        +sign_up(email, password)
        +sign_in(email, password)
        +save_translation(user_id, label)
        +get_translations(user_id)
    }
    
    MainWindow --> LiveTranslationPage
    MainWindow --> DatabaseService
    LiveTranslationPage --> CameraWidget
    LiveTranslationPage --> SimpleTranslationEngine
    CameraWidget --> HandTracker
    LiveTranslationPage --> Classifier
    SimpleTranslationEngine --> SentenceMapper
```

---

## 8. Component Diagram

```mermaid
flowchart TB
    subgraph "Presentation Layer"
        UI[UI Components]
        Pages[Page Views]
        Widgets[Custom Widgets]
    end
    
    subgraph "Application Layer"
        Core[Core Engine]
        Pipeline[Translation Pipeline]
        Analytics[Analytics Service]
        Export[Export Manager]
    end
    
    subgraph "Business Logic Layer"
        ML[ML Classifier]
        Heuristic[Heuristic Classifier]
        Buffer[Sequence Buffer]
        Mapper[Sentence Mapper]
        Dict[Gesture Dictionary]
    end
    
    subgraph "Detection Layer"
        Camera[Camera Handler]
        Video[Video Handler]
        HandTrack[Hand Tracker]
        FaceTrack[Face Detector]
        Features[Feature Extractor]
    end
    
    subgraph "Data Layer"
        DB[(SQLite)]
        Models[(ML Models)]
        Assets[(Assets)]
    end
    
    UI --> Pages --> Widgets
    Widgets --> Core
    Core --> Pipeline --> ML & Heuristic
    ML & Heuristic --> Buffer --> Mapper --> Dict
    
    Widgets --> Camera & Video
    Camera & Video --> HandTrack & FaceTrack
    HandTrack --> Features --> ML
    
    Core --> DB
    ML --> Models
    UI --> Assets
```

---

## 9. State Diagram - Translation States

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> Initializing : Start Translation
    Initializing --> CameraError : Camera Unavailable
    CameraError --> Idle : Retry
    
    Initializing --> Capturing : Camera Ready
    
    Capturing --> Detecting : Frame Available
    Detecting --> Capturing : No Hand
    Detecting --> Recognizing : Hand Detected
    
    Recognizing --> Buffering : Gesture Recognized
    Buffering --> Capturing : Continue Capture
    
    Buffering --> WaitingTimeout : Gesture Confirmed
    WaitingTimeout --> Capturing : Continue Signing
    WaitingTimeout --> Translating : Timeout Reached
    
    Translating --> DisplayResult : Translation Complete
    DisplayResult --> Speaking : Voice Enabled
    Speaking --> Saving : Speech Complete
    DisplayResult --> Saving : Voice Disabled
    
    Saving --> Idle : User Stops
    Saving --> Capturing : Continue Session
    
    Capturing --> Idle : Stop Translation
    
    Idle --> [*]
```

---

## 10. Deployment Diagram

```mermaid
flowchart TB
    subgraph "User Machine"
        subgraph "Application"
            PY[Python Runtime]
            APP[EmoSign App]
            QT[PySide6 GUI]
        end
        
        subgraph "Resources"
            DB[(signlanguage.db)]
            ML[(ML Models)]
            MP[(MediaPipe Models)]
        end
        
        subgraph "Hardware"
            CAM[Webcam]
            SPK[Speakers]
            MIC[Microphone]
        end
    end
    
    PY --> APP
    APP --> QT
    APP --> DB
    APP --> ML
    APP --> MP
    
    CAM --> APP
    APP --> SPK
```

---

## Legend

| Diagram Type | Purpose |
|--------------|---------|
| ER Diagram | Database structure and relationships |
| Use Case | User interactions with system |
| DFD Level 0 | High-level data flow overview |
| DFD Level 1 | Detailed process data flow |
| Activity | Translation workflow steps |
| Sequence | Object interactions over time |
| Class | Object-oriented structure |
| Component | System architecture layers |
| State | Translation state machine |
| Deployment | Physical deployment structure |

---

*Generated for EmoSign v3.0 - Sign Language Translator*
