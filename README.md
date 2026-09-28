<p align="center">
  <img src="static/img/slogo.png" width="88" alt="SorSana">
</p>

<h1 align="center">SorSana</h1>

<p align="center">
  <strong>Bilgini yarıştır.</strong><br>
  Topluluk quizleri, fotoğraf turnuvası, kör sıralama ve tier list.
</p>

<p align="center">
  <a href="https://sorsana.pythonanywhere.com"><strong>Canlı site</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/vedat-kaya/Social-Quiz-Platform">Kaynak</a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3-000000?style=flat-square&logo=flask&logoColor=white">
  <img alt="MySQL" src="https://img.shields.io/badge/MySQL-8-4479A1?style=flat-square&logo=mysql&logoColor=white">
  <img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=flat-square&logo=javascript&logoColor=black">
</p>

---

Tek fotoğraf havuzundan üç oyun. Taslak yayınlanmadan vitrine düşmez. Kayıt, doğrulama ve spam önlemleri üretim ortamında çalışır.

## Oyunlar

| Mod | Ne yapar |
| --- | --- |
| Klasik test | Soru, şık, sonuç kartı |
| Turnuva | İki görsel, bir kazanan |
| Kör sıralama | Ortada fotoğraf, solda 1–10 |
| Tier list | Sürükle-bırak katmanlar |

Beğeni, kaydetme, zirve tablosu ve yönetici paneli dahildir.

## Yığın

`Flask` · `MySQL` · `Jinja2` · `JavaScript` · `Bootstrap 4` · `Pillow` · `Flask-Mail` · `Authlib`

Sunucu: [PythonAnywhere](https://www.pythonanywhere.com)

## Kurulum

```bash
git clone https://github.com/vedat-kaya/Social-Quiz-Platform.git
cd Social-Quiz-Platform
python -m venv venv
pip install -r requirements.txt
```

Kök dizine `.env` koy (repoya girmez):

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

Şema: `veritabani.sql`

```bash
python quiz.py
```

## Güvenlik

CSRF, honeypot, IP limiti, Gmail normalizasyonu, 24 saat doğrulanmayan hesap temizliği, 1 saatlik şifre sıfırlama token’ı. `.env` `.gitignore`’dadır.

## Lisans

Özel proje. Tüm hakları saklıdır.
