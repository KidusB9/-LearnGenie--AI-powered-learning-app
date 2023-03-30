from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import openai


# Load your OpenAI API key from an environment variable or secret management service
api_key = "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"
openai.api_key = api_key

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
app.config['SECRET_KEY'] = 'e887f52689f0f063b30dcc6fc08d52bf'

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


class UserProfile(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        bio = db.Column(db.Text, nullable=True)
        interests = db.Column(db.String(256), nullable=True)


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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        bio = request.form['bio']
        interests = request.form['interests']

        if user_profile:
            user_profile.bio = bio
            user_profile.interests = interests
        else:
            user_profile = UserProfile(user_id=current_user.id, bio=bio, interests=interests)
            db.session.add(user_profile)

        db.session.commit()
        flash('Profile updated successfully!')

    return render_template('profile.html', user_profile=user_profile)



# ... (previous code)
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

@app.route('/view_content/<int:content_id>', methods=['GET'])
@login_required
def view_content(content_id):
    # Your logic for fetching and rendering the content
    # For example:
    content = Content.query.get_or_404(content_id)
    return render_template('view_content.html', content=content)

# ... (rest of the code)


def _generate_learning_content(user_interest, prompt):
    content = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Generate a lesson plan about {user_interest}. {prompt}",
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return content.choices[0].text.strip()
from flask import jsonify

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Please provide a search query.'}), 400

    results = Content.query.filter(Content.title.contains(query) | Content.description.contains(query)).all()
    return jsonify({'results': [{'id': content.id, 'title': content.title, 'description': content.description} for content in results]})

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

def recommend_content(content_id, top_n=5):
    contents = Content.query.all()
    content_data = [{'id': content.id, 'text': content.title + ' ' + content.description} for content in contents]

    # Create a mapping from content ID to index in the contents list
    id_to_index = {content.id: index for index, content in enumerate(contents)}

    df = pd.DataFrame(content_data)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['text'])

    cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)

    # Use the mapping to get the correct index for the content_id
    index = id_to_index[content_id]
    sim_scores = list(enumerate(cosine_similarities[index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_n+1]

    content_indices = [i[0] for i in sim_scores]
    return [contents[i] for i in content_indices]

@app.route('/content/<int:content_id>/recommendations')
@login_required
def get_recommendations(content_id):
    recommended_contents = recommend_content(content_id)
    return jsonify({'recommendations': [{'id': content.id, 'title': content.title, 'description': content.description} for content in recommended_contents]})


if __name__ == "__main__":
    app.run(debug=True)
