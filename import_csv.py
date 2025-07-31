import csv
from app import app, db, Questao

def normalizar(texto):
    """Remove espaços duplicados e deixa tudo minúsculo"""
    return ' '.join(texto.strip().lower().split())

def questao_existe(enunciado):
    """Verifica se já existe uma questão com esse enunciado"""
    with db.session.no_autoflush:  # ✅ Impede flush automático
        return db.session.query(Questao).filter(
            db.func.lower(db.func.trim(Questao.enunciado)) == normalizar(enunciado)
        ).first() is not None

arquivo_csv = "questoes.csv"
total_inseridas = 0
total_duplicadas = 0

with app.app_context():
    with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        
        for row in leitor:
            enunciado = row["enunciado"]

            if questao_existe(enunciado):
                print(f"❌ Questão duplicada ignorada: {enunciado[:60]}...")
                total_duplicadas += 1
                continue

            nova = Questao(
                enunciado=enunciado,
                tema=row["tema"],
                tipo=row["tipo"],
                nivel=row["nivel"],
                gabarito=row["gabarito"],
                fonte=row["fonte"]
            )
            db.session.add(nova)
            total_inseridas += 1

        db.session.commit()

    print(f"\n✅ {total_inseridas} questões inseridas com sucesso.")
    print(f"🔁 {total_duplicadas} questões duplicadas foram ignoradas.")
