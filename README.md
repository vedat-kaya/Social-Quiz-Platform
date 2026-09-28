# SorSana

Topluluk tabanlı quiz ve görsel oyun platformu. Kullanıcılar klasik test, fotoğraf turnuvası, kör sıralama ve tier list oluşturur, oynar ve paylaşır.

**Canlı site:** [sorsana.pythonanywhere.com](https://sorsana.pythonanywhere.com)

## Özellikler

- Klasik test (sonuç kartı) ve fotoğraf havuzu
- Aynı havuzdan üç oyun: VS turnuva, kör sıralama (1–10), düzenlenebilir tier list
- Kayıt, e-posta doğrulama, Google ile giriş, şifre sıfırlama
- Taslak / yayın ayrımı — yayınlanmamış içerik yalnızca sahibine açık
- Beğeni, kaydetme, liderlik tablosu, yönetici paneli
- Mobil ve masaüstü uyumlu koyu arayüz

## Teknolojiler

Python 3 · Flask · MySQL · Jinja2 · JavaScript · Bootstrap 4 · Pillow · Flask-Mail · Authlib (Google OAuth)

Dağıtım: [PythonAnywhere](https://www.pythonanywhere.com)

## Kurulum

```bash
git clone https://github.com/vedat-kaya/Social-Quiz-Platform.git
cd Social-Quiz-Platform
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Proje köküne `.env` dosyası oluştur (GitHub’a yüklenmez):

```env
SECRET_KEY=
MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DB=
MYSQL_PORT=3306
MAIL_USERNAME=
MAIL_PASSWORD=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Veritabanı şemasını `veritabani.sql` ile oluştur, ardından:

```bash
python quiz.py
```

## Güvenlik notları

- `.env` `.gitignore` içindedir; sırlar repoya girmez.
- Kayıtta CSRF, honeypot, IP limiti ve Gmail adres normalizasyonu vardır.
- Doğrulanmayan hesaplar 24 saat sonra temizlenir.
- Şifre sıfırlama bağlantısı 1 saat geçerlidir.

## Lisans

Özel proje — kaynak [GitHub](https://github.com/vedat-kaya/Social-Quiz-Platform) üzerinde. Tüm hakları saklıdır.
