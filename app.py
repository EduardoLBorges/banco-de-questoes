from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from config import Config
from datetime import datetime
import random

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "sua_chave_secreta"  # Necessário para o uso de flash()

db = SQLAlchemy(app)

# MODELOS

class Questao(db.Model):
    __tablename__ = 'questoes'

    id = db.Column(db.Integer, primary_key=True)
    enunciado = db.Column(db.Text, nullable=False)
    tema = db.Column(db.String(100))
    tipo = db.Column(db.String(50))
    nivel = db.Column(db.String(50))
    gabarito = db.Column(db.Text)
    fonte = db.Column(db.String(200))

class Prova(db.Model):
    __tablename__ = 'provas'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.now)

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
    questoes = Questao.query.order_by(Questao.id.desc()).limit(5).all()
    return render_template('home.html', questoes=questoes)


@app.route("/cadastrar", methods=["GET", "POST"], endpoint="cadastrar_questao")
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


@app.route("/gerar_prova", methods=["GET", "POST"])
def gerar_prova():
    if request.method == "POST":
        temas = request.form.getlist("temas")
        nivel = request.form.get("nivel")
        quantidade = int(request.form.get("quantidade"))

        query = Questao.query

        if temas:
            query = query.filter(Questao.tema.in_(temas))
        if nivel:
            query = query.filter_by(nivel=nivel)

        questoes_disponiveis = query.all()

        if not questoes_disponiveis:
            flash("Nenhuma questão encontrada com os filtros selecionados.")
            return redirect(url_for("gerar_prova"))

        questoes_sorteadas = random.sample(
            questoes_disponiveis,
            min(quantidade, len(questoes_disponiveis))
        )

        tema_str = ", ".join(temas) if temas else "Geral"
        nova_prova = Prova(titulo=f"Prova gerada ({tema_str})")
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


@app.route("/provas")
def listar_provas():
    provas = Prova.query.order_by(Prova.data_criacao.desc()).all()
    return render_template("listar_provas.html", provas=provas)


@app.route("/prova/<int:prova_id>/excluir", methods=["POST"])
def excluir_prova(prova_id):
    prova = Prova.query.get_or_404(prova_id)
    # Exclui as questões associadas primeiro
    ProvaQuestao.query.filter_by(prova_id=prova.id).delete()
    db.session.delete(prova)
    db.session.commit()
    flash("Prova excluída com sucesso!")
    return redirect(url_for("listar_provas"))


@app.route("/prova/<int:prova_id>/trocar_questao/<int:prova_questao_id>", methods=["POST"])
def trocar_questao(prova_id, prova_questao_id):
    pq = ProvaQuestao.query.get_or_404(prova_questao_id)
    prova = Prova.query.get_or_404(prova_id)

    # Busca questões do mesmo tema e nível, que não estão na prova
    questoes_na_prova = [q.questao_id for q in ProvaQuestao.query.filter_by(prova_id=prova_id).all()]
    novas_questoes = Questao.query.filter(
        Questao.tema == pq.questao.tema,
        Questao.nivel == pq.questao.nivel,
        ~Questao.id.in_(questoes_na_prova)
    ).all()

    if not novas_questoes:
        flash("Não há outra questão disponível com os mesmos critérios.")
        return redirect(url_for("visualizar_prova", prova_id=prova_id))

    nova_questao = random.choice(novas_questoes)
    pq.questao_id = nova_questao.id
    db.session.commit()
    flash("Questão trocada com sucesso!")
    return redirect(url_for("visualizar_prova", prova_id=prova_id))


if __name__ == "__main__":
    app.run(debug=True)
