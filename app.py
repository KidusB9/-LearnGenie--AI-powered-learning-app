from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import openai

# Load your OpenAI API key from an environment variable or secret management service
api_key = "your_openai_api_key"
openai.api_key = api_key

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    progress = db.relationship('Progress', backref='user', lazy='dynamic')

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    progress = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    contents = Content.query.all()
    return render_template('index.html', contents=contents)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/content/<int:content_id>')
@login_required
def view_content(content_id):
    content = Content.query.get_or_404(content_id)
    return render_template('content.html', content=@app.route('/content/<int:content_id>', methods=['GET', 'POST'])
@login_required
def view_content(content_id):
    content = Content.query.get_or_404(content_id)
    progress = Progress.query.filter_by(user_id=current_user.id, content_id=content_id).first()

    if request.method == 'POST':
        user_progress = float(request.form['progress'])
        if progress:
            progress.progress = user_progress
        else:
            progress = Progress(user_id=current_user.id, content_id=content_id, progress=user_progress)
            db.session.add(progress)
        db.session.commit()
        flash('Progress saved successfully')

    return render_template('content.html', content=content, progress=progress)

@app.route('/generate')
@login_required
def generate_learning_content():
    user_interest = request.args.get('interest', '')
    prompt = request.args.get('prompt', '')

    if user_interest and prompt:
        generated_content = _generate_learning_content(user_interest, prompt)
        return {'content': generated_content}
    else:
        return {'error': 'Please provide both an interest and a prompt.'}, 400

def _generate_learning_content(user_interest, prompt):
    content = openai.Completion.create(
        engine="davinci-codex",
        prompt=f"Generate a lesson plan about {user_interest}. {prompt}",
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return content.choices[0].text.strip()

if __name__ == "__main__":
    app.run(debug=True)

