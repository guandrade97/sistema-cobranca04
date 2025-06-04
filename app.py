from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"  # Altere para uma chave forte no deploy

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Usuários fixos para teste - depois troque por DB
users = {
    "admin": {"password": "senha123"},
    "user1": {"password": "abc123"},
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users.get(username)
        if user and user["password"] == password:
            user_obj = User(username)
            login_user(user_obj)
            return redirect(url_for("dashboard"))
        else:
            return "Usuário ou senha incorretos", 401

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=10000)

