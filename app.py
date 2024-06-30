from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import requests
#from flask_oauthlib.client import OAuth
from flask import Flask, redirect, request
from flask import session
from flask import Flask, make_response
from sqlalchemy.orm import joinedload
#from flask import User, UserProfile
from sqlalchemy.orm import relationship
from hashlib import md5
from werkzeug.utils import secure_filename
import os



from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()




api_key = ""
openai.api_key = api_key

import os

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
app.config['SECRET_KEY'] = 'e887f52689f0f063b30dcc6fc08d52bf'


#oauth = OAuth(app)
# Initialize Google OAuth
#google = oauth.remote_app(
   # 'google',
  #  consumer_key='541354141268-26u25706gprfrfv2n17gfi3qm4dbaf4n.apps.googleusercontent.com',
   # consumer_secret='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',
   # request_token_params={
    #    'scope': 'email',
    #},
    #base_url='https://www.googleapis.com/oauth2/v1/',
    #request_token_url=None,
   # access_token_method='POST',
   # access_token_url='https://accounts.google.com/o/oauth2/token',
   # authorize_url='https://accounts.google.com/o/oauth2/auth',
#)




db = SQLAlchemy(app)
migrate = Migrate(app, db)



from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()



def content_belongs_to_user(content, user):
    return user in content.users





login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class ContentUserMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    #user = relationship("User", back_populates="contents")
    users = db.relationship('User', secondary='content_user_map', back_populates='contents')





class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    progress = db.relationship('Progress', backref='user', lazy='dynamic')
    profile = relationship("UserProfile", uselist=False, back_populates="user")
    #contents = db.relationship('Content', back_populates='user')
    #contents = db.relationship('Content', backref='user', lazy='dynamic')
    contents = db.relationship('Content', secondary='content_user_map', back_populates='users')

    def avatar(self, size):
        digest = md5(self.username.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)



    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return True
        return False

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return True
        return False

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    progress = db.Column(db.Float, default=0.0)
    rating = db.Column(db.Float, nullable=True)



class UserProfile(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        bio = db.Column(db.Text, nullable=True)
        interests = db.Column(db.String(256), nullable=True)
        user = relationship("User", back_populates="profile")



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    contents = Content.query.all()
    #users = User.query.options(joinedload('profile')).all()
    from sqlalchemy.orm import joinedload
    users = User.query.options(joinedload(User.profile)).all()
    users = User.query.all()  # Fetching all users from the database
    return render_template('index.html', contents=contents, users=users)


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
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('username', username, secure=True)

            return resp
        else:
            flash('Invalid username or password')
    return render_template('login.html')



@app.route('/images/<filename>')
def image(filename):
    return send_from_directory('static/images', filename)


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








@app.route('/generated_content/<int:content_id>', methods=['GET'])
@login_required
def view_content(content_id):
    # Your logic for fetching and rendering the content
    # For example:
    content = Content.query.get_or_404(content_id)
    return render_template('generated_content.html', content=content)






def _generate_learning_content(user_interest, prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate a lesson plan about:"},
            {"role": "user", "content": f"{user_interest}. {prompt}"}
        ],
        max_tokens=3000,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()







def _generate_detailed_content(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Explain in detail:"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message['content'].strip()








def generate_dalle_image(prompt, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        #"model": "image-alpha-001",
        "num_images":4,
        "prompt": prompt,
        "size": "512x512",
    }
    response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data)

    if response.status_code == 200:
        json_response = response.json()
        image_url = json_response["data"][0]["url"]

        # Download the image
        image_data = requests.get(image_url).content

        # Save the image
        filename = secure_filename(f"dalle_image_{os.urandom(6).hex()}.jpg")
        image_path = os.path.join(app.root_path, 'static/images', filename)
        with open(image_path, 'wb') as file:
            file.write(image_data)

        # Return the new path
        return url_for('image', filename=filename)
    else:
        raise Exception(f"Error generating image: {response.text}")



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
    # Prepare the response for database recommendations
    db_recommendations = [{'id': content.id, 'title': content.title, 'description': content.description} for content in recommended_contents]

    learn_genie_recommendations = []
    prompt = "LearnGenie, what are the top 3 books you'd recommend for someone interested in history, universe, data science? Respond with three short sentences, one for history, one for universe, one for data science."

    try:

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Provide a recommendation:"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        learn_genie_recommendations.append(response.choices[0].message['content'].strip())
    except Exception as e:
        pass

    combined_recommendations = {
        'database_recommendations': [{'id': content.id, 'title': content.title, 'description': content.description} for content in recommended_contents],
        'learn_genie_recommendations': learn_genie_recommendations
    }


    return jsonify({'recommendations': combined_recommendations})

@app.route('/user/<int:user_id>')
@login_required
def user(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))

    all_contents = Content.query.all()
    user_contents = [content for content in all_contents if content_belongs_to_user(content, user)]
    return render_template('user.html', user=user, contents=user_contents)

#def content_belongs_to_user(content, user):
    #return user in content.users



@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself.')
        return redirect(url_for('user', user_id=user_id))
    if current_user.follow(user):
        db.session.commit()
        flash(f'You are now following {user.username}.')
    return redirect(url_for('user', user_id=user_id))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself.')
        return redirect(url_for('user', user_id=user_id))
    if current_user.unfollow(user):
        db.session.commit()
        flash(f'You are no longer following {user.username}.')
    return redirect(url_for('user', user_id=user_id))

from flask import render_template

@app.route('/generate')
@login_required
def generate_learning_content():
    user_interest = request.args.get('interest', '')
    prompt = request.args.get('prompt', '')

    if user_interest and prompt:
        generated_content = _generate_learning_content(user_interest, prompt)
        generated_image = generate_dalle_image(prompt, api_key) # Pass the api_key as an argument
        return render_template('generated_content.html', content=generated_content, image_url=generated_image)
    else:
        return {'error': 'Please provide both an interest and a prompt.'}, 400





@app.route('/create_content', methods=['GET', 'POST'])
@login_required
def create_content():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        # Add any other fields you have in your Content model

        content = Content(title=title, description=description)
        # Set other fields for the content object as needed

        db.session.add(content)
        db.session.commit()

        flash('Content created successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('create_content.html')




@app.route('/detailed_content', methods=['GET'])
@login_required
def detailed_content():
    prompt = request.args.get('prompt', '')

    if prompt:
        detailed_text = _generate_detailed_content(prompt)
        print(f"Detailed text: {detailed_text}")
        return render_template('detailed_content.html', detailed_text=detailed_text)
    else:
        return {'error': 'Please provide a prompt.'}, 400



# Google OAuth Routes
#@app.route('/google_login')
#def google_login():
    #return google.authorize(callback=url_for('google_authorized', _external=True))

#@app.route('/google_logout')
#def google_logout():
   # session.pop('google_token')
    #return redirect(url_for('index'))

#@app.route('/google_login/authorized')
#def google_authorized():
   # response = google.authorized_response()
   # if response is None or response.get('access_token') is None:
       # return 'Access denied: reason={} error={}'.format(
       #     request.args['error_reason'],
          #  request.args['error_description']
       # )

   # session['google_token'] = (response['access_token'], '')
    #user_info = google.get('userinfo')
    #return 'Logged in as: ' + user_info.data['email']

#@google.tokengetter
#def get_google_oauth_token():
    #return session.get('google_token')

@app.route('/google_login')
def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": "541354141268-26u25706gprfrfv2n17gfi3qm4dbaf4n.apps.googleusercontent.com",
        "redirect_uri": "https://kidusb.pythonanywhere.com/google_callback",
        "response_type": "code",
        "scope": "email",
    }
    return redirect(requests.Request('GET', google_auth_url, params=params).prepare().url)

@app.route('/google_callback')
def google_callback():
    code = request.args.get('code')
    if code is None:
        return "Missing code"

    google_token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": "541354141268-26u25706gprfrfv2n17gfi3qm4dbaf4n.apps.googleusercontent.com",
        "client_secret": "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",
        "redirect_uri": "https://kidusb.pythonanywhere.com/google_callback",
        "grant_type": "authorization_code",
    }
    response = requests.post(google_token_url, data=token_data)
    token_info = response.json()
    access_token = token_info.get('access_token')

    if access_token is None:
        return "Failed to get access token"

    # Fetch user info
    user_info_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={'Authorization': f'Bearer {access_token}'})
    user_info = user_info_response.json()
    email = user_info.get('email')

    # Check if user exists
    user = User.query.filter_by(username=email).first()

    if not user:
        # Register user
        new_user = User(username=email, password=generate_password_hash(email))
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    # Log user in
    login_user(user)
    flash('Login successful!')

    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('index'))


@app.route('/setcookie/<username>')
def set_cookie(username):
    resp = make_response('Setting cookie!')
    resp.set_cookie('username', username)
    return resp

@app.route('/getcookie')
def get_cookie():
    username = request.cookies.get('username')
    return f'Found cookie: {username}'




if __name__ == "__main__":
    app.config['SQLALCHEMY_ECHO'] = True
    app.run(debug=True, host='0.0.0.0', port=5000)