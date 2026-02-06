import sqlite3
import datetime
import hashlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import json
import os

# 数据库初始化
def init_db():
    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # 文章表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            author_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (author_id) REFERENCES user (id),
            FOREIGN KEY (category_id) REFERENCES category (id)
        )
    ''')
    
    # 浏览历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article_view_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, article_id),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (article_id) REFERENCES article (id)
        )
    ''')
    
    # 创建示例数据
    cursor.execute('SELECT COUNT(*) FROM user')
    if cursor.fetchone()[0] == 0:
        # 创建示例用户
        password_hash = hashlib.sha256('demo123'.encode()).hexdigest()
        cursor.execute('INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)', 
                      ('demo', 'demo@example.com', password_hash))
        
        # 创建示例分类
        categories = [
            ('技术', '技术相关文章'),
            ('生活', '生活感悟'),
            ('学习', '学习笔记')
        ]
        for name, desc in categories:
            cursor.execute('INSERT INTO category (name, description) VALUES (?, ?)', (name, desc))
        
        # 创建示例文章
        demo_articles = [
            ('Flask入门指南', 'Flask是一个轻量级的Python Web框架，非常适合快速开发Web应用。本文将介绍Flask的基础知识，包括路由、模板、表单处理等核心概念。通过学习本文，你将能够使用Flask构建简单的Web应用。', '本文介绍了Flask框架的基础知识和使用方法', 1, 1),
            ('Python装饰器详解', '装饰器是Python中一个非常强大的功能，它可以让你在不修改原函数代码的情况下，为函数添加新的功能。本文将深入讲解装饰器的工作原理，并通过实际例子演示如何使用装饰器。', '深入理解Python装饰器的原理和应用', 1, 1),
            ('我的编程学习之路', '从开始接触编程到现在，已经有好几年的时间了。在这个过程中，我遇到了很多挑战，也收获了很多宝贵的经验。希望通过分享我的学习经历，能够帮助到正在学习编程的朋友们。', '分享我的编程学习经验和心得体会', 1, 3)
        ]
        
        for title, content, summary, author_id, category_id in demo_articles:
            cursor.execute('INSERT INTO article (title, content, summary, author_id, category_id) VALUES (?, ?, ?, ?, ?)', 
                          (title, content, summary, author_id, category_id))
    
    conn.commit()
    conn.close()

# 获取数据库连接
def get_db():
    return sqlite3.connect('blog.db', check_same_thread=False)

# HTML模板
def render_template(template_name, **kwargs):
    templates = {
        'base': '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        header {{ background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1rem 0; margin-bottom: 2rem; }}
        nav {{ display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.5rem; font-weight: bold; color: #007bff; text-decoration: none; }}
        .nav-menu {{ display: flex; list-style: none; gap: 2rem; align-items: center; }}
        .nav-menu a {{ text-decoration: none; color: #333; font-weight: 500; transition: color 0.3s; }}
        .nav-menu a:hover {{ color: #007bff; }}
        .user-menu {{ position: relative; }}
        .dropdown {{ position: absolute; top: 100%; right: 0; background-color: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px; padding: 0.5rem 0; min-width: 150px; display: none; z-index: 1000; }}
        .dropdown.show {{ display: block; }}
        .dropdown a {{ display: block; padding: 0.5rem 1rem; color: #333; text-decoration: none; transition: background-color 0.3s; }}
        .dropdown a:hover {{ background-color: #f8f9fa; color: #007bff; }}
        .btn {{ display: inline-block; padding: 0.5rem 1rem; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; transition: background-color 0.3s; }}
        .btn:hover {{ background-color: #0056b3; }}
        .btn-outline {{ background-color: transparent; color: #007bff; border: 1px solid #007bff; }}
        .btn-outline:hover {{ background-color: #007bff; color: white; }}
        main {{ min-height: calc(100vh - 200px); }}
        footer {{ background-color: #343a40; color: white; text-align: center; padding: 2rem 0; margin-top: 3rem; }}
        .flash {{ padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }}
        .flash-success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .flash-error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .card {{ background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1.5rem; margin-bottom: 1.5rem; }}
        .card h2 {{ margin-bottom: 1rem; color: #333; }}
        .card-meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1rem; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .form-group input, .form-group textarea {{ width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }}
        .hero {{ text-align: center; padding: 3rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; margin-bottom: 2rem; }}
        .hero h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        .hero p {{ font-size: 1.2rem; opacity: 0.9; }}
        .articles h2 {{ margin-bottom: 2rem; color: #333; }}
        .history-item {{ background-color: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
        .history-content {{ flex: 1; }}
        .history-content h3 {{ margin-bottom: 0.5rem; }}
        .history-content h3 a {{ text-decoration: none; color: #333; }}
        .history-content h3 a:hover {{ color: #007bff; }}
        .history-meta {{ color: #666; font-size: 0.9rem; display: flex; gap: 1rem; }}
        .auth-container {{ display: flex; justify-content: center; align-items: center; min-height: 60vh; }}
        .auth-card {{ background-color: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }}
        .auth-card h2 {{ margin-bottom: 1.5rem; text-align: center; color: #333; }}
        .empty-state {{ text-align: center; padding: 3rem; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav>
                <a href="/" class="logo">Flask博客</a>
                <ul class="nav-menu">
                    <li><a href="/">首页</a></li>
                    {user_menu}
                </ul>
            </nav>
        </div>
    </header>
    
    <main class="container">
        {content}
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2024 Flask博客. All rights reserved.</p>
        </div>
    </footer>
    
    <script>
        function toggleDropdown() {{
            const dropdown = document.getElementById('userDropdown');
            dropdown.classList.toggle('show');
        }}
        
        document.addEventListener('click', function(event) {{
            const dropdown = document.getElementById('userDropdown');
            const userMenu = document.querySelector('.user-menu');
            
            if (!userMenu.contains(event.target)) {{
                dropdown.classList.remove('show');
            }}
        }});
    </script>
</body>
</html>''',
        
        'index': '''<div class="hero">
    <h1>欢迎来到Flask博客</h1>
    <p>分享技术，记录生活</p>
</div>

<div class="articles">
    <h2>最新文章</h2>
    {articles}
</div>''',
        
        'article_detail': '''<div class="article-detail">
    <article class="card">
        <header class="article-header">
            <h1>{title}</h1>
            <div class="article-meta">
                <span>作者: {author}</span>
                <span>分类: {category}</span>
                <span>发布时间: {created_at}</span>
                <span>浏览: {views}次</span>
            </div>
        </header>
        
        <div class="article-content">
            {content}
        </div>
        
        <footer class="article-footer">
            <p>最后更新时间: {updated_at}</p>
        </footer>
    </article>
</div>''',
        
        'login': '''<div class="auth-container">
    <div class="auth-card">
        <h2>用户登录</h2>
        <form method="POST">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn" style="width: 100%;">登录</button>
        </form>
        
        <p style="text-align: center; margin-top: 1rem;">
            还没有账号？<a href="/register">立即注册</a>
        </p>
    </div>
</div>''',
        
        'register': '''<div class="auth-container">
    <div class="auth-card">
        <h2>用户注册</h2>
        <form method="POST">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="email">邮箱</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn" style="width: 100%;">注册</button>
        </form>
        
        <p style="text-align: center; margin-top: 1rem;">
            已有账号？<a href="/login">立即登录</a>
        </p>
    </div>
</div>''',
        
        'browsing_history': '''<div class="history-container">
    <h2>我的浏览历史</h2>
    
    {history_content}
</div>'''
    }
    
    return templates.get(template_name, '').format(**kwargs)

# 会话管理
sessions = {}
current_user = None

def get_user_menu():
    global current_user
    if current_user:
        return f'''<li class="user-menu">
            <a href="#" onclick="toggleDropdown()">{current_user['username']}</a>
            <div class="dropdown" id="userDropdown">
                <a href="/browsing-history">浏览历史</a>
                <a href="/logout">退出登录</a>
            </div>
        </li>'''
    else:
        return '''<li><a href="/login" class="btn btn-outline">登录</a></li>
                <li><a href="/register" class="btn">注册</a></li>'''

# 路由处理
class BlogHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global current_user
        
        if self.path == '/':
            self.show_index()
        elif self.path.startswith('/article/'):
            article_id = int(self.path.split('/')[-1])
            self.show_article(article_id)
        elif self.path == '/login':
            self.show_login()
        elif self.path == '/register':
            self.show_register()
        elif self.path == '/logout':
            current_user = None
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        elif self.path == '/browsing-history':
            self.show_browsing_history()
        else:
            self.send_error(404)
    
    def do_POST(self):
        global current_user
        
        content_length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(content_length).decode())
        
        if self.path == '/login':
            username = post_data.get('username', [''])[0]
            password = post_data.get('password', [''])[0]
            
            conn = get_db()
            cursor = conn.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('SELECT id, username, email FROM user WHERE username = ? AND password_hash = ?', 
                          (username, password_hash))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                current_user = {'id': user[0], 'username': user[1], 'email': user[2]}
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
        
        elif self.path == '/register':
            username = post_data.get('username', [''])[0]
            email = post_data.get('email', [''])[0]
            password = post_data.get('password', [''])[0]
            
            conn = get_db()
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                self.send_response(302)
                self.send_header('Location', '/register')
                self.end_headers()
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)', 
                          (username, email, password_hash))
            conn.commit()
            conn.close()
            
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
    
    def show_index(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.title, a.summary, a.created_at, a.views, u.username, c.name 
            FROM article a 
            JOIN user u ON a.author_id = u.id 
            JOIN category c ON a.category_id = c.id 
            ORDER BY a.created_at DESC
        ''')
        articles = cursor.fetchall()
        conn.close()
        
        articles_html = ''
        for article in articles:
            articles_html += f'''
            <div class="card">
                <h3><a href="/article/{article[0]}" style="text-decoration: none; color: #333;">{article[1]}</a></h3>
                <div class="card-meta">
                    <span>作者: {article[5]}</span> | 
                    <span>分类: {article[6]}</span> | 
                    <span>发布时间: {article[3]}</span> | 
                    <span>浏览: {article[4]}次</span>
                </div>
                <p>{article[2] or article[3][:200] + '...'}</p>
                <a href="/article/{article[0]}" class="btn">阅读全文</a>
            </div>'''
        
        if not articles_html:
            articles_html = '<div class="card"><p>暂无文章</p></div>'
        
        content = render_template('index', articles=articles_html)
        html = render_template('base', title='首页 - Flask博客', content=content, user_menu=get_user_menu())
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def show_article(self, article_id):
        global current_user
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取文章信息
        cursor.execute('''
            SELECT a.title, a.content, a.created_at, a.updated_at, a.views, u.username, c.name 
            FROM article a 
            JOIN user u ON a.author_id = u.id 
            JOIN category c ON a.category_id = c.id 
            WHERE a.id = ?
        ''', (article_id,))
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            self.send_error(404)
            return
        
        # 记录浏览历史（仅登录用户）
        if current_user:
            # 更新或插入浏览记录
            cursor.execute('''
                INSERT OR REPLACE INTO article_view_history (user_id, article_id, viewed_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (current_user['id'], article_id))
            
            # 更新文章浏览计数
            cursor.execute('UPDATE article SET views = views + 1 WHERE id = ?', (article_id,))
            conn.commit()
        
        conn.close()
        
        content = render_template('article_detail',
                                 title=article[0],
                                 content=article[1],
                                 created_at=article[2],
                                 updated_at=article[3],
                                 views=article[4] + (1 if current_user else 0),
                                 author=article[5],
                                 category=article[6])
        
        html = render_template('base', title=f'{article[0]} - Flask博客', content=content, user_menu=get_user_menu())
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def show_login(self):
        content = render_template('login')
        html = render_template('base', title='登录 - Flask博客', content=content, user_menu=get_user_menu())
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def show_register(self):
        content = render_template('register')
        html = render_template('base', title='注册 - Flask博客', content=content, user_menu=get_user_menu())
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def show_browsing_history(self):
        global current_user
        
        if not current_user:
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取最近一个月的浏览历史
        cursor.execute('''
            SELECT a.title, c.name, h.viewed_at, a.id
            FROM article_view_history h
            JOIN article a ON h.article_id = a.id
            JOIN category c ON a.category_id = c.id
            WHERE h.user_id = ? AND h.viewed_at >= datetime('now', '-30 days')
            ORDER BY h.viewed_at DESC
        ''', (current_user['id'],))
        
        history = cursor.fetchall()
        conn.close()
        
        if history:
            history_html = '<div class="history-list">'
            for item in history:
                history_html += f'''
                <div class="history-item">
                    <div class="history-content">
                        <h3><a href="/article/{item[3]}">{item[0]}</a></h3>
                        <div class="history-meta">
                            <span>分类: {item[1]}</span>
                            <span>浏览时间: {item[2]}</span>
                        </div>
                    </div>
                    <div class="history-actions">
                        <a href="/article/{item[3]}" class="btn btn-sm">查看文章</a>
                    </div>
                </div>'''
            history_html += '</div>'
        else:
            history_html = '''<div class="empty-state">
                <p>您还没有浏览过任何文章</p>
                <a href="/" class="btn">去浏览文章</a>
            </div>'''
        
        content = render_template('browsing_history', history_content=history_html)
        html = render_template('base', title='浏览历史 - Flask博客', content=content, user_menu=get_user_menu())
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

def run_server():
    init_db()
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, BlogHandler)
    print('服务器启动在 http://localhost:5000')
    print('演示账号: demo/demo123')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()