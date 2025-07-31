CREATE TABLE questoes(  
    id INT PRIMARY KEY,
    enunciado TEXT,
    tema TEXT,
    tipo TEXT,
    nivel TEXT,
    gabarito TEXT,
    fonte TEXT
);

CREATE TABLE provas(
    id INTEGER PRIMARY KEY,
    data_criacao DATE,
    titulo TEXT
);

CREATE TABLE prova_questoes(
    prova_id INTEGER REFERENCES provas(id),
    questao_id INTEGER REFERENCES questoes(id),
    ordem INTEGER
)