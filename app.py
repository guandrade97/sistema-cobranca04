from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Modelos do banco
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

    # Certifique-se de que get_id retorna o id numérico como string
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


@login_manager.user_loader
def load_user(user_id):
    # Converte user_id para int e busca no banco
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

@app.before_first_request
def create_tables():
    db.create_all()

# Rotas de autenticação
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Usuário já existe")
            return redirect(url_for("register"))

        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro feito com sucesso! Faça login.")
        return redirect(url_for("login"))

    return render_template("register.html")

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

# Dashboard mostrando cobranças do usuário
@app.route("/")
@login_required
def dashboard():
    cobrancas = Cobranca.query.filter_by(usuario_id=current_user.id).all()
    total_pendente = sum(c.valor for c in cobrancas)
    return render_template("dashboard.html", cobrancas=cobrancas, total_pendente=total_pendente, user=current_user)

# Criar nova cobrança
@app.route("/nova_cobranca", methods=["GET", "POST"])
@login_required
def nova_cobranca():
    if request.method == "POST":
        descricao = request.form["descricao"]
        valor = float(request.form["valor"])

        c = Cobranca(descricao=descricao, valor=valor, usuario_id=current_user.id)
        db.session.add(c)
        db.session.commit()
        flash("Cobrança criada com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("nova_cobranca.html")

if __name__ == "__main__":
    app.run(debug=True, port=10000)
