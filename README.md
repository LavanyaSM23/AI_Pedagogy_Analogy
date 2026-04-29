# 🧠 AI Pedagogy — Smart Learning System

An AI-powered pedagogy and analogy recommendation system that runs **entirely on your local machine** using open-source LLMs — no internet or API keys required for inference.

---

## ✨ Features

- **AI Lesson Generation** — Personalized pedagogy, explanations, analogies, and summaries
- **Interactive Diagrams** — Mermaid-powered flowcharts with zoom and pan support
- **AI Quick Quiz** — Test knowledge immediately after any lesson
- **Premium Analytics** — Track progress with animated Chart.js dashboards
- **Hardware Optimized** — Auto-detects CPU cores and GPU availability for fast inference

---

## 📋 Prerequisites

Make sure you have the following installed:

- **Python 3.10+** → [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- **Git** → [Download](https://git-scm.com/)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/LavanyaSM23/AI_Pedagogy_Analogy.git
cd AI_Pedagogy_Analogy
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🤖 Downloading the AI Model (Required)

> ⚠️ The AI model files are **not included** in this repository because they are too large for GitHub (600MB–4GB). You **must** download a model manually and place it in the `models/` folder.

### Step 1: Create the models folder

```bash
mkdir models
```

### Step 2: Download the Model

The app uses **TinyLlama 1.1B (Q4_K_M GGUF format)** by default. Download it from Hugging Face:

**👉 [Download tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf)**

Or use `wget` / `curl`:

```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" -OutFile "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Mac/Linux
wget -P models/ https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Step 3: Verify the file is in the right place

Your folder structure should look like this:
```
AI_Pedagogy_Analogy/
├── models/
│   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf   ✅
├── app.py
├── services/
│   └── llm_service.py
└── ...
```

### 🔄 Want to use a different (better) model?

You can use any GGUF-format model. For example:
| Model | Size | Download |
|---|---|---|
| TinyLlama 1.1B (default) | ~638 MB | [Link](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) |
| Phi-2 | ~1.6 GB | [Link](https://huggingface.co/TheBloke/phi-2-GGUF) |
| Mistral 7B Instruct | ~4.1 GB | [Link](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) |

After downloading a different model, update the filename in `services/llm_service.py`:

```python
# Line 9 in services/llm_service.py
MODEL_FILENAME = 'your-model-filename.gguf'   # ← Change this
```

---

## ▶️ Running the App

```bash
python app.py
```

You will see:
```
AI PEDAGOGY SYSTEM READY
Open http://localhost:5000
```

Open your browser and go to: **[http://localhost:5000](http://localhost:5000)**

> 💡 The first request may take a few seconds while the model loads into memory. Subsequent requests will be fast.

---

## 📁 Project Structure

```
AI_Pedagogy_Analogy/
├── app.py                    # Main Flask application & all routes
├── models.py                 # SQLAlchemy model definitions
├── requirements.txt          # Python dependencies
├── services/
│   └── llm_service.py        # LLM loading & inference logic
├── static/
│   └── style.css             # Global CSS styles
├── templates/                # HTML templates (Jinja2)
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── profile.html
│   ├── lesson_input.html
│   ├── lesson.html
│   ├── quiz.html
│   ├── feedback.html
│   └── analytics.html
├── models/                   # ← Place your downloaded .gguf model here
└── pedagogy.db               # SQLite database (auto-created on first run)
```

---

## 🛠 Troubleshooting

| Problem | Solution |
|---|---|
| `FileNotFoundError: Model not found` | Make sure the `.gguf` file is inside the `models/` folder and the filename matches `MODEL_FILENAME` in `llm_service.py` |
| `ModuleNotFoundError: llama_cpp` | Run `pip install llama-cpp-python` |
| Slow generation speed | Use a smaller model like TinyLlama, or install a GPU-enabled version of `llama-cpp-python` |
| Windows encoding errors | The app auto-patches this. Just restart with `python app.py` |
| Port already in use | Change `port=5000` to another port in the last line of `app.py` |

---

## 📦 Dependencies

Key packages (see `requirements.txt` for full list):

- `flask` — Web framework
- `flask-login` — User session management
- `flask-sqlalchemy` — Database ORM
- `llama-cpp-python` — Local LLM inference engine
- `werkzeug` — Password hashing

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

*Built with ❤️ using Flask + llama.cpp — runs 100% locally, no cloud required.*
