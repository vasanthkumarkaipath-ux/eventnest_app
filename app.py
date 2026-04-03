from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('events.db')

    # Users
    conn.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    # Teams
    conn.execute('''CREATE TABLE IF NOT EXISTS teams(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )''')

    # Participants (FIXED TABLE)
    conn.execute('''CREATE TABLE IF NOT EXISTS registrations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )''')

    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('events.db')
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                     (username,password))
        conn.commit()
        conn.close()

        return redirect('/login/user')

    return render_template('signup.html')

# ---------- LOGIN ----------
@app.route('/login/<role>', methods=['GET','POST'])
def login(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('events.db')
        user = conn.execute("SELECT * FROM users WHERE username=?",
                            (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = username

            if role == "admin" and username == "admin":
                return redirect('/admin_dashboard')
            elif role == "user":
                return redirect('/dashboard')

        return "Invalid Login ❌"

    return render_template('login.html', role=role)

# ---------- USER DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login/user')

    conn = sqlite3.connect('events.db')
    teams = conn.execute("SELECT * FROM teams").fetchall()
    participants = conn.execute("SELECT * FROM registrations").fetchall()
    conn.close()

    return render_template('dashboard.html',
                           teams=teams,
                           participants=participants)

# ---------- REGISTER NAME ----------
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']

    conn = sqlite3.connect('events.db')
    conn.execute("INSERT INTO registrations (name) VALUES (?)",(name,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------- ADMIN DASHBOARD ----------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session['user']!='admin':
        return redirect('/login/admin')

    conn = sqlite3.connect('events.db')
    users = conn.execute("SELECT * FROM users").fetchall()
    teams = conn.execute("SELECT * FROM teams").fetchall()
    participants = conn.execute("SELECT * FROM registrations").fetchall()
    conn.close()

    return render_template('admin_dashboard.html',
                           users=users,
                           teams=teams,
                           participants=participants)

# ---------- ADD TEAM ----------
@app.route('/add_team', methods=['POST'])
def add_team():
    team = request.form['team']

    conn = sqlite3.connect('events.db')
    conn.execute("INSERT INTO teams (name) VALUES (?)",(team,))
    conn.commit()
    conn.close()

    return redirect('/admin_dashboard')

# ---------- DELETE TEAM ----------
@app.route('/delete_team/<int:id>')
def delete_team(id):
    conn = sqlite3.connect('events.db')
    conn.execute("DELETE FROM teams WHERE id=?",(id,))
    conn.commit()
    conn.close()

    return redirect('/admin_dashboard')

# ---------- EDIT TEAM ----------
@app.route('/edit_team/<int:id>', methods=['GET','POST'])
def edit_team(id):
    conn = sqlite3.connect('events.db')

    if request.method == 'POST':
        name = request.form['name']
        conn.execute("UPDATE teams SET name=? WHERE id=?",(name,id))
        conn.commit()
        conn.close()
        return redirect('/admin_dashboard')

    team = conn.execute("SELECT * FROM teams WHERE id=?",(id,)).fetchone()
    conn.close()

    return render_template('edit_team.html', team=team)

# ---------- DELETE PARTICIPANT ----------
@app.route('/delete_participant/<int:id>')
def delete_participant(id):
    conn = sqlite3.connect('events.db')
    conn.execute("DELETE FROM registrations WHERE id=?",(id,))
    conn.commit()
    conn.close()

    return redirect('/admin_dashboard')

# ---------- QR ----------
@app.route('/qr')
def qr():
    img = qrcode.make("http://127.0.0.1:5000/")
    img.save("static/qr.png")
    return render_template('qr.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)