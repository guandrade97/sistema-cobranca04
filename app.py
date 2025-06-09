from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

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
    cobranca_id = db.Column(db.Integer, db.ForeignKey('cobranca.id'))
    data_vencimento = db.Column(db.Date)
    valor = db.Column(db.Float)
    status = db.Column(db.String(20), default="pendente")  # pendente, paga

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        valor_total = float(request.form["valor"])
        parcelas = int(request.form["parcelas"])
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]
        primeira_data = datetime.strptime(request.form["data_primeira_parcela"], "%Y-%m-%d").date()

        c = Cobranca(
            nome_cliente=nome_cliente,
            descricao=descricao,
            valor=valor_total,
            parcelas=parcelas,
            email=email,
            whatsapp=whatsapp,
            usuario_id=current_user.id
        )
        db.session.add(c)
        db.session.commit()

        valor_parcela = round(valor_total / parcelas, 2)
        for i in range(parcelas):
            data_venc = primeira_data + timedelta(days=30 * i)
            p = Parcela(cobranca_id=c.id, data_vencimento=data_venc, valor=valor_parcela)
            db.session.add(p)

        db.session.commit()
        flash("Cobrança e parcelas criadas com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("nova_cobranca.html")
@app.route("/parcela/<int:parcela_id>/pagar", methods=["POST"])
@login_required
def marcar_parcela_paga(parcela_id):
    parcela = Parcela.query.get_or_404(parcela_id)

    # Verifica se a parcela pertence a uma cobrança do usuário logado
    if parcela.cobranca.usuario_id != current_user.id:
        flash("Você não tem permissão para alterar essa parcela.")
        return redirect(url_for("dashboard"))

    parcela.status = "paga"
    db.session.commit()
    flash("Parcela marcada como paga.")
    return redirect(url_for("ver_parcelas", cobranca_id=parcela.cobranca_id))


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

# === Simulação do envio de mensagens (print no terminal) ===
def enviar_mensagem(destino, mensagem):
    print(f"[MENSAGEM] Para: {destino} | Texto: {mensagem}")

# === Agendador automático para cobrança ===
def verificar_cobrancas():
    hoje = datetime.today().date()
    dias_antes = [5, 4, 3, 2, 1, 0]

    parcelas = Parcela.query.filter_by(status="pendente").all()
    for p in parcelas:
        dias_para_vencer = (p.data_vencimento - hoje).days
        dias_vencida = (hoje - p.data_vencimento).days

        cobranca = Cobranca.query.get(p.cobranca_id)
        nome = cobranca.nome_cliente

        if dias_para_vencer in dias_antes:
            msg = f"Olá, {nome}. Sua parcela vence em {dias_para_vencer} dia(s). Por favor, efetue o pagamento."
            enviar_mensagem(cobranca.whatsapp, msg)

        if dias_para_vencer == 0:
            msg = f"Olá, {nome}. Hoje é o vencimento da sua parcela. Evite juros, pague hoje!"
            enviar_mensagem(cobranca.whatsapp, msg)

        if dias_vencida > 0:
            msg = f"Olá, {nome}. Sua parcela venceu há {dias_vencida} dia(s). Por favor, regularize o quanto antes."
            enviar_mensagem(cobranca.whatsapp, msg)

# Iniciar agendador ao iniciar app
scheduler = BackgroundScheduler()
scheduler.add_job(verificar_cobrancas, 'interval', hours=24)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)




