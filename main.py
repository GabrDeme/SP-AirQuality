from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
import json

# -----------------------------
# Configuração inicial
# -----------------------------
app = Flask("AirQuality")

# Configurações do banco MySQL
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:senai%40134@127.0.0.1/db_aqi"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

mydb = SQLAlchemy(app)

# -----------------------------
# Modelos do banco
# -----------------------------
class Leituras(mydb.Model):
    __tablename__ = "tb_leituras"
    idLeitura = mydb.Column(mydb.Integer, primary_key=True)
    data_hora = mydb.Column(mydb.String(255))
    co2 = mydb.Column(mydb.String(255))
    umidade = mydb.Column(mydb.String(255))
    pressao = mydb.Column(mydb.String(255))
    temperatura = mydb.Column(mydb.String(255))
    poeira_1 = mydb.Column(mydb.String(255))
    poeira_2 = mydb.Column(mydb.String(255))
    altitude = mydb.Column(mydb.String(255))

    def to_json(self):
        return {
            "idLeitura": self.idLeitura,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "co2": self.co2,
            "umidade": self.umidade,
            "pressao": self.pressao,
            "temperatura": self.temperatura,
            "poeira_1": self.poeira_1,
            "poeira_2": self.poeira_2,
            "altitude": self.altitude,
        }

class Poluentes(mydb.Model):
    __tablename__ = "tb_poluentes"
    idPoluente = mydb.Column(mydb.Integer, primary_key=True)
    idLeitura = mydb.Column(mydb.String(255))
    nome = mydb.Column(mydb.String(255))
    valor = mydb.Column(mydb.String(255))
    unidade = mydb.Column(mydb.String(255))

    def to_json(self):
        return {
            "idPoluente": self.idPoluente,
            "idLeitura": self.idLeitura,
            "nome": self.nome,
            "valor": self.valor,
            "unidade": self.unidade,
            }


# -----------------------------
# Função auxiliar de resposta
# -----------------------------
def gera_resposta(status, conteudo, mensagem=False):
    body = {"conteudo": conteudo}
    if mensagem:
        body["mensagem"] = mensagem
    return Response(json.dumps(body), status=status, mimetype="application/json")


# -----------------------------
# Rotas CRUD - Leituras
# -----------------------------

# GET - Todas as leituras
@app.route("/aqi/tb_leituras", methods=["GET"])
def get_leituras():
    leituras = Leituras.query.all()
    leituras_json = [l.to_json() for l in leituras]
    return gera_resposta(200, leituras_json)


# GET - Leitura por ID
@app.route("/aqi/tb_leituras/<int:idLeitura>", methods=["GET"])
def get_leitura_id(idLeitura):
    leitura = Leituras.query.filter_by(idLeitura=idLeitura).first()
    if not leitura:
        return gera_resposta(404, {}, "Leitura não encontrada")
    return gera_resposta(200, leitura.to_json())


# POST - Criar leitura
@app.route("/aqi/tb_leituras", methods=["POST"])
def criar_leitura():
    requisicao = request.get_json()
    try:
        leitura = Leituras(
            data_hora=requisicao["data_hora"],
            co2=requisicao["co2"],
            umidade=requisicao["umidade"],
            pressao=requisicao["pressao"],
            temperatura=requisicao["temperatura"],
            poeira_1=requisicao["poeira_1"],
            poeira_2=requisicao["poeira_2"],
            altitude=requisicao["altitude"],
        )
        mydb.session.add(leitura)
        mydb.session.commit()
        return gera_resposta(201, leitura.to_json(), "Leitura criada com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_resposta(400, {}, "Erro ao cadastrar leitura")


# PUT - Atualizar leitura
@app.route("/aqi/tb_leituras/<int:idLeitura>", methods=["PUT"])
def atualizar_leitura(idLeitura):
    leitura = Leituras.query.filter_by(idLeitura=idLeitura).first()
    if not leitura:
        return gera_resposta(404, {}, "Leitura não encontrada")

    requisicao = request.get_json()
    try:
        for campo in [
            "data_hora",
            "co2",
            "umidade",
            "pressao",
            "temperatura",
            "poeira_1",
            "poeira_2",
            "altitude",
        ]:
            if campo in requisicao:
                setattr(leitura, campo, requisicao[campo])

        mydb.session.commit()
        return gera_resposta(200, leitura.to_json(), "Leitura atualizada com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_resposta(400, {}, "Erro ao atualizar leitura")


# GET - Todos os poluentes
@app.route("/aqi/tb_poluentes", methods=["GET"])
def get_poluentes():
    poluentes = Poluentes.query.all()
    poluentes_json = [p.to_json() for p in poluentes]
    return gera_resposta(200, poluentes_json)


# GET - Poluente por ID
@app.route("/aqi/tb_poluentes/<int:idPoluente>", methods=["GET"])
def get_poluente_id(idPoluente):
    poluente = Poluentes.query.filter_by(idPoluente=idPoluente).first()
    if not poluente:
        return gera_resposta(404, {}, "Poluente não encontrado")
    return gera_resposta(200, poluente.to_json())


# POST - Criar poluente
@app.route("/aqi/tb_poluentes", methods=["POST"])
def criar_poluente():
    requisicao = request.get_json()
    try:
        poluente = Poluentes(
            idLeitura=requisicao["idLeitura"],
            nome=requisicao["nome"],
            valor=requisicao["valor"],
            unidade=requisicao["unidade"],
        )
        mydb.session.add(poluente)
        mydb.session.commit()
        return gera_resposta(201, poluente.to_json(), "Poluente criado com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_resposta(400, {}, "Erro ao cadastrar poluente")


# PUT - Atualizar poluente
@app.route("/aqi/tb_poluentes/<int:idPoluente>", methods=["PUT"])
def atualizar_poluente(idPoluente):
    poluente = Poluentes.query.filter_by(idPoluente=idPoluente).first()
    if not poluente:
        return gera_resposta(404, {}, "Poluente não encontrado")

    requisicao = request.get_json()
    try:
        for campo in ["idLeitura", "nome", "valor", "unidade"]:
            if campo in requisicao:
                setattr(poluente, campo, requisicao[campo])

        mydb.session.commit()
        return gera_resposta(200, poluente.to_json(), "Poluente atualizado com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_resposta(400, {}, "Erro ao atualizar poluente")


# -----------------------------
# Inicialização
# -----------------------------
if __name__ == "__main__":
    app.run(port=5000, host="localhost", debug=True)
