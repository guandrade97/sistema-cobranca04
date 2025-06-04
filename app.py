from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('cobranca.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        telefone TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cobrancas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        valor REAL,
        vencimento TEXT,
        status TEXT,
        boleto_link TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('cobranca.db')
    c = conn.cursor()
    c.execute('''SELECT cobrancas.id, clientes.nome, cobrancas.valor, cobrancas.vencimento, cobrancas.status
                 FROM cobrancas JOIN clientes ON cobrancas.cliente_id = clientes.id''')
    cobrancas = c.fetchall()
    conn.close()
    return render_template('dashboard.html', cobrancas=cobrancas)

@app.route('/nova_cobranca', methods=['GET', 'POST'])
def nova_cobranca():
    conn = sqlite3.connect('cobranca.db')
    c = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        valor = float(request.form['valor'])
        vencimento = request.form['vencimento']

        c.execute('INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)', (nome, email, telefone))
        cliente_id = c.lastrowid

        boleto_link = f"https://boleto.fake.bb.com.br/{cliente_id}-{datetime.now().timestamp()}"

        c.execute('''INSERT INTO cobrancas (cliente_id, valor, vencimento, status, boleto_link)
                     VALUES (?, ?, ?, ?, ?)''', (cliente_id, valor, vencimento, 'pendente', boleto_link))
        conn.commit()
        conn.close()

        print(f"[WHATSAPP] Enviando boleto para {telefone} - Link: {boleto_link}")
        print(f"[EMAIL] Enviando boleto para {email} - Link: {boleto_link}")

        return redirect(url_for('index'))
    return render_template('nova_cobranca.html')

if __name__ == '__main__':
    app.run(debug=True)