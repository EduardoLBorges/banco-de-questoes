from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from config import Config
from datetime import datetime
import random

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

class Questao(db.Model):
    __tablename__ = 'questoes'

    id = db.Column(db.Integer, primary_key=True)
    enunciado = db.Column(db.Text, nullable=False)
    tema = db.Column(db.String(100))
    tipo = db.Column(db.String(50))  # Ex: "múltipla escolha", "dissertativa"
    nivel = db.Column(db.String(50))  # Ex: "fácil", "médio", "difícil"
    gabarito = db.Column(db.Text)
    fonte = db.Column(db.String(200))

class Prova(db.Model):
    __tablename__ = 'provas'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    questoes = db.relationship("ProvaQuestao", back_populates="prova")

class ProvaQuestao(db.Model):
    __tablename__ = 'prova_questoes'

    id = db.Column(db.Integer, primary_key=True)
    prova_id = db.Column(db.Integer, db.ForeignKey('provas.id'), nullable=False)
    questao_id = db.Column(db.Integer, db.ForeignKey('questoes.id'), nullable=False)
    ordem = db.Column(db.Integer)

    prova = db.relationship("Prova", back_populates="questoes")
    questao = db.relationship("Questao")


@app.route("/")
def home():
        # Busca as últimas 5 questões cadastradas
    questoes = Questao.query.order_by(Questao.id.desc()).limit(5).all()
    return render_template('home.html', questoes=questoes)


@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar_questao():
    if request.method == "POST":
        enunciado = request.form["enunciado"]
        tema = request.form["tema"]
        tipo = request.form["tipo"]
        nivel = request.form["nivel"]
        gabarito = request.form["gabarito"]
        fonte = request.form["fonte"]

        nova = Questao(
            enunciado=enunciado,
            tema=tema,
            tipo=tipo,
            nivel=nivel,
            gabarito=gabarito,
            fonte=fonte
        )
        db.session.add(nova)
        db.session.commit()
        flash("Questão cadastrada com sucesso!")
        return redirect(url_for("cadastrar_questao"))

    return render_template("cadastrar.html")

@app.route("/questoes")
def listar_questoes():
    questoes = Questao.query.order_by(Questao.id.desc()).all()
    return render_template("listar_questoes.html", questoes=questoes)

@app.template_filter('truncate')
def truncate(text, length=80):
    return text if len(text) <= length else text[:length] + "..."

import random
from sqlalchemy import func

@app.route("/gerar_prova", methods=["GET", "POST"])
def gerar_prova():
    if request.method == "POST":
        tema = request.form.get("tema")
        nivel = request.form.get("nivel")
        quantidade = int(request.form.get("quantidade"))

        query = Questao.query

        if tema:
            query = query.filter(Questao.tema.ilike(f"%{tema}%"))
        if nivel:
            query = query.filter_by(nivel=nivel)

        questoes_disponiveis = query.all()
        questoes_sorteadas = random.sample(questoes_disponiveis, min(quantidade, len(questoes_disponiveis)))

        nova_prova = Prova(titulo=f"Prova gerada ({tema or 'Geral'})")
        db.session.add(nova_prova)
        db.session.commit()

        for i, questao in enumerate(questoes_sorteadas):
            pq = ProvaQuestao(prova_id=nova_prova.id, questao_id=questao.id, ordem=i+1)
            db.session.add(pq)

        db.session.commit()
        return redirect(url_for("visualizar_prova", prova_id=nova_prova.id))

    return render_template("gerar_prova.html")

@app.route("/prova/<int:prova_id>")
def visualizar_prova(prova_id):
    prova = Prova.query.get_or_404(prova_id)
    questoes = ProvaQuestao.query.filter_by(prova_id=prova.id).order_by(ProvaQuestao.ordem).all()
    return render_template("prova.html", prova=prova, questoes=questoes)


if __name__ == "__main__":
    app.run(debug=True)
