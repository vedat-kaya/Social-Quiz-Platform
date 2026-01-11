import os
import uuid
import random
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageOps
from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, FileField, SelectField
from wtforms.validators import InputRequired, Optional
from passlib.hash import sha256_crypt
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
load_dotenv()
# === UYGULAMA AYARLARI (CONFIG) ===
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# MySQL Bağlantı Ayarları
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

# Mail Ayarları
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# Dosya Yükleme Ayarları
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
base_dir = app.root_path

UPLOAD_FOLDER = os.path.join(base_dir, 'static/uploads/quiz_images')
UPLOAD_FOLDER_PROFILE = os.path.join(base_dir, 'static/uploads/profile_pics')
UPLOAD_FOLDER_QUIZ_COVERS = os.path.join(base_dir, 'static/uploads/quiz_covers')

# Dosya yollarını sunucuya göre ayarlıyoruz
app.config['UPLOAD_FOLDER_QUIZ_COVERS'] = '/home/sorsana/static/uploads/quiz_covers'
app.config['UPLOAD_FOLDER_PROFILE_PICS'] = '/home/sorsana/static/uploads/profile_pics'
app.config['UPLOAD_FOLDER_QUIZ_IMAGES'] = '/home/sorsana/static/uploads/quiz_images'

# Klasör Kontrolü
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

def save_optimized_image(file_storage, save_path, target_size=(600, 600)):
    """Resimleri optimize ederek ve kırparak kaydeder."""
    try:
        img = Image.open(file_storage)
        img = img.convert("RGB")

        # 1. Arka Plan (Bulanık Efekt)
        background = ImageOps.fit(img, target_size, method=Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=20))

        # 2. Ön Plan (Orantılı)
        img.thumbnail(target_size, Image.LANCZOS)

        # 3. Birleştirme
        bg_w, bg_h = target_size
        img_w, img_h = img.size
        offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
        background.paste(img, offset)

        background.save(save_path, format='JPEG', optimize=True, quality=90)

    except Exception as e:
        print(f"Resim işleme hatası: {e}")
        file_storage.seek(0)
        file_storage.save(save_path)

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
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
    name = StringField("İsim Soyisim", validators=[validators.Length(min=4, max=20), validators.DataRequired()])
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min=5, max=30)])
    email = StringField("E Mail", validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz...")])
    password = PasswordField("Parola:", validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyiniz."),
        validators.EqualTo(fieldname="confirm", message="Parolanız Uyuşmuyor.")
    ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("", render_kw={"placeholder": "Kullanıcı Adı veya Email "})
    password = PasswordField("", render_kw={"placeholder": "Şifre"})

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
                                    ('turnuva', 'Turnuva (VS, Fotoğraflı Eleme)')],
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

    # Sadece yayındaki (is_published=1) quizleri çekiyoruz
    sorgu = """
        SELECT q.*, u.name as author_name
        FROM quizzes q
        JOIN users u ON q.user_id = u.id
        WHERE q.is_published = 1
        ORDER BY q.created_at DESC
    """
    result = cursor.execute(sorgu)
    all_quizzes = cursor.fetchall() if result > 0 else []
    cursor.close()

    # --- VERİLERİ GRUPLAMA MANTIĞI ---
    grouped_quizzes = {
        'Trendler': [],       # En çok izlenenleri buraya koyabiliriz (şimdilik karışık)
        'En Yeniler': [],     # Tarihe göre en yeniler
        'Teknoloji': [],
        'Eğlence': [],
        'Spor': [],
        'Film & Dizi': [],
        'Oyun': [],
        'Genel Kültür': []
    }

    # 1. En Yeniler (Hepsinden ilk 10 tanesi)
    grouped_quizzes['En Yeniler'] = all_quizzes[:10]

    # 2. Trendler (İzlenme sayısına göre sırala - Python ile yapıyoruz)
    # Listeyi views'e göre tersten sırala
    sorted_by_views = sorted(all_quizzes, key=lambda x: x['views'], reverse=True)
    grouped_quizzes['Trendler'] = sorted_by_views[:10]

    # 3. Kategoriye Göre Dağıt
    for quiz in all_quizzes:
        cat = quiz['category']
        # Kategori ismini veritabanındaki ile eşleştirelim
        if cat == 'Teknoloji': grouped_quizzes['Teknoloji'].append(quiz)
        elif cat == 'Eğlence': grouped_quizzes['Eğlence'].append(quiz)
        elif cat == 'Spor': grouped_quizzes['Spor'].append(quiz)
        elif cat == 'Film': grouped_quizzes['Film & Dizi'].append(quiz)
        elif cat == 'Oyun': grouped_quizzes['Oyun'].append(quiz)
        elif cat == 'Genel': grouped_quizzes['Genel Kültür'].append(quiz)

    # Boş kategorileri temizle (Sitede boş başlık görünmesin)
    final_groups = {k: v for k, v in grouped_quizzes.items() if v}

    return render_template("index.html", grouped_quizzes=final_groups)


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
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu_kontrol = "SELECT * FROM users WHERE email = %s OR username = %s"
        result = cursor.execute(sorgu_kontrol, (email, username))

        if result > 0:
            flash("Bu e-posta adresi veya kullanıcı adı zaten alınmış!", "danger")
            cursor.close()
            return redirect(url_for("register"))
        else:
            default_profile_pic = "default.png"
            sorgu_kayit = "INSERT INTO users(name,email,username,password,profile_pic_url, is_verified) VALUES(%s,%s,%s,%s,%s, 0)"
            cursor.execute(sorgu_kayit, (name, email, username, password, default_profile_pic))
            mysql.connection.commit()
            cursor.close()

            # --- MAİL GÖNDERME KISMI ---
            token = s.dumps(email, salt='email-confirm')
            msg = Message('SorSana Hesap Doğrulama', sender='sorsana.iletisim@gmail.com', recipients=[email])

            link = url_for('confirm_email', token=token, _external=True)
            msg.body = f'Merhaba {name}! SorSana ailesine hoş geldin. Hesabını aktifleştirmek için lütfen şu linke tıkla: {link}'

            try:
                mail.send(msg)
                return render_template("verify_email_sent.html", email=email)
            except Exception as e:
                flash(f"Mail gönderilemedi, ama kaydınız alındı. Hata: {str(e)}", "danger")
            return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username_or_email = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s OR email = %s"
        result = cursor.execute(sorgu, (username_or_email, username_or_email))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                if data['is_verified'] == 0:
                    flash("Lütfen önce mail adresine gelen linke tıklayarak hesabını doğrula!", "warning")
                    return redirect(url_for("login"))
                flash("Başarıyla giriş Yaptınız", "success")
                session["logged_in"] = True
                session["username"] = data["username"]
                session["user_id"] = data["id"]
                session["profile_pic_url"] = data["profile_pic_url"]
                session["is_admin"] = (data["is_admin"] == 1)
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz", "danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı adı veya e-posta bulunamadı.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("Doğrulama linki geçersiz veya süresi dolmuş!", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET is_verified = 1 WHERE email = %s", [email])
    mysql.connection.commit()
    cursor.close()

    flash("Hesabın başarıyla doğrulandı! Artık giriş yapabilirsin.", "success")
    return redirect(url_for('login'))

# === NAVBAR İÇİN OTOMATİK VERİ ÇEKİCİ (CONTEXT PROCESSOR) ===
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
    cursor.execute("SELECT * FROM quizzes WHERE is_published = 1 ORDER BY views DESC LIMIT 50")
    quizzes = cursor.fetchall()
    cursor.close()
    return render_template("index.html", quizzes=quizzes)

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
            save_optimized_image(file, file_path)
            cover_image_filename = unique_filename

        cursor = mysql.connection.cursor()

        # DÜZELTİLEN SQL SORGUSU (Tam Eşleşme):
        sorgu = """
            INSERT INTO quizzes (user_id, title, description, category, quiz_type, cover_image_url, is_published)
            VALUES (%s, %s, %s, %s, %s, %s, 0)
        """
        # 6 değişken gönderiyoruz, 6 tane %s var (is_published 0 olarak hardcode edildi)
        cursor.execute(sorgu, (user_id, title, description, category, quiz_type, cover_image_filename))

        mysql.connection.commit()

        # Otomatik oluşan ID'yi al
        quiz_id = cursor.lastrowid
        cursor.close()

        if not quiz_id or quiz_id == 0:
            flash("Quiz oluşturuldu ama ID alınamadı. Paylaştıklarım sayfasından düzenleyin.", "warning")
            return redirect(url_for("paylastiklarim"))

        flash("Quiz başarıyla oluşturuldu! Şimdi soruları ekleyebilirsiniz.", "success")
        return redirect(url_for("add_questions", quiz_id=str(quiz_id)))

    return render_template("create_quiz.html", form=form)

@app.route("/add_questions/<string:quiz_id>", methods=["GET", "POST"])
@login_required
def add_questions(quiz_id):
    cursor = mysql.connection.cursor()

    # Quiz var mı kontrol et
    sorgu_tip = "SELECT quiz_type, title FROM quizzes WHERE quiz_id = %s"
    result = cursor.execute(sorgu_tip, (quiz_id,))

    if result == 0:
        flash("Quiz bulunamadı.", "danger")
        cursor.close()
        return redirect(url_for("index"))

    quiz_data = cursor.fetchone()
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
                    save_optimized_image(file, save_path)
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
            save_optimized_image(file, file_path)

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
        if soru_sayisi < 1:
            flash(f"HATA: Boş test yayımlanamaz! En az 1 soru eklemelisiniz.", "danger")
            hata_var = True

    # --- KURAL 2: TURNUVA ---
    elif quiz_type == 'turnuva':
        if soru_sayisi < 2:
            flash(f"HATA: Turnuva başlatmak için en az 2 seçenek eklemelisiniz.", "danger")
            hata_var = True

    # Eğer hata varsa, soru ekleme sayfasına geri postala
    if hata_var:
        cursor.close()
        return redirect(url_for("add_questions", quiz_id=quiz_id))

    # 3. HER ŞEY TAMAMSA YAYIMLA!
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
    quizzes = cursor.fetchall() if result > 0 else None
    cursor.close()
    return render_template("paylastiklarim.html", quizzes=quizzes)

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
                winners_list.append(winner_data)
                session[session_winners_key] = winners_list

            current_list = current_list[2:]
            session[session_list_key] = current_list
            session.modified = True
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
                return render_template("tournament_winner.html", quiz=quiz_data, winner=winner)
            else:
                try:
                    cursor.execute("UPDATE quizzes SET views = views + 1 WHERE quiz_id = %s", (quiz_id,))
                    mysql.connection.commit()
                except: pass

                sorgu_questions = "SELECT * FROM questions WHERE quiz_id = %s"
                cursor.execute(sorgu_questions, (quiz_id,))
                questions_data = list(cursor.fetchall())

                if len(questions_data) < 2:
                    flash("Yetersiz seçenek. Turnuva için en az 2 resim lazım.", "danger")
                    return redirect(url_for("index"))

                random.shuffle(questions_data)
                session[session_list_key] = questions_data
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

        return render_template("tournament_view.html", quiz=quiz_data, item1=item1, item2=item2, round=current_round, remaining=len(current_list))
    else:
        flash("Bilinmeyen quiz tipi.", "danger")
        cursor.close()
        return redirect(url_for("index"))

@app.route("/like_quiz/<string:quiz_id>")
@login_required
def like_quiz(quiz_id):
    user_id = session["user_id"]
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO quiz_likes (user_id, quiz_id) VALUES (%s, %s)", (user_id, quiz_id))
        cursor.execute("UPDATE quizzes SET likes = likes + 1 WHERE quiz_id = %s", (quiz_id,))
        mysql.connection.commit()
        flash("Quiz'i beğendin!", "success")
    except Exception:
        mysql.connection.rollback()
        flash("Bu quiz'i zaten beğenmiştin.", "danger")
    finally:
        cursor.close()
    return redirect(request.referrer or url_for("index"))

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

@app.route("/save_quiz/<string:quiz_id>")
@login_required
def save_quiz(quiz_id):
    cursor = mysql.connection.cursor()
    user_id = session["user_id"]

    cursor.execute("SELECT * FROM quiz_saves WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM quiz_saves WHERE user_id=%s AND quiz_id=%s", (user_id, quiz_id))
        mysql.connection.commit()
        flash("Quiz koleksiyonundan çıkarıldı.", "warning")
    else:
        cursor.execute("INSERT INTO quiz_saves (user_id, quiz_id) VALUES (%s, %s)", (user_id, quiz_id))
        mysql.connection.commit()
        flash("Quiz koleksiyonuna kaydedildi.", "success")

    cursor.close()
    return redirect(request.referrer or url_for('index'))

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

@app.route("/admin")
@admin_required
def admin_panel():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM quizzes")
    quiz_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM questions")
    question_count = cursor.fetchone()['count']
    cursor.execute("SELECT * FROM quizzes ORDER BY created_at DESC LIMIT 5")
    latest_quizzes = cursor.fetchall()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 20")
    users = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_count=user_count, quiz_count=quiz_count, question_count=question_count, latest_quizzes=latest_quizzes, users=users)

@app.route("/admin/delete_quiz/<string:quiz_id>")
@admin_required
def delete_quiz_admin(quiz_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    mysql.connection.commit()
    cursor.close()
    flash("Quiz silindi (Admin).", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_user/<string:user_id>")
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
            save_optimized_image(file, save_path)
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
    cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE users SET google_id = %s, is_verified = 1 WHERE email = %s", (google_id, email))
            mysql.connection.commit()
        else:
            username = email.split('@')[0]
            fake_password = sha256_crypt.encrypt(str(uuid.uuid4()))
            cursor.execute("INSERT INTO users(name, email, google_id, username, password, is_verified) VALUES(%s, %s, %s, %s, %s, 1)",
                           (name, email, google_id, username, fake_password))
            mysql.connection.commit()
            cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
            user = cursor.fetchone()

    session["logged_in"] = True
    session["username"] = user["username"]
    session["user_id"] = user["id"]
    session["id"] = user["id"]
    session["profile_pic_url"] = user.get("profile_pic_url", "default.png")
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

@app.route("/delete_pool_item/<string:item_id>", methods=["POST"])
@login_required
def delete_pool_item(item_id):
    cursor = mysql.connection.cursor()
    sorgu_resim = """
        SELECT question_image_url, option_a_image_url, option_b_image_url, option_c_image_url, option_d_image_url
        FROM questions
        WHERE question_id = %s
    """
    cursor.execute(sorgu_resim, (item_id,))
    resimler = cursor.fetchone()

    if resimler:
        folder_path = app.config['UPLOAD_FOLDER_QUIZ_IMAGES']
        for resim_adi in resimler.values():
            if resim_adi:
                try:
                    full_path = os.path.join(folder_path, resim_adi)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"Silindi: {resim_adi}")
                except Exception as e:
                    print(f"Dosya silinirken hata: {e}")

    sorgu_sil = "DELETE FROM questions WHERE question_id = %s"
    cursor.execute(sorgu_sil, (item_id,))
    mysql.connection.commit()
    cursor.close()

    flash("Soru ve varsa resimleri başarıyla silindi.", "success")
    return redirect(request.referrer)

if __name__ == "__main__":
    app.run(debug=False, port=5001)