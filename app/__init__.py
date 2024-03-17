from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os

# Flask-Anwendung initialisieren
app = Flask(__name__, template_folder="templates")

# Datenbankkonfiguration aus Umgebungsvariablen holen
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
hostname = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{username}:{password}@{hostname}/{database}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret Key - Wichtig für die Verwendung von Sessions in Flask
app.secret_key = os.getenv("SECRET_KEY", "ein_sehr_geheimer_schlüssel")

# SQLAlchemy und Flask-Migrate initialisieren
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Datenmodell für Benutzer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    todos = db.relationship('Todo', backref='user', lazy=True)

    # Passwort setzen
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Passwort überprüfen
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Datenmodell für Todo-Items
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150))
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Startseite
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        todos = user.todos
        # todo = Todo.query.filter_by(id=session['user_id'])
        return render_template('index.html', todos=todos, user=user)
    else:
        return redirect(url_for('login'))

# Login-Seite
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

# Registrierungsseite
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

# Logout-Funktion
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Neues Todo hinzufügen
@app.route('/add', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = request.form.get('task')
    if task:
        new_todo = Todo(task=task, done=False, user_id=session['user_id'])
        db.session.add(new_todo)
        db.session.commit()
        flash('Todo wurde erfolgreich hinzugefügt.')
    return redirect(url_for('index'))

# Todo bearbeiten
@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    todo = Todo.query.get_or_404(todo_id)
    if request.method == 'POST':
        todo.task = request.form.get('task')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', todo=todo)

# Todo löschen
@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    flash('Todo erfolgreich gelöscht.')
    return redirect(url_for('index'))

# Todo-Status ändern
@app.route('/check/<int:todo_id>', methods=['POST'])
def check(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    todo = Todo.query.get_or_404(todo_id)
    todo.done = not todo.done
    db.session.commit()
    flash('Todo-Status aktualisiert.')
    return redirect(url_for('index'))

# Route für API
@app.route('/api/getToDo/<userid>')
def api_getToDo(userid):
    todo = ToDo.query.filter_by(user_id = userid)
    return jsonify([s.toDict() for s in todo])
 
@app.route('/api/getallusers')
def api_getallusers():
    user = User.query.all()
    return jsonify([s.toDict() for s in user])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
