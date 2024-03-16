from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialisiert die Flask-Anwendung
app = Flask(__name__, template_folder="templates")
# Konfiguriert die Datenbank; verwendet SQLite für die lokale Entwicklung
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meine_lokale_datenbank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Setzt einen geheimen Schlüssel für die Sitzungsverschlüsselung
app.secret_key = 'ein_sehr_geheimer_schlüssel'
# Initialisiert SQLAlchemy mit der Flask-Anwendung
db = SQLAlchemy(app)

# Datenmodell für Benutzer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Eindeutige ID für jeden Benutzer
    username = db.Column(db.String(80), unique=True, nullable=False)  # Benutzername
    password_hash = db.Column(db.String(128))  # Speichert Passwort-Hash
    todos = db.relationship('Todo', backref='user', lazy=True)  # Verknüpfung zu den Todo-Items des Benutzers

    # Setzt das Passwort (als Hash)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Überprüft das Passwort
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Datenmodell für Todo-Items
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Eindeutige ID für jedes Todo-Item
    task = db.Column(db.String(150))  # Beschreibung der Aufgabe
    done = db.Column(db.Boolean, default=False)  # Status des Todo-Items (erledigt oder nicht)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Verknüpft Todo-Item mit einem Benutzer

# Startseite; zeigt Todo-Liste an, falls Benutzer eingeloggt ist; sonst Umleitung zur Login-Seite
@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        todos = Todo.query.filter_by(user_id=user.id).all()
        return render_template('index.html', todos=todos)
    return redirect(url_for('login'))

# Login-Seite; behandelt die Anmelde-Logik
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Falscher Benutzername oder Passwort.')
    return render_template('login.html')

# Registrierungsseite; behandelt die Registrierungs-Logik
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        flash('Benutzername bereits vergeben.')
    return render_template('register.html')

# Logout-Route; entfernt den Benutzer aus der Sitzung
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Route zum Bearbeiten eines Todo-Items; nur für den Besitzer des Todo-Items
@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_id != session['user_id']:
        flash('Nicht berechtigt, dieses Todo zu bearbeiten.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        todo.task = request.form['todo']
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', todo=todo)

# Startet die Flask-Anwendung
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
