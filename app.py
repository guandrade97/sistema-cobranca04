from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
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

# MODELS
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

# AUTENTICAÇÃO
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

@app.before_first_request
def create_tables():
    db.create_all()

# ROTAS DE AUTENTICAÇÃO
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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("As senhas não coincidem.")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já está em uso.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method="sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Conta criada com sucesso! Faça login.")
        return redirect(url_for("login"))

    return render_template("register.html")

# DASHBOARD
@app.route("/")
@login_required
def dashboard():
    cobrancas = Cobranca.query.filter_by(usuario_id=current_user.id).all()
    total_pendente = sum(c.valor for c in cobrancas)
    return render_template("dashboard.html", cobrancas=cobrancas, total_pendente=total_pendente, user=current_user)

# NOVA COBRANÇA
@app.route("/nova_cobranca", methods=["GET", "POST"])
@login_required
def nova_cobranca():
    if request.method == "POST":
        nome_cliente = request.form["nome_cliente"]
        descricao = request.form["descricao"]
        valor = float(request.form["valor"])  # valor da parcela, não total
        parcelas = int(request.form["parcelas"])
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]

        c = Cobranca(
            nome_cliente=nome_cliente,
            descricao=descricao,
            valor=valor,  # aqui salva o valor da parcela
            parcelas=parcelas,
            email=email,
            whatsapp=whatsapp,
            usuario_id=current_user.id
        )
        db.session.add(c)
        db.session.commit()

        for i in range(1, parcelas + 1):
            parcela = Parcela(
                cobranca_id=c.id,
                numero=i,
                valor=valor,  # usa o valor informado, sem dividir
                vencimento=date.today() + relativedelta(months=i - 1),
                paga=False,
                usuario_id=current_user.id
            )
            db.session.add(parcela)
        db.session.commit()

        flash("Cobrança e parcelas criadas com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("nova_cobranca.html")


# LISTAR PARCELAS
@app.route("/parcelas")
@login_required
def listar_parcelas():
    parcelas = Parcela.query.filter_by(usuario_id=current_user.id).order_by(Parcela.vencimento).all()
    return render_template("parcelas.html", parcelas=parcelas, now=date.today())

# NOVA PARCELA
@app.route("/nova_parcela", methods=["GET", "POST"])
@login_required
def nova_parcela():
    if request.method == "POST":
        cobranca_id = request.form["cobranca_id"]
        valor = float(request.form["valor"])
        vencimento_str = request.form["vencimento"]
        vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d").date()

        # Definir o número da nova parcela
        ult_parcela = Parcela.query.filter_by(cobranca_id=cobranca_id).order_by(Parcela.numero.desc()).first()
        numero = (ult_parcela.numero + 1) if ult_parcela else 1

        nova = Parcela(
            cobranca_id=cobranca_id,
            numero=numero,
            valor=valor,
            vencimento=vencimento,
            paga=False,
            usuario_id=current_user.id
        )
        db.session.add(nova)
        db.session.commit()

        flash("Parcela adicionada com sucesso.")
        return redirect(url_for("listar_parcelas"))

    cobrancas = Cobranca.query.filter_by(usuario_id=current_user.id).all()
    return render_template("nova_parcela.html", cobrancas=cobrancas)

# MARCAR PARCELA COMO PAGA
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

# EDITAR PARCELA
@app.route("/parcela/editar/<int:parcela_id>", methods=["GET", "POST"])
@login_required
def editar_parcela(parcela_id):
    parcela = Parcela.query.get_or_404(parcela_id)
    if parcela.usuario_id != current_user.id:
        flash("Acesso negado.")
        return redirect(url_for("listar_parcelas"))

    if request.method == "POST":
        try:
            parcela.valor = float(request.form["valor"])
            parcela.vencimento = datetime.strptime(request.form["vencimento"], "%Y-%m-%d").date()
            db.session.commit()
            flash("Parcela atualizada com sucesso.")
            return redirect(url_for("listar_parcelas"))
        except Exception as e:
            flash("Erro ao atualizar parcela.")
            return redirect(url_for("editar_parcela", parcela_id=parcela_id))

    return render_template("editar_parcela.html", parcela=parcela)

# EXCLUIR PARCELA
@app.route("/parcela/excluir/<int:parcela_id>")
@login_required
def excluir_parcela(parcela_id):
    parcela = Parcela.query.get_or_404(parcela_id)
    if parcela.usuario_id != current_user.id:
        flash("Acesso negado.")
        return redirect(url_for("listar_parcelas"))
    db.session.delete(parcela)
    db.session.commit()
    flash(f"Parcela {parcela.numero} excluída com sucesso.")
    return redirect(url_for("listar_parcelas"))

# ENVIOS AUTOMÁTICOS
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

# AGENDADOR
scheduler = BackgroundScheduler()
scheduler.add_job(func=enviar_cobrancas, trigger="interval", hours=24)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)

