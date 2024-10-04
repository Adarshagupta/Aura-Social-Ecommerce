from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from PIL import Image
import io
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aura_zc9o_user:W2niGk1Mea0dmeVkW9yFjDbNWHmJ9HZK@dpg-cs03hkaj1k6c73ebjsh0-a.singapore-postgres.render.com/aura_zc9o'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    aura_points = db.Column(db.Integer, default=0)
    super_aura_points = db.Column(db.Integer, default=0)
    profile_photo = db.Column(db.LargeBinary)
    profile_photo_mimetype = db.Column(db.String(50))
    banner_photo = db.Column(db.LargeBinary)
    banner_photo_mimetype = db.Column(db.String(50))
    bio = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], backref='follower', lazy='dynamic')
    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], backref='followed', lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)

    def unfollow(self, user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)

    def is_following(self, user):
        return self.following.filter_by(followed_id=user.id).first() is not None

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_data = db.Column(db.LargeBinary)
    image_mimetype = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)
    aura_points = db.Column(db.Integer, default=0)  # Replace vote_count with aura_points

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_aura = db.Column(db.Integer, nullable=False)
    price_super_aura = db.Column(db.Integer, nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user = db.relationship('User', backref='comments')
    post = db.relationship('Post', backref='comments')

class Hashtag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', secondary='post_hashtags', backref='hashtags')

post_hashtags = db.Table('post_hashtags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        followed_users = [user.id for user in current_user.following]
        followed_users.append(current_user.id)
        posts = Post.query.filter(Post.user_id.in_(followed_users)).order_by(Post.timestamp.desc()).all()
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.password_hash = generate_password_hash(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        content = request.form['content']
        image = request.files['image']
        
        post = Post(content=content, author=current_user)
        
        if image:
            img = Image.open(image)
            img.thumbnail((800, 800))
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG')
            img_io.seek(0)
            post.image_data = img_io.getvalue()
            post.image_mimetype = 'image/jpeg'
        
        # Extract hashtags from the content
        hashtags = [tag.strip('#') for tag in content.split() if tag.startswith('#')]
        for tag_name in hashtags:
            tag = Hashtag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Hashtag(name=tag_name)
                db.session.add(tag)
            post.hashtags.append(tag)
        
        db.session.add(post)
        db.session.commit()
        
        current_user.aura_points += 1
        if current_user.aura_points % 10 == 0:
            current_user.super_aura_points += 1
        db.session.commit()
        
        flash('Post created successfully!')
        return redirect(url_for('index'))
    
    return render_template('create_post.html')

@app.route('/shop')
@login_required
def shop():
    products = Product.query.all()
    return render_template('shop.html', products=products)

@app.route('/buy/<int:product_id>')
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if current_user.aura_points >= product.price_aura and current_user.super_aura_points >= product.price_super_aura:
        current_user.aura_points -= product.price_aura
        current_user.super_aura_points -= product.price_super_aura
        db.session.commit()
        flash(f'You have successfully purchased {product.name}!')
    else:
        flash('Insufficient points to make this purchase.')
    
    return redirect(url_for('shop'))

@app.route('/image/<int:post_id>')
def get_image(post_id):
    post = Post.query.get_or_404(post_id)
    if post.image_data:
        return send_file(
            io.BytesIO(post.image_data),
            mimetype=post.image_mimetype
        )
    return 'No image', 404

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if like:
        db.session.delete(like)
        post.aura_points -= 1
        post.author.aura_points -= 1
        message = 'Post unliked'
    else:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        post.aura_points += 1
        post.author.aura_points += 1
        if post.author.aura_points % 10 == 0:
            post.author.super_aura_points += 1
        message = 'Post liked'

    db.session.commit()
    return jsonify({'message': message, 'aura_points': post.aura_points})

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.bio = request.form['bio']
        
        if 'profile_photo' in request.files:
            profile_photo = request.files['profile_photo']
            if profile_photo.filename != '':
                img = Image.open(profile_photo)
                img.thumbnail((200, 200))
                img_io = io.BytesIO()
                img.save(img_io, 'JPEG')
                img_io.seek(0)
                current_user.profile_photo = img_io.getvalue()
                current_user.profile_photo_mimetype = 'image/jpeg'
        
        if 'banner_photo' in request.files:
            banner_photo = request.files['banner_photo']
            if banner_photo.filename != '':
                img = Image.open(banner_photo)
                img.thumbnail((800, 200))
                img_io = io.BytesIO()
                img.save(img_io, 'JPEG')
                img_io.seek(0)
                current_user.banner_photo = img_io.getvalue()
                current_user.banner_photo_mimetype = 'image/jpeg'
        
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('profile', username=current_user.username))
    
    return render_template('edit_profile.html')

@app.route('/user_image/<int:user_id>/<image_type>')
def get_user_image(user_id, image_type):
    user = User.query.get_or_404(user_id)
    if image_type == 'profile' and user.profile_photo:
        return send_file(
            io.BytesIO(user.profile_photo),
            mimetype=user.profile_photo_mimetype
        )
    elif image_type == 'banner' and user.banner_photo:
        return send_file(
            io.BytesIO(user.banner_photo),
            mimetype=user.banner_photo_mimetype
        )
    return 'No image', 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, user_id=current_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': 'Comment added', 'comment_id': comment.id})
    return jsonify({'error': 'Comment content is required'}), 400

@app.route('/search')
def search():
    query = request.args.get('q')
    if query:
        posts = Post.query.filter(Post.content.ilike(f'%{query}%')).all()
        users = User.query.filter(User.username.ilike(f'%{query}%')).all()
        return render_template('search_results.html', posts=posts, users=users, query=query)
    return redirect(url_for('index'))

@app.route('/trending')
def trending_posts():
    trending = Post.query.order_by(Post.aura_points.desc(), Post.timestamp.desc()).limit(10).all()
    return render_template('trending.html', trending_posts=trending)

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        return jsonify({'error': 'You cannot follow yourself'}), 400
    if not current_user.is_following(user):
        follow = Follow(follower=current_user, followed=user)
        db.session.add(follow)
        db.session.commit()
    return jsonify({'message': f'You are now following {user.username}'})

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        return jsonify({'error': 'You cannot unfollow yourself'}), 400
    follow = Follow.query.filter_by(follower=current_user, followed=user).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
    return jsonify({'message': f'You have unfollowed {user.username}'})

@app.route('/discover')
def discover():
    trending_posts = Post.query.order_by(Post.aura_points.desc(), Post.timestamp.desc()).limit(10).all()
    popular_hashtags = db.session.query(Hashtag, func.count(post_hashtags.c.post_id).label('post_count')) \
        .join(post_hashtags) \
        .group_by(Hashtag) \
        .order_by(func.count(post_hashtags.c.post_id).desc()) \
        .limit(10) \
        .all()
    return render_template('discover.html', trending_posts=trending_posts, popular_hashtags=popular_hashtags)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)