import os
import re
import sys
import json
import urllib.parse
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import flask_login
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from services.llm_service import query_llm

# -----------------------------
# Windows UTF Fix
# -----------------------------
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"


# -----------------------------
# Flask Config
# -----------------------------
app = Flask(__name__)
app.secret_key = "pedagogy-secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR,'pedagogy.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -----------------------------
# Login Manager
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# -----------------------------
# Models
# -----------------------------
class User(db.Model, flask_login.UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(200))

    domain = db.Column(db.String(50))
    level = db.Column(db.String(50))


class Feedback(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    topic = db.Column(db.String(200))

    rating = db.Column(db.Integer)

    comment = db.Column(db.Text)

    lesson_content = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------
# Extract Mermaid
# -----------------------------
def extract_mermaid(viz_text, topic="Topic"):
    text = viz_text
    
    # 1. Broad extraction from markdown blocks
    match = re.search(r'```(?:mermaid)?\s*\n?(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        # Fallback: remove tags manually if partial
        text = text.replace('```mermaid', '').replace('```', '').strip()

    # 2. Key Mermaid diagrams to look for
    keywords = ['graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'pie', 'gantt', 'erDiagram', 'mindmap', 'timeline', 'journey', 'quadrantChart', 'requirementDiagram', 'gitGraph']
    
    lines = text.split('\n')
    valid_lines = []
    started = False
    
    for line in lines:
        clean = line.strip()
        if not clean: continue
        
        # Stricter start condition: Must be the FIRST word of the line
        if not started:
            for kw in keywords:
                # Use re.match to ensure it's at the very beginning of the string
                if re.match(rf'^{kw}\b', clean, re.IGNORECASE):
                    started = True
                    valid_lines.append(clean)
                    break
        else:
            # Stop if we hit a next section header or markdown closure
            if clean.startswith('```') or re.match(r'^[A-Z\s]{4,}:', clean):
                break
            valid_lines.append(clean)
                
    if valid_lines:
        return '\n'.join(valid_lines)
    
    # Ultimate fallback: Simple flowchart with quotes to avoid syntax errors
    # Ultimate fallback: Technical hub-spoke diagram
    return f'graph TD\n    A["{topic}"] --- B["Architecture"]\n    A --- C["Core Logic"]\n    A --- D["Implementation"]'


# -----------------------------
# Global Store
# -----------------------------
user_lessons = {}

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# Signup
# -----------------------------
@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("User exists")
            return redirect(url_for("signup"))

        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash,password):

            login_user(user)

            return redirect(url_for("profile"))

        flash("Invalid login")

    return render_template("login.html")


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("home"))


# -----------------------------
# Profile
# -----------------------------
@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():

    if request.method == "POST":

        current_user.domain = request.form.get("domain")
        current_user.level = request.form.get("level")

        db.session.commit()

        return redirect(url_for("lesson_input"))

    return render_template("profile.html", user=current_user)


# -----------------------------
# Topic Input
# -----------------------------
@app.route("/lesson-input")
@login_required
def lesson_input():

    return render_template("lesson_input.html")


# -----------------------------
# Generate Lesson
# -----------------------------
@app.route("/generate", methods=["POST"])
@login_required
def generate():

    topic = request.form.get("topic")

    if not topic:

        flash("Enter topic")
        return redirect(url_for("lesson_input"))

    domain = current_user.domain
    level = current_user.level

    encoded = urllib.parse.quote(topic)

    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"
    session['last_topic'] = topic
    
    user_lessons[current_user.id] = {
        'topic': topic,
        'pedagogy': '',
        'explanation': '',
        'analogy': '',
        'summary': '',
        'mermaid_code': '',
        'image_url': image_url
    }

    return redirect(url_for("lesson_display"))


@app.route("/generate-section", methods=["POST"])
@login_required
def generate_section():
    data = request.get_json()
    if not data:
        return {"error": "Invalid JSON"}, 400
        
    section_type = data.get("section_type")
    
    topic = session.get('last_topic')
    domain = current_user.domain
    level = current_user.level
    
    if not topic or not section_type:
        return {"error": "Missing topic or section type"}, 400

    prompts = {
        'pedagogy': f"Identify the best pedagogy method for teaching '{topic}' to {level} students in {domain}. Provide a brief 2-3 sentence overview of this strategy. Keep it very short.",
        'explanation': f"Provide a concise yet deep and comprehensive explanation of '{topic}' for {level} students in {domain}. Use well-structured paragraphs. Length: 300-450 tokens.",
        'analogy': f"Provide a simple, relatable analogy for the concept '{topic}' for {level} level students in {domain}. Output ONLY the analogy text.",
        'summary': f"Provide a concise summary of the topic '{topic}' for {level} level students in {domain}. Output ONLY the summary text.",
        'mermaid_code': f"Generate a HIGH-FIDELITY, dynamic educational Mermaid.js diagram for '{topic}'. \n"
                        f"1. MINDSET: Think like a technical architect. Avoid all simplicity. Use deep technical terms only.\n"
                        f"2. CHOICE: Choose the BEST specialized type: 'mindmap', 'flowchart TD', 'gantt', 'sequenceDiagram', 'stateDiagram-v2', or 'timeline'.\n"
                        f"3. SPECIFICITY: Use 7-12 technical components. BANNED: No generic labels like 'Start', 'Step 1', 'Details', 'Concept', 'Input'.\n"
                        f"4. RELATIONSHIPS: Ensure all connectors have descriptive labels explaining exact technical interactions (e.g., 'encapsulates', 'synchronizes', 'maps to').\n"
                        f"5. STYLING: Use 'classDef' for a premium dark-mode look with vibrant accent colors. Use double quotes for all node text. Output ONLY the code."
    }
    
    prompt = prompts.get(section_type)
    if not prompt:
        return {"error": "Invalid section type"}, 400

    # Capture context data BEFORE entering the generator to avoid context errors
    user_id = current_user.id
    current_topic = topic # Already captured from session above
    
    def generate_stream():
        full_content = ""
        try:
            stream = query_llm(prompt, stream=True, max_tokens=600)
            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    text = chunk['choices'][0].get('text', '')
                    if text:
                        full_content += text
                        # Update local store IMMEDIATELY during stream
                        if user_id in user_lessons:
                            user_lessons[user_id][section_type] = full_content
                        # Yield JSON string formatted for Server-Sent Events
                        yield f"data: {json.dumps({'content': full_content, 'done': False})}\n\n"
            
            if section_type == 'mermaid_code':
                # Pass captured topic to extract_mermaid
                full_content = extract_mermaid(full_content, topic=current_topic)
                if user_id in user_lessons:
                    user_lessons[user_id][section_type] = full_content
                yield f"data: {json.dumps({'content': full_content, 'done': True, 'final_mermaid': True})}\n\n"
            else:
                if user_id in user_lessons:
                    user_lessons[user_id][section_type] = full_content
                yield f"data: {json.dumps({'content': full_content, 'done': True})}\n\n"
                
        except Exception as e:
            print(f"[ERROR] generate_stream exception: {e}")
            yield f"data: {json.dumps({'content': f'Error generating content: {str(e)}', 'done': True})}\n\n"

    return Response(generate_stream(), mimetype='text/event-stream')


@app.route("/lesson")
@login_required
def lesson_display():
    topic = session.get('last_topic')
    sections = user_lessons.get(current_user.id)
    if not topic or not sections:
        return redirect(url_for("lesson_input"))
    
    return render_template(
        "lesson.html",
        topic=topic,
        sections=sections,
        image_url=sections.get('image_url'),
        domain=current_user.domain,
        level=current_user.level
    )

@app.route("/generate-quiz", methods=["GET", "POST"])
@login_required
def generate_quiz():
    topic = session.get('last_topic')
    level = current_user.level
    print(f"[DEBUG] /generate-quiz called | Topic: {topic} | Level: {level}")
    if not topic:
        print("[DEBUG] No topic found in session!")
        return {"error": "No topic found"}, 400
        return {"error": "No topic found"}, 400
    
    prompt = f"""Create 3 Multiple Choice Questions about '{topic}' for {level} level students. 
Follow this EXACT format for each question:

Q1: [Question Text]
A: [Option A]
B: [Option B]
C: [Option C]
D: [Option D]
Answer: [A, B, C, or D]
Explanation: [Brief text]

Example:
Q1: What is 2+2?
A: 3
B: 4
C: 5
D: 6
Answer: B
Explanation: Simple addition.

Generate exactly 3 questions. No extra dialogue."""

    def stream_quiz():
        full_content = ""
        try:
            stream = query_llm(prompt, stream=True, max_tokens=600)
            print("[DEBUG] LLM Stream Started")
            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    text = chunk['choices'][0].get('text', '')
                    if text:
                        full_content += text
                        # Send ONLY the delta (new text)
                        yield f"data: {json.dumps({'delta': text, 'done': False})}\n\n"
            
            print(f"[DEBUG] Stream Finished. Full length: {len(full_content)}")
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            print(f"[DEBUG] Quiz Stream Error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return Response(stream_quiz(), mimetype='text/event-stream')


@app.route("/quiz")
@login_required
def quiz():
    topic = session.get('last_topic')
    if not topic:
        return redirect(url_for("lesson_input"))
    return render_template("quiz.html", topic=topic)


# -----------------------------
# Feedback
# -----------------------------
@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        rating_str = request.form.get("rating")
        if not rating_str:
            flash("Rating is required", "warning")
            return redirect(url_for("feedback"))
            
        rating = int(rating_str)
        comment = request.form.get("comment", "")

        data = user_lessons.get(current_user.id)
        if not data:
            flash("No active lesson found to provide feedback for.", "warning")
            return redirect(url_for("lesson_input"))

        fb = Feedback(
            user_id=current_user.id,
            topic=data.get("topic", "General"),
            rating=rating,
            comment=comment,
            lesson_content=str(data)
        )

        db.session.add(fb)
        db.session.commit()
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("analytics"))

    # GET request - show the form
    topic = session.get("last_topic")
    return render_template("feedback.html", topic=topic)


# -----------------------------
# Analytics
# -----------------------------
@app.route("/analytics")
@login_required
def analytics():
    feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
    total = len(feedbacks)
    
    avg = db.session.query(func.avg(Feedback.rating)).filter(Feedback.user_id == current_user.id).scalar() or 0
    avg_rating = round(float(avg), 1)

    # Count ratings for the chart
    rating_counts = {i: 0 for i in range(1, 6)}
    for f in feedbacks:
        if f.rating in rating_counts:
            rating_counts[f.rating] += 1

    return render_template(
        "analytics.html",
        feedbacks=feedbacks,
        total=total,
        avg_rating=avg_rating,
        rating_counts=rating_counts
    )


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    print("AI PEDAGOGY SYSTEM READY")
    print("Open http://localhost:5000")
    app.run(debug=True, port=5000)