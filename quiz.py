import os
import uuid
import random
import time
import hmac
import secrets
import re
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageOps
from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, FileField, SelectField
from wtforms.validators import InputRequired, Optional
from passlib.hash import sha256_crypt
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# PythonAnywhere WSGI farklı klasörden başlar; .env'i quiz.py yanından oku
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
for _env_path in (
    os.path.join(_APP_DIR, ".env"),
    os.path.join(_APP_DIR, "sorsana.env"),
    "/home/sorsana/.env",
    "/home/sorsana/sorsana.env",
):
    if os.path.isfile(_env_path):
        load_dotenv(_env_path, override=False)
load_dotenv(override=False)

# === UYGULAMA AYARLARI (CONFIG) ===
app = Flask(__name__)

# PythonAnywhere varsayılanları — .env varsa onu kullanır
app.secret_key = os.getenv("SECRET_KEY") or "sorsana-secret-key-2026"

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST") or "sorsana.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER") or "sorsana"
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD") or "Sorsana2026!"
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB") or "sorsana$quizes"
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT") or 3306)
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if os.path.isdir("/home/sorsana"):
    app.config["SESSION_COOKIE_SECURE"] = True

# Mail Ayarları
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME") or "sorsana.iletisim@gmail.com"
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# Dosya Yükleme Ayarları
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
base_dir = app.root_path
UPLOAD_ROOT = '/home/sorsana/static/uploads' if os.path.isdir('/home/sorsana') else os.path.join(base_dir, 'static', 'uploads')

app.config['UPLOAD_FOLDER_QUIZ_COVERS'] = os.path.join(UPLOAD_ROOT, 'quiz_covers')
app.config['UPLOAD_FOLDER_PROFILE_PICS'] = os.path.join(UPLOAD_ROOT, 'profile_pics')
app.config['UPLOAD_FOLDER_PROFILE'] = app.config['UPLOAD_FOLDER_PROFILE_PICS']
app.config['UPLOAD_FOLDER_QUIZ_IMAGES'] = os.path.join(UPLOAD_ROOT, 'quiz_images')
app.config['UPLOAD_FOLDER'] = app.config['UPLOAD_FOLDER_QUIZ_IMAGES']

os.makedirs(app.config['UPLOAD_FOLDER_QUIZ_COVERS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_PROFILE_PICS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_QUIZ_IMAGES'], exist_ok=True)

mysql = MySQL(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# === YARDIMCI FONKSİYONLAR ===

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_optimized_image(file_storage, save_path, target_size=(1200, 1600), max_size=None, quality=90):
    """Resimleri optimize ederek kaydeder. max_size eski çağrılar için alias."""
    if max_size:
        target_size = max_size
    try:
        img = Image.open(file_storage)
        img = img.convert("RGB")
        background = ImageOps.fit(img, target_size, method=Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=16))
        img.thumbnail(target_size, Image.LANCZOS)
        bg_w, bg_h = target_size
        img_w, img_h = img.size
        offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
        background.paste(img, offset)
        background.save(save_path, format='JPEG', optimize=True, quality=quality, progressive=True)
    except Exception as e:
        print(f"Resim işleme hatası: {e}")
        try:
            file_storage.seek(0)
            file_storage.save(save_path)
        except Exception:
            pass

def slim_contestant(row):
    return {
        "question_id": row.get("question_id"),
        "question_text": row.get("question_text") or "",
        "image_url": row.get("image_url") or "",
    }

MIN_PHOTO_ITEMS = 10
MIN_BLIND_ITEMS = 10
MIN_PLAY_ITEMS = 2
MIN_CLASSIC_QUESTIONS = 3

def delete_quiz_cascade(cursor, quiz_id):
    cursor.execute("DELETE FROM questions WHERE quiz_id = %s", (quiz_id,))
    for table in ("quiz_likes", "quiz_saves", "quiz_results"):
        try:
            cursor.execute("DELETE FROM {} WHERE quiz_id = %s".format(table), (quiz_id,))
        except Exception:
            pass
    cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))

def ensure_quiz_draft_column(cursor):
    try:
        cursor.execute("ALTER TABLE quizzes ADD COLUMN is_draft TINYINT(1) NOT NULL DEFAULT 0")
    except Exception:
        pass

EMAIL_TOKEN_MAX_AGE = 3600
UNVERIFIED_TTL_HOURS = 24
REGISTER_IP_LIMIT = 5
REGISTER_IP_WINDOW = 3600
_register_hits = {}
_reset_hits = {}
GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}
USERNAME_RE = re.compile(r"^[a-z0-9_]{5,24}$")

def client_ip():
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return forwarded or (request.remote_addr or "0.0.0.0")

def normalize_email(email):
    raw = (email or "").strip().lower()
    if "@" not in raw:
        return raw
    local, domain = raw.rsplit("@", 1)
    if domain in GMAIL_DOMAINS:
        domain = "gmail.com"
        local = local.split("+", 1)[0].replace(".", "")
    return local + "@" + domain

def ensure_auth_columns(cursor):
    for stmt in (
        "ALTER TABLE users ADD COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN email_norm VARCHAR(120) NULL",
        "ALTER TABLE users ADD COLUMN google_id VARCHAR(64) NULL",
    ):
        try:
            cursor.execute(stmt)
        except Exception:
            pass

def looks_like_bot_username(username):
    u = username or ""
    if not USERNAME_RE.match(u):
        return True
    vowels = sum(ch in "aeiou" for ch in u)
    if len(u) >= 14 and vowels <= 2:
        return True
    unique_ratio = len(set(u)) / float(len(u))
    if len(u) >= 16 and unique_ratio >= 0.75 and vowels <= 3:
        return True
    return False

def issue_csrf():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token
    return token

def csrf_ok():
    sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token") or ""
    expected = session.get("csrf_token") or ""
    if not sent or not expected:
        return False
    return hmac.compare_digest(str(sent), str(expected))

def register_rate_limited():
    ip = client_ip()
    now = time.time()
    hits = [t for t in _register_hits.get(ip, []) if now - t < REGISTER_IP_WINDOW]
    if len(hits) >= REGISTER_IP_LIMIT:
        _register_hits[ip] = hits
        return True
    hits.append(now)
    _register_hits[ip] = hits
    return False

def reset_rate_limited():
    ip = client_ip()
    now = time.time()
    hits = [t for t in _reset_hits.get(ip, []) if now - t < REGISTER_IP_WINDOW]
    if len(hits) >= REGISTER_IP_LIMIT:
        _reset_hits[ip] = hits
        return True
    hits.append(now)
    _reset_hits[ip] = hits
    return False

def delete_user_cascade(cursor, user_id):
    cursor.execute("SELECT quiz_id FROM quizzes WHERE user_id = %s", (user_id,))
    for row in cursor.fetchall() or []:
        delete_quiz_cascade(cursor, row["quiz_id"])
    for table in ("quiz_likes", "quiz_saves"):
        try:
            cursor.execute("DELETE FROM {} WHERE user_id = %s".format(table), (user_id,))
        except Exception:
            pass
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

def purge_unverified_users():
    try:
        cursor = mysql.connection.cursor()
        ensure_auth_columns(cursor)
        cursor.execute(
            """
            SELECT id FROM users
            WHERE IFNULL(is_verified, 0) = 0
              AND IFNULL(is_admin, 0) = 0
              AND COALESCE(created_at, register_date) < DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            % UNVERIFIED_TTL_HOURS
        )
        ids = [row["id"] for row in (cursor.fetchall() or [])]
        for user_id in ids:
            try:
                cursor.execute("SELECT google_id FROM users WHERE id = %s", (user_id,))
                g = cursor.fetchone() or {}
                if g.get("google_id"):
                    continue
            except Exception:
                pass
            delete_user_cascade(cursor, user_id)
        if ids:
            mysql.connection.commit()
        cursor.close()
    except Exception:
        pass

def purge_abandoned_quizzes():
    try:
        cursor = mysql.connection.cursor()
        ensure_quiz_draft_column(cursor)
        cursor.execute(
            """
            SELECT q.quiz_id
            FROM quizzes q
            LEFT JOIN questions qs ON qs.quiz_id = q.quiz_id
            WHERE q.is_published = 0 AND IFNULL(q.is_draft, 0) = 0
            GROUP BY q.quiz_id
            HAVING (
                COUNT(qs.question_id) = 0
                AND MAX(q.created_at) < DATE_SUB(NOW(), INTERVAL 12 MINUTE)
            ) OR MAX(q.created_at) < DATE_SUB(NOW(), INTERVAL 2 HOUR)
            """
        )
        ids = [row["quiz_id"] for row in (cursor.fetchall() or [])]
        for quiz_id in ids:
            delete_quiz_cascade(cursor, quiz_id)
        if ids:
            mysql.connection.commit()
        cursor.close()
    except Exception:
        pass

def load_photo_pool(quiz_id, min_items=MIN_PLAY_ITEMS, mode_label="Bu mod"):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        cursor.close()
        return None, None, ("Quiz bulunamadı.", "danger", "index", {})
    if quiz.get("quiz_type") != "turnuva":
        cursor.close()
        return None, None, ("Bu oyun modu yalnızca fotoğraf havuzu quizlerinde oynanır.", "warning", "quiz_detail", {"quiz_id": quiz_id})
    if not can_view_quiz(quiz):
        cursor.close()
        return None, None, ("Bu içerik taslak. Yalnızca hazırlayanı görebilir.", "warning", "index", {})
    cursor.execute("SELECT question_id, question_text, image_url FROM questions WHERE quiz_id = %s", (quiz_id,))
    items = [slim_contestant(row) for row in cursor.fetchall() if row.get("image_url")]
    if len(items) < min_items:
        cursor.close()
        return None, None, (f"{mode_label} için en az {min_items} fotoğraflı aday gerekir.", "danger", "quiz_detail", {"quiz_id": quiz_id})
    try:
        cursor.execute("UPDATE quizzes SET views = views + 1 WHERE quiz_id = %s", (quiz_id,))
        mysql.connection.commit()
    except Exception:
        pass
    cursor.close()
    random.shuffle(items)
    payload = [{
        "id": item["question_id"],
        "name": item["question_text"],
        "image": url_for("static", filename="uploads/quiz_images/" + item["image_url"]),
    } for item in items]
    return quiz, payload, None

def can_view_quiz(quiz):
    if not quiz:
        return False
    if quiz.get("is_published"):
        return True
    uid = session.get("user_id")
    if uid is not None and int(quiz.get("user_id") or 0) == int(uid):
        return True
    return bool(session.get("is_admin"))

def block_private_quiz(quiz):
    if can_view_quiz(quiz):
        return None
    flash("Bu içerik taslak. Yalnızca hazırlayanı görebilir.", "warning")
    return redirect(url_for("index"))

YASAKLI_KELIMELER = [ "aptal", "amk"]

def icerik_uygun_mu(metin):
    if not metin:
        return True
    metin = metin.lower()
    for kelime in YASAKLI_KELIMELER:
        if kelime in metin:
            return False
    return True

# === DECORATORS ===

def wants_json():
    return request.headers.get("X-Requested-With") == "fetch"

_login_guard = {}
LOGIN_FAIL_LIMIT = 5
LOGIN_LOCK_SECONDS = 15 * 60

def _login_guard_key():
    ident = (request.form.get("username") or "").strip().lower()
    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
    return ip + "|" + ident

def login_lock_remaining():
    rec = _login_guard.get(_login_guard_key()) or {}
    until = rec.get("until", 0)
    if until > time.time():
        return int(until - time.time())
    return 0

def record_login_failure():
    key = _login_guard_key()
    rec = _login_guard.get(key) or {"fails": 0, "until": 0}
    rec["fails"] = rec.get("fails", 0) + 1
    if rec["fails"] >= LOGIN_FAIL_LIMIT:
        rec["until"] = time.time() + LOGIN_LOCK_SECONDS
        rec["fails"] = 0
    _login_guard[key] = rec

def clear_login_failures():
    _login_guard.pop(_login_guard_key(), None)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            if wants_json():
                return jsonify(ok=False, login=True), 401
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session or not session.get("is_admin"):
            flash("Bu sayfaya erişim yetkiniz yok!", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# === FORM SINIFLARI ===

class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min=4, max=40), validators.DataRequired()])
    username = StringField("Kullanıcı Adı", validators=[
        validators.Length(min=5, max=24),
        validators.Regexp(r"^[A-Za-z0-9_]+$", message="Kullanıcı adı yalnızca harf, rakam ve alt çizgi olabilir."),
    ])
    email = StringField("E Mail", validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz...")])
    password = PasswordField("Parola:", validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyiniz."),
        validators.Length(min=8, message="Parola en az 8 karakter olmalı."),
        validators.EqualTo(fieldname="confirm", message="Parolanız Uyuşmuyor.")
    ])
    confirm = PasswordField("Parola Doğrula")
    website = StringField("Website")

class LoginForm(Form):
    username = StringField("", render_kw={"placeholder": "Kullanıcı Adı veya Email "})
    password = PasswordField("", render_kw={"placeholder": "Şifre"})

class ForgotPasswordForm(Form):
    email = StringField("E-posta", validators=[validators.Email(message="Geçerli bir e-posta gir.")])
    website = StringField("Website")

class ResetPasswordForm(Form):
    password = PasswordField("Yeni parola", validators=[
        validators.DataRequired(message="Parola gerekli."),
        validators.Length(min=8, message="Parola en az 8 karakter olmalı."),
        validators.EqualTo(fieldname="confirm", message="Parolalar uyuşmuyor."),
    ])
    confirm = PasswordField("Parola tekrar")

class QuizCreateForm(Form):
    title = StringField("Quiz Başlığı", validators=[validators.Length(min=5, max=255), validators.DataRequired(message="Lütfen bir başlık girin")])
    description = TextAreaField("Açıklama")
    category = SelectField("Kategori", choices=[
        ('Genel', '🌍 Genel'), ('Oyun', '🎮 Oyun'), ('Müzik', '🎵 Müzik'),
        ('Film', '🎬 Film & Dizi'), ('Spor', '⚽ Spor'), ('Anime', '🎌 Anime'),
        ('Eğlence', '🎉 Eğlence'), ('Teknoloji', '💻 Teknoloji'), ('Bilim', '🧪 Bilim'),
        ('Tarih', '📜 Tarih'), ('Yemek', '🍔 Yemek'), ('Doğa', '🌲 Doğa'),
        ('Sanat', '🎨 Sanat'), ('Eğitim', '📚 Eğitim'), ('Yaşam', '🧘 Yaşam'),
        ('Yayıncı', '📹 Yayıncılar')
    ])
    cover_image = FileField('Kapak Fotoğrafı (Opsiyonel)', validators=[Optional()])
    quiz_type = RadioField("Quiz Tipi",
                           choices=[('klasik_test', 'Klasik Test (Sonuç Odaklı)'),
                                    ('turnuva', 'Fotoğraf Havuzu (Turnuva + Kör Sıralama)')],
                           default='klasik_test',
                           validators=[validators.DataRequired(message="Lütfen bir quiz tipi seçin")])

class QuestionAddForm(Form):
    question_text = TextAreaField("Soru Metni", validators=[validators.DataRequired(message="Soru alanı boş bırakılamaz")])
    option_a = StringField("A Seçeneği", validators=[validators.DataRequired()])
    option_b = StringField("B Seçeneği", validators=[validators.DataRequired()])
    option_c = StringField("C Seçeneği", validators=[validators.DataRequired()])
    option_d = StringField("D Seçeneği", validators=[validators.DataRequired()])

class PollItemForm(Form):
    item_name = StringField("Seçenek Adı (Opsiyonel)")
    item_image = FileField('Seçenek Fotoğrafı', validators=[InputRequired(message="Lütfen bir fotoğraf seçin")])

class ProfileEditForm(Form):
    profile_image = FileField('Yeni Profil Fotoğrafı', validators=[InputRequired(message="Lütfen bir fotoğraf seçin")])

# === ROTALAR (ROUTES) ===

@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    keyword = (request.args.get("keyword") or "").strip()
    params = []
    sorgu = """
        SELECT q.*, u.name as author_name
        FROM quizzes q
        JOIN users u ON q.user_id = u.id
        WHERE q.is_published = 1
    """
    if keyword:
        like = f"%{keyword}%"
        sorgu += " AND (q.title LIKE %s OR q.description LIKE %s OR q.category LIKE %s)"
        params.extend([like, like, like])
    sorgu += " ORDER BY q.created_at DESC"
    result = cursor.execute(sorgu, params) if params else cursor.execute(sorgu)
    all_quizzes = cursor.fetchall() if result > 0 else []
    cursor.close()

    # --- VERİLERİ GRUPLAMA MANTIĞI ---
    grouped_quizzes = {
        'Trendler': [],
        'En Yeniler': [],
        'Teknoloji': [],
        'Eğlence': [],
        'Spor': [],
        'Film & Dizi': [],
        'Oyun': [],
        'Müzik': [],
        'Genel Kültür': []
    }
    grouped_quizzes['En Yeniler'] = all_quizzes[:12]
    grouped_quizzes['Trendler'] = sorted(all_quizzes, key=lambda x: x.get('views') or 0, reverse=True)[:12]
    cat_map = {
        'Teknoloji': 'Teknoloji',
        'Eğlence': 'Eğlence',
        'Spor': 'Spor',
        'Film': 'Film & Dizi',
        'Oyun': 'Oyun',
        'Müzik': 'Müzik',
        'Genel': 'Genel Kültür',
    }
    for quiz in all_quizzes:
        key = cat_map.get(quiz.get('category'))
        if key:
            grouped_quizzes[key].append(quiz)
    final_groups = {k: v for k, v in grouped_quizzes.items() if v}
    return render_template("index.html", grouped_quizzes=final_groups, keyword=keyword)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST":
        if (form.website.data or "").strip():
            return render_template("verify_email_sent.html", email=form.email.data or "")
        if not csrf_ok():
            flash("Oturum doğrulaması başarısız. Sayfayı yenileyip tekrar dene.", "danger")
            return render_template("register.html", form=form)
        if register_rate_limited():
            flash("Çok fazla kayıt denemesi. Bir süre sonra tekrar dene.", "danger")
            return render_template("register.html", form=form)
        if not form.validate():
            return render_template("register.html", form=form)

        name = (form.name.data or "").strip()
        username = (form.username.data or "").strip().lower()
        email = (form.email.data or "").strip().lower()
        email_norm = normalize_email(email)
        if looks_like_bot_username(username):
            flash("Bu kullanıcı adı kabul edilmedi. Daha okunaklı bir ad seç.", "danger")
            return render_template("register.html", form=form)

        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        ensure_auth_columns(cursor)
        try:
            cursor.execute(
                """
                SELECT id FROM users
                WHERE username = %s OR email = %s OR email = %s OR IFNULL(email_norm, '') = %s
                """,
                (username, email, email_norm, email_norm),
            )
        except Exception:
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            flash("Bu e-posta adresi veya kullanıcı adı zaten alınmış!", "danger")
            cursor.close()
            return redirect(url_for("register"))

        default_profile_pic = "default.png"
        try:
            cursor.execute(
                """
                INSERT INTO users(name, email, email_norm, username, password, profile_pic_url, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, 0)
                """,
                (name, email, email_norm, username, password, default_profile_pic),
            )
        except Exception:
            cursor.execute(
                "INSERT INTO users(name,email,username,password,profile_pic_url, is_verified) VALUES(%s,%s,%s,%s,%s, 0)",
                (name, email, username, password, default_profile_pic),
            )
        mysql.connection.commit()
        cursor.close()

        token = s.dumps(email_norm, salt="email-confirm")
        msg = Message("SorSana Hesap Doğrulama", sender="sorsana.iletisim@gmail.com", recipients=[email])
        link = url_for("confirm_email", token=token, _external=True)
        msg.body = (
            "Merhaba {}! SorSana ailesine hoş geldin. Hesabını aktifleştirmek için "
            "1 saat içinde şu linke tıkla: {}".format(name, link)
        )
        try:
            mail.send(msg)
            return render_template("verify_email_sent.html", email=email)
        except Exception:
            flash("Mail gönderilemedi, ama kaydın alındı. Doğrulama mailini daha sonra isteyebilirsin.", "danger")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        if not csrf_ok():
            flash("Oturum doğrulaması başarısız. Sayfayı yenileyip tekrar dene.", "danger")
            return render_template("login.html", form=form)
        wait = login_lock_remaining()
        if wait > 0:
            mins = max(1, wait // 60)
            flash("Çok fazla hatalı deneme. {} dakika sonra tekrar dene.".format(mins), "danger")
            return render_template("login.html", form=form)
        username_or_email = (form.username.data or "").strip()
        password_entered = form.password.data
        email_norm = normalize_email(username_or_email)
        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s OR email = %s OR IFNULL(email_norm, '') = %s",
                (username_or_email, username_or_email, email_norm),
            )
        except Exception:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s OR email = %s",
                (username_or_email, username_or_email),
            )
        data = cursor.fetchone()
        cursor.close()
        ok = False
        if data:
            try:
                ok = sha256_crypt.verify(password_entered, data["password"])
            except Exception:
                ok = False
        if ok:
            if data.get("is_verified") == 0:
                flash("Lütfen önce mail adresine gelen linke tıklayarak hesabını doğrula!", "warning")
                return redirect(url_for("login"))
            clear_login_failures()
            flash("Başarıyla giriş yaptınız", "success")
            session["logged_in"] = True
            session["username"] = data["username"]
            session["user_id"] = data["id"]
            session["profile_pic_url"] = data["profile_pic_url"]
            session["is_admin"] = (data["is_admin"] == 1)
            return redirect(url_for("index"))
        record_login_failure()
        flash("Kullanıcı adı veya şifre hatalı.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html", form=form)

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt="email-confirm", max_age=EMAIL_TOKEN_MAX_AGE)
    except Exception:
        flash("Doğrulama linki geçersiz veya süresi dolmuş (1 saat).", "danger")
        return redirect(url_for("login"))

    email_norm = normalize_email(email)
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET is_verified = 1 WHERE email = %s OR email = %s OR IFNULL(email_norm, '') = %s",
            (email, email_norm, email_norm),
        )
    except Exception:
        cursor.execute("UPDATE users SET is_verified = 1 WHERE email = %s", [email])
    mysql.connection.commit()
    cursor.close()

    flash("Hesabın başarıyla doğrulandı! Artık giriş yapabilirsin.", "success")
    return redirect(url_for('login'))

@app.route("/sifremi-unuttum", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm(request.form)
    if request.method == "POST":
        if (form.website.data or "").strip():
            flash("Eğer bu e-posta kayıtlıysa, sıfırlama bağlantısı gönderildi.", "success")
            return redirect(url_for("login"))
        if not csrf_ok():
            flash("Oturum doğrulaması başarısız. Sayfayı yenileyip tekrar dene.", "danger")
            return render_template("forgot_password.html", form=form)
        if reset_rate_limited():
            flash("Çok fazla deneme. Bir süre sonra tekrar dene.", "danger")
            return render_template("forgot_password.html", form=form)
        if not form.validate():
            return render_template("forgot_password.html", form=form)

        email = (form.email.data or "").strip().lower()
        email_norm = normalize_email(email)
        cursor = mysql.connection.cursor()
        ensure_auth_columns(cursor)
        try:
            cursor.execute(
                "SELECT id, name, email FROM users WHERE email = %s OR IFNULL(email_norm, '') = %s",
                (email, email_norm),
            )
        except Exception:
            cursor.execute("SELECT id, name, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            token = s.dumps(email_norm or email, salt="password-reset")
            link = url_for("reset_password", token=token, _external=True)
            msg = Message(
                "SorSana şifre sıfırlama",
                sender=app.config.get("MAIL_USERNAME") or "sorsana.iletisim@gmail.com",
                recipients=[user.get("email") or email],
            )
            msg.body = (
                "Merhaba {}!\n\nŞifreni yenilemek için 1 saat içinde şu bağlantıya tıkla:\n{}\n\n"
                "Bu isteği sen yapmadıysan bu maili yok say."
            ).format(user.get("name") or "", link)
            try:
                mail.send(msg)
            except Exception:
                pass
        flash("Eğer bu e-posta kayıtlıysa, sıfırlama bağlantısı gönderildi.", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html", form=form)

@app.route("/sifre-sifirla/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="password-reset", max_age=EMAIL_TOKEN_MAX_AGE)
    except Exception:
        flash("Sıfırlama bağlantısı geçersiz veya süresi dolmuş (1 saat).", "danger")
        return redirect(url_for("forgot_password"))

    form = ResetPasswordForm(request.form)
    if request.method == "POST":
        if not csrf_ok():
            flash("Oturum doğrulaması başarısız. Sayfayı yenileyip tekrar dene.", "danger")
            return render_template("reset_password.html", form=form)
        if not form.validate():
            return render_template("reset_password.html", form=form)
        hashed = sha256_crypt.encrypt(form.password.data)
        email_norm = normalize_email(email)
        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE users
                SET password = %s, is_verified = 1
                WHERE email = %s OR email = %s OR IFNULL(email_norm, '') = %s
                """,
                (hashed, email, email_norm, email_norm),
            )
        except Exception:
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
        mysql.connection.commit()
        cursor.close()
        flash("Şifren güncellendi. Şimdi giriş yapabilirsin.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form)

# === NAVBAR İÇİN OTOMATİK VERİ ÇEKİCİ (CONTEXT PROCESSOR) ===
@app.context_processor
def inject_csrf():
    return dict(csrf_token=issue_csrf)

@app.context_processor
def inject_navbar_data():
    """Bu fonksiyon her şablona otomatik olarak 'top_5_quizzes' değişkenini gönderir."""
    try:
        cursor = mysql.connection.cursor()
        # DÜZELTME: Sadece yayındaki quizleri öner
        sorgu = "SELECT quiz_id, title, category, views FROM quizzes WHERE is_published = 1 ORDER BY views DESC LIMIT 5"
        cursor.execute(sorgu)
        top_quizzes = cursor.fetchall()
        cursor.close()
        return dict(navbar_top_quizzes=top_quizzes)
    except Exception as e:
        return dict(navbar_top_quizzes=[])

# === ÖNERİLENLER SAYFASI ROTASI ===
@app.route("/onerilenler")
def onerilenler():
    cursor = mysql.connection.cursor()
    # DÜZELTME: Sadece yayındaki quizleri getir
    cursor.execute("SELECT q.*, u.name as author_name FROM quizzes q JOIN users u ON q.user_id = u.id WHERE q.is_published = 1 ORDER BY q.views DESC LIMIT 50")
    quizzes = cursor.fetchall()
    cursor.close()
    return render_template("index.html", grouped_quizzes={'Popüler': quizzes} if quizzes else {}, keyword='')

# === QUIZ OLUŞTURMA İŞLEMLERİ ===

@app.route("/create_quiz", methods=["GET", "POST"])
@login_required
def create_quiz():
    form = QuizCreateForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        description = form.description.data
        category = form.category.data
        quiz_type = form.quiz_type.data

        if not icerik_uygun_mu(title) or not icerik_uygun_mu(description):
            flash("Quiz başlığında veya açıklamasında uygunsuz ifadeler tespit edildi!", "danger")
            return render_template("create_quiz.html", form=form)

        user_id = session["user_id"]

        # Resim Yükleme Kısmı
        file = request.files.get('cover_image')
        cover_image_filename = 'zirael.png'

        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER_QUIZ_COVERS'], unique_filename)
            save_optimized_image(file, file_path, target_size=(1400, 900), quality=90)
            cover_image_filename = unique_filename

        cursor = mysql.connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO quizzes (user_id, title, description, category, quiz_type, cover_image_url, is_published, is_draft)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0)
                """,
                (user_id, title, description, category, quiz_type, cover_image_filename),
            )
        except Exception:
            cursor.execute(
                """
                INSERT INTO quizzes (user_id, title, description, category, quiz_type, cover_image_url, is_published)
                VALUES (%s, %s, %s, %s, %s, %s, 0)
                """,
                (user_id, title, description, category, quiz_type, cover_image_filename),
            )

        mysql.connection.commit()

        # Otomatik oluşan ID'yi al
        quiz_id = cursor.lastrowid
        cursor.close()

        if not quiz_id or quiz_id == 0:
            flash("Quiz oluşturuldu ama ID alınamadı. Paylaştıklarım sayfasından düzenleyin.", "warning")
            return redirect(url_for("paylastiklarim"))

        flash("Stüdyo açıldı. Yayınlamadan çıkarsan ve taslağa kaydetmezsen bu çalışma silinir.", "warning")
        return redirect(url_for("add_questions", quiz_id=str(quiz_id)))

    return render_template("create_quiz.html", form=form)

@app.route("/add_questions/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def add_questions(quiz_id):
    cursor = mysql.connection.cursor()

    # Quiz var mı kontrol et
    sorgu_tip = "SELECT quiz_type, title, user_id FROM quizzes WHERE quiz_id = %s"
    result = cursor.execute(sorgu_tip, (quiz_id,))

    if result == 0:
        flash("Quiz bulunamadı.", "danger")
        cursor.close()
        return redirect(url_for("index"))

    quiz_data = cursor.fetchone()
    if int(quiz_data["user_id"]) != int(session["user_id"]) and not session.get("is_admin"):
        cursor.close()
        flash("Bu stüdyoya erişim yetkin yok.", "danger")
        return redirect(url_for("index"))
    quiz_type = quiz_data["quiz_type"]
    quiz_title = quiz_data["title"]

    # --- KLASİK TEST (RESİMLİ & METİNLİ) ---
    if quiz_type == 'klasik_test':
        form = QuestionAddForm(request.form)

        if request.method == "POST" and form.validate():
            question_text = form.question_text.data
            option_a = form.option_a.data
            option_b = form.option_b.data
            option_c = form.option_c.data
            option_d = form.option_d.data
            correct_answer = request.form.get('correct_answer')

            if not correct_answer:
                 flash("Lütfen doğru cevabı işaretleyin.", "danger")
                 return redirect(url_for("add_questions", quiz_id=quiz_id))

            def process_image(file_key):
                file = request.files.get(file_key)
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + "_" + filename
                    save_path = os.path.join(app.config['UPLOAD_FOLDER_QUIZ_IMAGES'], unique_filename)
                    save_optimized_image(file, save_path, target_size=(1200, 1600), quality=92)
                    return unique_filename
                return None

            q_img = process_image('question_image')
            opt_a_img = process_image('option_a_img')
            opt_b_img = process_image('option_b_img')
            opt_c_img = process_image('option_c_img')
            opt_d_img = process_image('option_d_img')

            sorgu_ekle = """
                INSERT INTO questions
                (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer,
                 question_image_url, option_a_image_url, option_b_image_url, option_c_image_url, option_d_image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sorgu_ekle, (
                quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer,
                q_img, opt_a_img, opt_b_img, opt_c_img, opt_d_img
            ))

            mysql.connection.commit()
            flash("Soru başarıyla eklendi.", "success")
            return redirect(url_for("add_questions", quiz_id=quiz_id))

        sorgu_sorular = "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_id ASC"
        cursor.execute(sorgu_sorular, (quiz_id,))
        questions = cursor.fetchall()
        cursor.close()

        return render_template("add_questions.html", form=form, quiz_id=quiz_id, quiz_title=quiz_title, questions=questions, quiz_type=quiz_type)

    # --- TURNUVA MODU ---
    elif quiz_type == 'turnuva':
        form = PollItemForm()
        if request.method == "POST":
            item_name = request.form.get('item_name')
            file = request.files.get('item_image')

            if not file or file.filename == '':
                flash("Lütfen bir fotoğraf seçin.", "danger")
                cursor.close()
                return redirect(url_for("add_questions", quiz_id=quiz_id))

            if not allowed_file(file.filename):
                flash("Geçersiz dosya tipi.", "danger")
                cursor.close()
                return redirect(url_for("add_questions", quiz_id=quiz_id))

            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER_QUIZ_IMAGES'], unique_filename)
            save_optimized_image(file, file_path, target_size=(1200, 1600), quality=92)

            sorgu_ekle = "INSERT INTO questions (quiz_id, question_text, image_url) VALUES (%s, %s, %s)"
            cursor.execute(sorgu_ekle, (quiz_id, item_name, unique_filename))
            mysql.connection.commit()

            flash(f"Seçenek '{item_name}' başarıyla eklendi.", "success")
            cursor.close()
            return redirect(url_for("add_questions", quiz_id=quiz_id))

        sorgu_mevcut = "SELECT * FROM questions WHERE quiz_id = %s"
        cursor.execute(sorgu_mevcut, (quiz_id,))
        items = cursor.fetchall()
        cursor.close()
        return render_template("add_poll_questions.html", form=form, quiz_id=quiz_id, quiz_title=quiz_title, items=items)

    return redirect(url_for("index"))

@app.route("/add_results/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def add_results(quiz_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM quiz_results WHERE quiz_id = %s", (quiz_id,))
    existing_results = cursor.fetchall()
    results_dict = {res['result_key']: res for res in existing_results}

    if request.method == "POST":
        keys = ['A', 'B', 'C', 'D']
        for key in keys:
            title = request.form.get(f'title_{key}')
            description = request.form.get(f'description_{key}')
            file = request.files.get(f'image_{key}')

            if not title: continue

            image_filename = results_dict.get(key, {}).get('image_url', 'default_result.png')
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                save_path = os.path.join(app.config['UPLOAD_FOLDER_QUIZ_COVERS'], unique_filename)
                save_optimized_image(file, save_path)
                image_filename = unique_filename

            if key in results_dict:
                cursor.execute("""UPDATE quiz_results SET title=%s, description=%s, image_url=%s WHERE id=%s""",
                               (title, description, image_filename, results_dict[key]['id']))
            else:
                cursor.execute("""INSERT INTO quiz_results (quiz_id, result_key, title, description, image_url) VALUES (%s, %s, %s, %s, %s)""",
                               (quiz_id, key, title, description, image_filename))

        mysql.connection.commit()
        flash("Sonuçlar kaydedildi. Quiz yayına hazır.", "success")
        return redirect(url_for('publish_quiz_action', quiz_id=quiz_id))

    cursor.close()
    return render_template("add_results.html", quiz_id=quiz_id, results=results_dict)

# ==========================================
#  GÜVENLİ YAYIMLAMA (VALIDATION)
# ==========================================
@app.route("/publish_quiz/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def publish_quiz_action(quiz_id):
    cursor = mysql.connection.cursor()

    # 1. Önce bu Quiz'in türünü ve sahibini bulalım
    # DÜZELTME: created_by yerine user_id kullanıldı
    sorgu = "SELECT quiz_type, title, user_id FROM quizzes WHERE quiz_id = %s"
    result = cursor.execute(sorgu, (quiz_id,))

    if result == 0:
        flash("Böyle bir quiz bulunamadı.", "danger")
        return redirect(url_for("index"))

    quiz = cursor.fetchone()

    # Güvenlik: Başkasının quizini yayınlamaya çalışmasın
    if int(quiz['user_id']) != int(session['user_id']):
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for("index"))

    # 2. İçindeki Soru/Seçenek Sayısını Sayalım
    # DÜZELTME BURADA: 'as sayi' ekledik ve [0] yerine ['sayi'] kullandık
    cursor.execute("SELECT COUNT(*) as sayi FROM questions WHERE quiz_id = %s", (quiz_id,))
    veri = cursor.fetchone()
    soru_sayisi = veri['sayi']

    quiz_type = quiz['quiz_type']
    hata_var = False

    # --- KURAL 1: KLASİK TEST ---
    if quiz_type == 'klasik_test':
        if soru_sayisi < MIN_CLASSIC_QUESTIONS:
            flash(f"Yayınlamak için en az {MIN_CLASSIC_QUESTIONS} soru ekle.", "danger")
            hata_var = True
    elif quiz_type == 'turnuva':
        if soru_sayisi < MIN_PLAY_ITEMS:
            flash(f"Yayınlamak için en az {MIN_PLAY_ITEMS} fotoğraf gerekir. Kör sıralama için {MIN_BLIND_ITEMS} aday önerilir.", "danger")
            hata_var = True

    # Eğer hata varsa, soru ekleme sayfasına geri postala
    if hata_var:
        cursor.close()
        return redirect(url_for("add_questions", quiz_id=quiz_id))

    # 3. HER ŞEY TAMAMSA YAYIMLA!
    try:
        cursor.execute("UPDATE quizzes SET is_published = 1, is_draft = 0 WHERE quiz_id = %s", (quiz_id,))
    except Exception:
        cursor.execute("UPDATE quizzes SET is_published = 1 WHERE quiz_id = %s", (quiz_id,))
    mysql.connection.commit()
    cursor.close()

    flash(f"Harika! '{quiz['title']}' başarıyla yayımlandı ve vitrine düştü.", "success")
    return redirect(url_for("quiz_detail", quiz_id=quiz_id))

# === PROFİL İŞLEMLERİ ===

@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    form = ProfileEditForm()
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()

    if request.method == "POST":
        file = request.files.get('profile_image')
        if file and allowed_file(file.filename):
            cursor.execute("SELECT profile_pic_url FROM users WHERE id = %s", (user_id,))
            old_pic = cursor.fetchone()['profile_pic_url']

            if old_pic and old_pic != 'default.png':
                old_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], old_pic)
                if os.path.exists(old_path):
                    try: os.remove(old_path)
                    except: pass

            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], unique_filename)
            save_optimized_image(file, save_path, max_size=(400, 400))

            cursor.execute("UPDATE users SET profile_pic_url = %s WHERE id = %s", (unique_filename, user_id))
            mysql.connection.commit()
            session["profile_pic_url"] = unique_filename
            flash("Profil fotoğrafınız güncellendi!", "success")
            return redirect(url_for("profil"))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as sayi FROM quizzes WHERE user_id = %s", (user_id,))
    created_count = cursor.fetchone()['sayi']

    cursor.execute("SELECT COUNT(*) as sayi FROM quiz_likes WHERE user_id = %s", (user_id,))
    liked_count = cursor.fetchone()['sayi']

    cursor.close()
    return render_template("profil.html", form=form, user=user_data, user_data=user_data, created_count=created_count, liked_count=liked_count)

@app.route("/paylastiklarim")
@login_required
def paylastiklarim():
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM quizzes WHERE user_id = %s ORDER BY created_at DESC"
    result = cursor.execute(sorgu, (user_id,))
    all_quizzes = list(cursor.fetchall() or []) if result > 0 else []
    cursor.close()
    drafts = [q for q in all_quizzes if not q.get("is_published") and q.get("is_draft")]
    quizzes = [q for q in all_quizzes if q.get("is_published")]
    return render_template("paylastiklarim.html", quizzes=quizzes, drafts=drafts)

@app.route("/save_draft/<string:quiz_id>")
@login_required
def save_draft(quiz_id):
    cursor = mysql.connection.cursor()
    ensure_quiz_draft_column(cursor)
    cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        cursor.close()
        flash("Quiz bulunamadı.", "danger")
        return redirect(url_for("paylastiklarim"))
    if int(quiz["user_id"]) != int(session["user_id"]):
        cursor.close()
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for("index"))
    if quiz.get("is_published"):
        cursor.close()
        flash("Bu quiz zaten yayında.", "info")
        return redirect(url_for("quiz_detail", quiz_id=quiz_id))
    try:
        cursor.execute("UPDATE quizzes SET is_draft = 1 WHERE quiz_id = %s", (quiz_id,))
        mysql.connection.commit()
    except Exception:
        pass
    cursor.close()
    flash("Taslağa kaydedildi. Paylaştıklarım > Taslaklar'dan devam edebilirsin.", "success")
    return redirect(url_for("paylastiklarim"))

@app.route("/kaydettiklerim")
@login_required
def kaydettiklerim():
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()
    sorgu = """
        SELECT q.*, u.name as author_name
        FROM quizzes q
        JOIN quiz_saves s ON q.quiz_id = s.quiz_id
        JOIN users u ON q.user_id = u.id
        WHERE s.user_id = %s
        ORDER BY s.id DESC
    """
    result = cursor.execute(sorgu, (user_id,))
    quizzes = cursor.fetchall() if result > 0 else None
    cursor.close()
    return render_template("kaydettiklerim.html", quizzes=quizzes)

@app.route("/bilgiler", methods=["GET", "POST"])
@login_required
def bilgiler():
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")

        sorgu = "UPDATE users SET name=%s, username=%s, email=%s WHERE id=%s"
        cursor.execute(sorgu, (name, username, email, user_id))
        mysql.connection.commit()

        session["username"] = username
        flash("Bilgileriniz başarıyla güncellendi.", "success")
        return redirect(url_for("bilgiler"))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return render_template("bilgiler.html", user=user)

# === QUIZ OYNAMA MANTIĞI ===

@app.route("/quiz/<string:quiz_id>", methods=["GET", "POST"])
def quiz_view(quiz_id):
    cursor = mysql.connection.cursor()
    sorgu_quiz = "SELECT * FROM quizzes WHERE quiz_id = %s"
    result_quiz = cursor.execute(sorgu_quiz, (quiz_id,))

    if result_quiz == 0:
        flash("Böyle bir quiz bulunamadı.", "danger")
        cursor.close()
        return redirect(url_for("index"))

    quiz_data = cursor.fetchone()
    blocked = block_private_quiz(quiz_data)
    if blocked:
        cursor.close()
        return blocked
    quiz_type = quiz_data["quiz_type"]

    # --- KLASİK TEST ---
    if quiz_type == 'klasik_test':
        sorgu_questions = "SELECT * FROM questions WHERE quiz_id = %s"
        cursor.execute(sorgu_questions, (quiz_id,))
        questions_data = cursor.fetchall()

        if request.method == "GET":
            try:
                cursor.execute("UPDATE quizzes SET views = views + 1 WHERE quiz_id = %s", (quiz_id,))
                mysql.connection.commit()
            except: pass
            cursor.close()
            return render_template("quiz_view.html", quiz=quiz_data, questions=questions_data)

        if request.method == "POST":
            user_choices = []
            for question in questions_data:
                answer = request.form.get(f"cevap_{question['question_id']}")
                if answer: user_choices.append(answer)

            if not user_choices:
                flash("Lütfen soruları cevaplayın.", "danger")
                cursor.close()
                return redirect(url_for('quiz_view', quiz_id=quiz_id))

            from collections import Counter
            counts = Counter(user_choices)
            most_common_letter = counts.most_common(1)[0][0]

            sorgu_sonuc = "SELECT * FROM quiz_results WHERE quiz_id = %s AND result_key = %s"
            cursor.execute(sorgu_sonuc, (quiz_id, most_common_letter))
            final_result = cursor.fetchone()

            if not final_result:
                final_result = {
                    'title': 'Sonuç Belirlenemedi',
                    'description': 'Bu test için henüz bir sonuç tanımlanmamış.',
                    'image_url': quiz_data['cover_image_url']
                }
            cursor.close()
            return render_template("result.html", result=final_result, quiz=quiz_data)

    # --- TURNUVA MODU ---
    elif quiz_type == 'turnuva':
        session_list_key = f'tournament_list_{quiz_id}'
        session_winners_key = f'winners_list_{quiz_id}'
        session_round_key = f'tournament_round_{quiz_id}'

        if request.method == "POST":
            vote_id = request.form.get('vote')
            winners_list = session.get(session_winners_key, [])
            current_list = session.get(session_list_key, [])

            winner_data = next((item for item in current_list if str(item['question_id']) == str(vote_id)), None)

            if winner_data:
                winners_list.append(slim_contestant(winner_data))
                session[session_winners_key] = winners_list

            current_list = current_list[2:]
            session[session_list_key] = current_list
            session.modified = True
            cursor.close()
            return redirect(url_for("quiz_view", quiz_id=quiz_id))

        if session_list_key not in session or not session.get(session_list_key):
            if session_winners_key in session and len(session.get(session_winners_key)) > 1:
                new_list = session.get(session_winners_key, [])
                random.shuffle(new_list)
                session[session_list_key] = new_list
                session[session_winners_key] = []
                session[session_round_key] = len(new_list)
                session.modified = True
            elif session_winners_key in session and len(session.get(session_winners_key)) == 1:
                winner = session[session_winners_key][0]
                session.pop(session_list_key, None)
                session.pop(session_winners_key, None)
                session.pop(session_round_key, None)
                session.modified = True
                cursor.close()
                return render_template("tournament_winner.html", quiz=quiz_data, winner=winner)
            else:
                try:
                    cursor.execute("UPDATE quizzes SET views = views + 1 WHERE quiz_id = %s", (quiz_id,))
                    mysql.connection.commit()
                except: pass

                sorgu_questions = "SELECT * FROM questions WHERE quiz_id = %s"
                cursor.execute(sorgu_questions, (quiz_id,))
                questions_data = list(cursor.fetchall())

                if len(questions_data) < MIN_PLAY_ITEMS:
                    flash(f"Turnuva için en az {MIN_PLAY_ITEMS} fotoğraf gerekir.", "danger")
                    cursor.close()
                    return redirect(url_for("quiz_detail", quiz_id=quiz_id))

                random.shuffle(questions_data)
                session[session_list_key] = [slim_contestant(q) for q in questions_data]
                session[session_winners_key] = []
                session[session_round_key] = len(questions_data)
                session.modified = True

        current_list = session.get(session_list_key, [])

        if len(current_list) == 1:
             winners_list = session.get(session_winners_key, [])
             winners_list.append(current_list[0])
             session[session_winners_key] = winners_list
             session[session_list_key] = []
             session.modified = True
             return redirect(url_for("quiz_view", quiz_id=quiz_id))

        if len(current_list) == 0:
            return redirect(url_for("quiz_view", quiz_id=quiz_id))

        item1 = current_list[0]
        item2 = current_list[1]
        current_round = session.get(session_round_key, len(current_list))
        cursor.close()
        return render_template("tournament_view.html", quiz=quiz_data, item1=item1, item2=item2, round=current_round, remaining=len(current_list))
    else:
        flash("Bilinmeyen quiz tipi.", "danger")
        cursor.close()
        return redirect(url_for("index"))

@app.route("/like_quiz/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def like_quiz(quiz_id):
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT like_id FROM quiz_likes WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM quiz_likes WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
        cursor.execute("UPDATE quizzes SET likes = GREATEST(likes - 1, 0) WHERE quiz_id = %s", (quiz_id,))
        liked = False
    else:
        cursor.execute("INSERT INTO quiz_likes (user_id, quiz_id) VALUES (%s, %s)", (user_id, quiz_id))
        cursor.execute("UPDATE quizzes SET likes = likes + 1 WHERE quiz_id = %s", (quiz_id,))
        liked = True
    mysql.connection.commit()
    cursor.execute("SELECT likes FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    row = cursor.fetchone()
    count = (row or {}).get("likes", 0)
    cursor.close()
    if wants_json():
        return jsonify(ok=True, liked=liked, likes=count)
    return redirect(request.referrer or url_for("quiz_detail", quiz_id=quiz_id))

@app.route("/leaderboard")
def leaderboard():
    cursor = mysql.connection.cursor()
    sorgu = """
        SELECT users.id, users.username, users.name, users.profile_pic_url,
            COALESCE(SUM(quizzes.views), 0) as total_views,
            COALESCE(SUM(quizzes.likes), 0) as total_likes
        FROM users LEFT JOIN quizzes ON users.id = quizzes.user_id
        GROUP BY users.id ORDER BY total_views DESC LIMIT 20
    """
    cursor.execute(sorgu)
    users = cursor.fetchall()
    cursor.close()
    return render_template("leaderboard.html", users=users)

@app.route("/quiz_detail/<string:quiz_id>")
def quiz_detail(quiz_id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT q.*, u.username, u.profile_pic_url FROM quizzes q JOIN users u ON q.user_id = u.id WHERE q.quiz_id = %s"
    cursor.execute(sorgu, (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash("Quiz bulunamadı.", "danger")
        return redirect(url_for('index'))

    blocked = block_private_quiz(quiz)
    if blocked:
        cursor.close()
        return blocked

    cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = %s", (quiz_id,))
    question_count = cursor.fetchone()['count']

    is_liked = False
    is_saved = False

    if "user_id" in session:
        user_id = session["user_id"]
        cursor.execute("SELECT * FROM quiz_likes WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
        if cursor.fetchone(): is_liked = True
        cursor.execute("SELECT * FROM quiz_saves WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
        if cursor.fetchone(): is_saved = True

    cursor.close()
    return render_template("quiz_detail.html", quiz=quiz, q_count=question_count, is_liked=is_liked, is_saved=is_saved)

@app.route("/save_quiz/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def save_quiz(quiz_id):
    cursor = mysql.connection.cursor()
    user_id = session["user_id"]
    cursor.execute("SELECT id FROM quiz_saves WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM quiz_saves WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
        saved = False
    else:
        cursor.execute("INSERT INTO quiz_saves (user_id, quiz_id) VALUES (%s, %s)", (user_id, quiz_id))
        saved = True
    mysql.connection.commit()
    cursor.close()
    if wants_json():
        return jsonify(ok=True, saved=saved)
    return redirect(request.referrer or url_for("quiz_detail", quiz_id=quiz_id))

@app.route("/user/<username>")
def user_profile(username):
    cursor = mysql.connection.cursor()
    sorgu_user = """
        SELECT users.*, COALESCE(SUM(quizzes.views), 0) as total_views,
        COALESCE(SUM(quizzes.likes), 0) as total_likes
        FROM users LEFT JOIN quizzes ON users.id = quizzes.user_id
        WHERE users.username = %s GROUP BY users.id
    """
    cursor.execute(sorgu_user, (username,))
    user = cursor.fetchone()

    if not user:
        flash("Böyle bir kullanıcı bulunamadı.", "danger")
        return redirect(url_for('index'))

    # DÜZELTME: Profilde sadece yayındaki testler görünsün
    cursor.execute("SELECT * FROM quizzes WHERE user_id = %s AND is_published = 1 ORDER BY created_at DESC", (user['id'],))
    quizzes = cursor.fetchall()
    cursor.close()
    return render_template("public_profile.html", user=user, quizzes=quizzes)

# === ADMIN PANEL ===

def detect_device():
    ua = (request.user_agent.string or "").lower()
    plat = (request.user_agent.platform or "").lower()
    if plat in ("android", "iphone", "ipad") or "mobi" in ua or "iphone" in ua or "android" in ua:
        return "mobile"
    return "desktop"

@app.before_request
def log_visit_device():
    if request.path.startswith("/static"):
        return
    if not session.get("_schema_ok"):
        try:
            cursor = mysql.connection.cursor()
            ensure_quiz_draft_column(cursor)
            ensure_auth_columns(cursor)
            mysql.connection.commit()
            cursor.close()
            session["_schema_ok"] = True
        except Exception:
            pass
    if not session.get("_purged"):
        purge_abandoned_quizzes()
        purge_unverified_users()
        session["_purged"] = True
    if session.get("_dev_logged"):
        return
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device VARCHAR(16) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("INSERT INTO visit_devices (device) VALUES (%s)", (detect_device(),))
        mysql.connection.commit()
        cursor.close()
        session["_dev_logged"] = True
    except Exception:
        pass

@app.route("/admin")
@admin_required
def admin_panel():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM quizzes WHERE is_published = 1")
    quiz_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM questions")
    question_count = cursor.fetchone()['count']
    cursor.execute("SELECT * FROM quizzes WHERE is_published = 1 ORDER BY created_at DESC LIMIT 5")
    latest_quizzes = cursor.fetchall()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 20")
    users = cursor.fetchall()
    mobile_all = desktop_all = mobile_today = desktop_today = 0
    try:
        cursor.execute("SELECT device, COUNT(*) as n FROM visit_devices GROUP BY device")
        for row in cursor.fetchall() or []:
            if row["device"] == "mobile":
                mobile_all = row["n"]
            else:
                desktop_all = row["n"]
        cursor.execute("SELECT device, COUNT(*) as n FROM visit_devices WHERE DATE(created_at) = CURDATE() GROUP BY device")
        for row in cursor.fetchall() or []:
            if row["device"] == "mobile":
                mobile_today = row["n"]
            else:
                desktop_today = row["n"]
    except Exception:
        pass
    cursor.close()
    return render_template(
        "admin.html",
        user_count=user_count,
        quiz_count=quiz_count,
        question_count=question_count,
        latest_quizzes=latest_quizzes,
        users=users,
        mobile_all=mobile_all,
        desktop_all=desktop_all,
        mobile_today=mobile_today,
        desktop_today=desktop_today,
    )

@app.route("/admin/delete_quiz/<string:quiz_id>", methods=["POST"])
@admin_required
def delete_quiz_admin(quiz_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    mysql.connection.commit()
    cursor.close()
    flash("Quiz silindi (Admin).", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_user/<string:user_id>", methods=["POST"])
@admin_required
def delete_user_admin(user_id):
    if int(user_id) == int(session["user_id"]):
        flash("Kendini silemezsin!", "danger")
        return redirect(url_for("admin_panel"))
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash("Kullanıcı silindi.", "warning")
    return redirect(url_for("admin_panel"))

# === HATALAR VE BAŞLATMA ===

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# --- SİLME İŞLEMİ ---
@app.route('/delete_quiz/<string:id>', methods=['POST'])
@login_required
def delete_quiz(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT user_id FROM quizzes WHERE quiz_id = %s", [id])
    quiz = cursor.fetchone()

    if quiz:
        if int(quiz['user_id']) == int(session['user_id']):
            cursor.execute("DELETE FROM questions WHERE quiz_id = %s", [id])
            cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", [id])
            try:
                cursor.execute("DELETE FROM quiz_likes WHERE quiz_id = %s", [id])
                cursor.execute("DELETE FROM quiz_saves WHERE quiz_id = %s", [id])
                cursor.execute("DELETE FROM quiz_results WHERE quiz_id = %s", [id])
            except: pass
            mysql.connection.commit()
            flash("Test ve tüm verileri başarıyla silindi.", "success")
        else:
            flash("Bu testi silme yetkiniz yok!", "danger")
    else:
        flash("Böyle bir test bulunamadı.", "danger")

    cursor.close()
    return redirect(url_for('paylastiklarim'))

# --- QUIZ DÜZENLEME (EDIT) ---
@app.route('/edit_quiz/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", [id])
    quiz = cursor.fetchone()

    if not quiz or int(quiz['user_id']) != int(session['user_id']):
        flash("Bu işlemi yapmaya yetkiniz yok!", "danger")
        return redirect(url_for('index'))

    form = QuizCreateForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data
        category = form.category.data

        file = request.files.get('cover_image')
        new_image_filename = quiz['cover_image_url']

        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER_QUIZ_COVERS'], unique_filename)
            save_optimized_image(file, save_path, target_size=(1400, 900), quality=90)
            new_image_filename = unique_filename

        sorgu = "UPDATE quizzes SET title=%s, description=%s, category=%s, cover_image_url=%s WHERE quiz_id=%s"
        cursor.execute(sorgu, (title, description, category, new_image_filename, id))
        mysql.connection.commit()

        flash("Quiz başarıyla güncellendi!", "success")
        return redirect(url_for('quiz_detail', quiz_id=id))

    form.title.data = quiz['title']
    form.description.data = quiz['description']
    form.category.data = quiz['category']
    cursor.close()
    return render_template('edit_quiz.html', form=form, quiz=quiz)

@app.route("/delete_user/<string:id>", methods=["POST"])
def delete_user(id):
    if session.get('username') != 'admin_kullanici_adin':
        flash("Bu işlem için yetkiniz yok!", "danger")
        return redirect(url_for("index"))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM quizzes WHERE user_id = %s", (id,))
    cursor.execute("DELETE FROM users WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Kullanıcı ve tüm verileri başarıyla silindi.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/hard_delete_user/<string:user_id>", methods=["POST"])
def hard_delete_user(user_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        flash("Yetkisiz erişim!", "danger")
        return redirect(url_for("index"))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM questions WHERE quiz_id IN (SELECT quiz_id FROM quizzes WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM quizzes WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        flash("Kullanıcı veritabanından tamamen kazındı! Mail boşa çıktı.", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Silme sırasında hata oluştu: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for("admin_panel"))

@app.route('/login/google')
def google_login():
    redirect_uri = "http://sorsana.pythonanywhere.com/login/google/callback"
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_authorize():
    token = google.authorize_access_token()
    resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
    user_info = resp.json()

    google_id = user_info.get('sub') or user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name')

    if not google_id or not email:
        flash("Google'dan kullanıcı bilgileri alınamadı.", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    ensure_auth_columns(cursor)
    email = (email or "").strip().lower()
    email_norm = normalize_email(email)
    user = None
    try:
        cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
        user = cursor.fetchone()
    except Exception:
        user = None

    if not user:
        try:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR IFNULL(email_norm, '') = %s",
                (email, email_norm),
            )
        except Exception:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            try:
                cursor.execute(
                    "UPDATE users SET google_id = %s, is_verified = 1, email_norm = %s WHERE id = %s",
                    (google_id, email_norm, user["id"]),
                )
            except Exception:
                cursor.execute("UPDATE users SET google_id = %s, is_verified = 1 WHERE email = %s", (google_id, email))
            mysql.connection.commit()
        else:
            username = re.sub(r"[^a-z0-9_]", "", email_norm.split("@")[0])[:24] or ("u" + str(uuid.uuid4().hex[:8]))
            fake_password = sha256_crypt.encrypt(str(uuid.uuid4()))
            try:
                cursor.execute(
                    """
                    INSERT INTO users(name, email, email_norm, google_id, username, password, is_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                    """,
                    (name, email, email_norm, google_id, username, fake_password),
                )
            except Exception:
                cursor.execute(
                    "INSERT INTO users(name, email, google_id, username, password, is_verified) VALUES(%s, %s, %s, %s, %s, 1)",
                    (name, email, google_id, username, fake_password),
                )
            mysql.connection.commit()
            cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
            user = cursor.fetchone()

    session["logged_in"] = True
    session["username"] = user["username"]
    session["user_id"] = user["id"]
    session["id"] = user["id"]
    session["profile_pic_url"] = user.get("profile_pic_url") or "default.png"
    session["is_admin"] = (user.get("is_admin") == 1)
    cursor.close()
    flash(f"Hoş geldin {name}!", "success")
    return redirect(url_for("index"))

@app.route("/quiz_clear_session/<string:quiz_id>")
def quiz_clear_session(quiz_id):
    session.pop(f'tournament_list_{quiz_id}', None)
    session.pop(f'winners_list_{quiz_id}', None)
    session.pop(f'tournament_round_{quiz_id}', None)
    session.modified = True
    flash("Turnuva oturumu sıfırlandı.", "success")
    return redirect(url_for("quiz_view", quiz_id=quiz_id))

@app.route("/quiz/<string:quiz_id>/blind")
def blind_rank(quiz_id):
    quiz, payload, err = load_photo_pool(quiz_id, min_items=MIN_BLIND_ITEMS, mode_label="Kör sıralama")
    if err:
        flash(err[0], err[1])
        return redirect(url_for(err[2], **err[3]))
    return render_template("blind_rank.html", quiz=quiz, items_json=payload)

@app.route("/quiz/<string:quiz_id>/tier")
def tier_list(quiz_id):
    quiz, payload, err = load_photo_pool(quiz_id, min_items=MIN_PLAY_ITEMS, mode_label="Tier list")
    if err:
        flash(err[0], err[1])
        return redirect(url_for(err[2], **err[3]))
    return render_template("tier_list.html", quiz=quiz, items_json=payload)

@app.route("/delete_pool_item/<string:item_id>", methods=["POST"])
@login_required
def delete_pool_item(item_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT questions.*, quizzes.user_id AS owner_id, quizzes.quiz_id AS owner_quiz
        FROM questions
        JOIN quizzes ON quizzes.quiz_id = questions.quiz_id
        WHERE questions.question_id = %s
        """,
        (item_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        flash("Öğe bulunamadı.", "danger")
        return redirect(url_for("paylastiklarim"))
    if int(row["owner_id"]) != int(session["user_id"]) and not session.get("is_admin"):
        cursor.close()
        flash("Bu öğeyi silme yetkin yok.", "danger")
        return redirect(url_for("index"))

    folder_path = app.config["UPLOAD_FOLDER_QUIZ_IMAGES"]
    for key in (
        "image_url",
        "question_image_url",
        "option_a_image_url",
        "option_b_image_url",
        "option_c_image_url",
        "option_d_image_url",
    ):
        resim_adi = row.get(key)
        if not resim_adi:
            continue
        try:
            full_path = os.path.join(folder_path, resim_adi)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass

    cursor.execute("DELETE FROM questions WHERE question_id = %s", (item_id,))
    mysql.connection.commit()
    quiz_id = row["owner_quiz"]
    cursor.close()
    flash("Soru ve varsa resimleri başarıyla silindi.", "success")
    return redirect(url_for("add_questions", quiz_id=quiz_id))

if __name__ == "__main__":
    app.run(debug=False, port=5001)