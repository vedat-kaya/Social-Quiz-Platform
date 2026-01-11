# Social Quiz Platform (SorSana)

### 🔴 [Click Here for Live Demo / Canlı Demo](https://sorsana.pythonanywhere.com)

A dynamic and interactive social quiz platform where users can create, share, and solve quizzes. Built with **Python Flask** and **MySQL**.

![Project Status](https://img.shields.io/badge/status-live-success.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange.svg)

## 🚀 Features

* **User System:** Register, Login (with Email Verification), and Google OAuth integration.
* **Quiz Engine:**
    * **Classic Mode:** Multiple choice questions with image support.
    * **Tournament Mode:** Image-based elimination voting system (FaceMash style).
* **Social Interactions:** Like quizzes, save to collection, view leaderboards, and user profiles.
* **Admin Panel:** Full control to manage users and quizzes.
* **Responsive Design:** Works smoothly on desktop and mobile.

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** MySQL (Production), SQLite (Dev)
* **Frontend:** HTML5, CSS3, Bootstrap, Jinja2
* **Security:** Password Hashing (SHA256), CSRF Protection, OAuth 2.0

## ⚙️ Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/vedat-kaya/Social-Quiz-Platform.git](https://github.com/vedat-kaya/Social-Quiz-Platform.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure Environment Variables:
    * Rename `.env.example` to `.env`.
    * Fill in your MySQL and Mail credentials.
4.  Import Database:
    * Import `veritabani.sql` to your MySQL server.
5.  Run the application:
    ```bash
    python quiz.py
    ```

---
**Developed by Vedat Kaya**
