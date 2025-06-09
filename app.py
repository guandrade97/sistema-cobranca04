from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

    def get_id(self):
        return str(self.id)

class Cobranca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    nome_cliente = db.Column(db.String(150))
    email = db.Column(db.String(150))
    whatsapp = db.Column(db.String(20))
    parcelas = db.Column(db.Integer)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cobranca_id = db.Column(db.Integer, db.ForeignKey('cobranca.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    pago = db.Column(db.Boolean, default=False)
    data_pagamento = db.Column(db.Date, nullable=True)

    cobranca = db.relationship('Cobranca', backref=db.backref('parcelas', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Usuário ou senha incorretos")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    cobrancas = Cobranca.query.filter_by(usuario_id=current_user.id).all()
    total_pendente = sum(c.valor for c in cobrancas)
    return render_template("dashboard.html", cobrancas=cobrancas, total_pendente=total_pendente, user=current_user)

@app.route("/nova_cobranca", methods=["GET", "POST"])
@login_required
def nova_cobranca():
    if request.method == "POST":
        nome_cliente = request.form["nome_cliente"]
        descricao = request.form["descricao"]
        valor = float(request.form["valor"])
        parcelas = int(request.form["parcelas"])
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]

        c = Cobranca(
            nome_cliente=nome_cliente,
            descricao=descricao,
            valor=valor,
            parcelas=parcelas,
            email=email,
            whatsapp=whatsapp,
            usuario_id=current_user.id
        )
        db.session.add(c)
        db.session.commit()

        flash("Cobrança criada com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("nova_cobranca.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("As senhas não conferem.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já está em uso.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method="sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Usuário registrado com sucesso. Faça login.")
        return redirect(url_for("login"))

    return render_template("register.html")



