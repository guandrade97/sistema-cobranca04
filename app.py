from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Models
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

    parcelas_rel = db.relationship('Parcela', backref='cobranca', lazy=True)

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cobranca_id = db.Column(db.Integer, db.ForeignKey('cobranca.id'))
    numero = db.Column(db.Integer)
    valor = db.Column(db.Float)
    vencimento = db.Column(db.Date)
    paga = db.Column(db.Boolean, default=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))

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

        # Criar parcelas com vencimento mensal
        for i in range(1, parcelas + 1):
            parcela = Parcela(
                cobranca_id=c.id,
                numero=i,
                valor=round(valor / parcelas, 2),
                vencimento=date.today() + relativedelta(months=i - 1),
                paga=False,
                usuario_id=current_user.id
            )
            db.session.add(parcela)
        db.session.commit()

        flash("Cobrança e parcelas criadas com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("nova_cobranca.html")

@app.route("/parcelas")
@login_required
def listar_parcelas():
    parcelas = Parcela.query.filter_by(usuario_id=current_user.id).order_by(Parcela.vencimento).all()
    return render_template("parcelas.html", parcelas=parcelas)

@app.route("/parcela/pagar/<int:parcela_id>")
@login_required
def pagar_parcela(parcela_id):
    parcela = Parcela.query.get_or_404(parcela_id)
    if parcela.usuario_id != current_user.id:
        flash("Acesso negado.")
        return redirect(url_for("listar_parcelas"))
    parcela.paga = True
    db.session.commit()
    flash(f"Parcela {parcela.numero} marcada como paga.")
    return redirect(url_for("listar_parcelas"))

def enviar_cobrancas():
    hoje = date.today()
    parcelas = Parcela.query.filter_by(paga=False).all()
    for p in parcelas:
        dias_para_vencer = (p.vencimento - hoje).days
        if dias_para_vencer in [5, 4, 3, 2, 1, 0]:
            print(f"[AVISO] Enviar mensagem para {p.cobranca.nome_cliente}: Parcela {p.numero} vence em {dias_para_vencer} dia(s).")
        elif dias_para_vencer < 0:
            dias_atraso = abs(dias_para_vencer)
            print(f"[ATENÇÃO] Enviar mensagem para {p.cobranca.nome_cliente}: Parcela {p.numero} está vencida há {dias_atraso} dia(s).")

scheduler = BackgroundScheduler()
scheduler.add_job(func=enviar_cobrancas, trigger="interval", hours=24)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)



