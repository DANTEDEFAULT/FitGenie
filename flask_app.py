from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash
import os
from openai import OpenAI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minhabase.sqlite3'
db = SQLAlchemy(app)
app.secret_key = os.urandom(24)
client = OpenAI(api_key='chave')

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GerenciadorDeUsuarios:
    def __init__(self, db):
        self.db = db

    def cadastrar_usuario(self, username, password):
        novo_usuario = Usuario(username=username, password=password)
        self.db.session.add(novo_usuario)
        self.db.session.commit()

    def excluir_usuario(self, usuario):
        self.db.session.delete(usuario)
        self.db.session.commit()

class AtualizadorDeDados:
    def __init__(self, db):
        self.db = db

    def commit(self):
        self.db.session.commit()

class Isaac:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Isaac, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.name = "Isaac"
            self.initialized = True

    def responder_pergunta(self, pergunta):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format={"type": "text"},
            messages=[
                {"role": "system", "content": "Responda como se você fosse um personal trainer virtual chamado Isaac, encarregado com a tarefa de auxiliar o usuário com quaisquer dúvidas em relação a rotina de exercícios, nutrição e coisas relacionadas. Tenha respostas naturais, como se o usuário estivesse conversando com um humano"},
                {"role": "user", "content": pergunta}
            ]
        )
        return response.choices[0].message.content

isaac_singleton = Isaac()
isaac = isaac_singleton

class PersonalTrainer:
    def __init__(self, isaac):
        self.isaac = isaac

    def responder_pergunta(self, pergunta):
        return self.isaac.responder_pergunta(pergunta)

class Comunicador:
    def __init__(self):
        self.isaac = isaac

    def responder_pergunta(self, pergunta):
        return self.isaac.responder_pergunta(pergunta)

mediador = Comunicador()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('homepage'))
    else:
        return redirect(url_for('login'))

@app.route('/homepage')
def homepage():
    if 'username' in session:
        username = session['username']
        return render_template('homepage.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/upload', methods=['POST', 'GET'])
def perguntar(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "text"},
        messages=[
            {"role": "system", "content": "Responda como se você fosse um personal trainer virtual chamado Alex, encarregado com a tarefa de auxiliar o usuário com quaisquer dúvidas em relação a rotina de exercícios, nutrição e coisas relacionadas. Tenha respostas naturais, como se o usuário estivesse conversando com um humano"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@app.route("/chatgpt", methods=['POST', 'GET'])
def chatgpt():
    if request.method == 'POST':
        prompt = request.form['homepage']
        resposta = perguntar(prompt)
        return render_template('homepage.html', resposta=resposta)
    return render_template('homepage.html')

@app.route('/cadastro', methods=['POST', 'GET'])
def cadastro():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if Usuario.query.filter_by(username=username).first():
            error = 'Usuário já existe!'
        else:
            user = Usuario(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('homepage'))
    return render_template('cadastro.html', error=error)

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user:
            if user.check_password(password):
                session['username'] = username
                return redirect(url_for('homepage'))
            else:
                error = 'Nome ou senha inválidos'
        else:
            error = 'Usuário não encontrado'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('homepage'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
