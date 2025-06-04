from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Pode mudar para uma string segura

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuários cadastrados (exemplo simples em memória)
users = {
    "admin": {"password": "1234"},
    "usuario1": {"password": "abcd"},
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect('/')
        else:
            erro = "Usuário ou senha inválidos"
    return render_template('login.html', erro=erro)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user.id)

@app.route('/nova_cobranca', methods=['GET', 'POST'])
@login_required
def nova_cobranca():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        valor_str = request.form['valor']

        if not valor_str:
            return "Erro: o campo valor é obrigatório", 400

        try:
            valor = float(valor_str)
        except ValueError:
            return "Erro: valor inválido", 400

        # Aqui futuramente salvaremos no banco de dados
        return redirect('/')

    return render_template('nova_cobranca.html')

if __name__ == '__main__':
    app.run(debug=True, port=10000)

