from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 浏览历史关系
    browsing_history = db.relationship('ArticleViewHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    articles = db.relationship('Article', backref='category', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    
    # 浏览历史关系
    view_history = db.relationship('ArticleViewHistory', backref='article', lazy='dynamic', cascade='all, delete-orphan')

class ArticleViewHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 复合唯一约束，确保同一用户对同一文章只有一条记录
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='_user_article_uc'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('index.html', articles=articles)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 记录浏览历史（仅登录用户）
    if current_user.is_authenticated:
        # 检查是否已有浏览记录
        existing_history = ArticleViewHistory.query.filter_by(
            user_id=current_user.id,
            article_id=article_id
        ).first()
        
        if existing_history:
            # 更新浏览时间
            existing_history.viewed_at = datetime.utcnow()
        else:
            # 创建新记录
            new_history = ArticleViewHistory(
                user_id=current_user.id,
                article_id=article_id
            )
            db.session.add(new_history)
        
        # 更新文章浏览计数
        article.views += 1
        db.session.commit()
    
    return render_template('article_detail.html', article=article)

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
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return render_template('register.html')
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/browsing-history')
@login_required
def browsing_history():
    # 获取当前用户的浏览历史，只显示最近一个月的记录
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    history = ArticleViewHistory.query.filter_by(user_id=current_user.id)\
        .filter(ArticleViewHistory.viewed_at >= one_month_ago)\
        .order_by(ArticleViewHistory.viewed_at.desc())\
        .all()
    
    return render_template('browsing_history.html', history=history)

@app.before_first_request
def create_tables():
    db.create_all()
    
    # 创建示例数据
    if not User.query.first():
        # 创建示例用户
        demo_user = User(
            username='demo',
            email='demo@example.com',
            password_hash=generate_password_hash('demo123')
        )
        db.session.add(demo_user)
        
        # 创建示例分类
        categories = [
            Category(name='技术', description='技术相关文章'),
            Category(name='生活', description='生活感悟'),
            Category(name='学习', description='学习笔记')
        ]
        for cat in categories:
            db.session.add(cat)
        
        db.session.commit()
        
        # 创建示例文章
        demo_articles = [
            Article(
                title='Flask入门指南',
                content='Flask是一个轻量级的Python Web框架，非常适合快速开发Web应用...',
                summary='本文介绍了Flask框架的基础知识和使用方法',
                author_id=1,
                category_id=1
            ),
            Article(
                title='Python装饰器详解',
                content='装饰器是Python中一个非常强大的功能，它可以让你在不修改原函数代码的情况下...',
                summary='深入理解Python装饰器的原理和应用',
                author_id=1,
                category_id=1
            ),
            Article(
                title='我的编程学习之路',
                content='从开始接触编程到现在，已经有好几年的时间了。在这个过程中...',
                summary='分享我的编程学习经验和心得体会',
                author_id=1,
                category_id=3
            )
        ]
        
        for article in demo_articles:
            db.session.add(article)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)