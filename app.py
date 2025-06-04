from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/nova_cobranca', methods=['GET', 'POST'])
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
