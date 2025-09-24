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

class Qualidade(mydb.Model):
    __tablename__ = 'tb_qualidade'
    idQualidade = mydb.Column(mydb.Integer, primary_key=True)
    idLeitura = mydb.Column(mydb.String(255))
    aqi = mydb.Column(mydb.String(255))
    red = mydb.Column(mydb.String(255))
    green = mydb.Column(mydb.String(255))
    blue = mydb.Column(mydb.String(255))
    category = mydb.Column(mydb.String(255))
    poluenteDominante = mydb.Column(mydb.String(255))
    
    def to_json(self):
        return {
            "idQualidade": self.idQualidade,
            "idLeitura": self.idLeitura,
            "aqi": self.aqi,
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "category": self.category,
            "poluenteDominante": self.poluenteDominante
        }

class Recomendacao(mydb.Model):
    __tablename__ = 'tb_recomendacao'
    idRecomendacao = mydb.Column(mydb.Integer, primary_key=True)
    idLeitura = mydb.Column(mydb.String(255))
    publico_alvo = mydb.Column(mydb.String(255))
    recomendacao = mydb.Column(mydb.String(1000))
    
    def to_json(self):
        return {
            "idRecomendacao": self.idRecomendacao,
            "idLeitura": self.idLeitura,
            "publico_alvo": self.publico_alvo,
            "recomendacao": self.recomendacao
        }
    


# Configuração de conexão com o banco
# %40 -> faz o papel de @
# 1 - Usuario (root) 2 - Senha(Senai540134) 3 - localhost (127.0.0.1) 4 - nome do banco
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Senai%40134@127.0.0.1/db_aqi"


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


def cria_qualidade():
    body = request.get_json()
    try:
        nova_qualidade = Qualidade(
            idLeitura=body.get('idLeitura'),
            aqi=body.get('aqi'),
            red=body.get('red'),
            green=body.get('green'),
            blue=body.get('blue'),
            category=body.get('category'),
            poluenteDominante=body.get('poluenteDominante')
        )
        mydb.session.add(nova_qualidade)
        mydb.session.commit()
        return gera_resposta(201, nova_qualidade.to_json(), "Registro de qualidade criado com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(400, {}, "Erro ao criar registro de qualidade.")

@app.route('/qualidade', methods=['GET'])
def get_qualidades():
    try:
        qualidades = Qualidade.query.all()
        if not qualidades:
            return gera_resposta(404, [], "Nenhuma qualidade encontrada.")
        
        qualidades_json = [q.to_json() for q in qualidades]
        return gera_resposta(200, qualidades_json)
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, {}, "Ocorreu um erro interno no servidor.")
    
@app.route('/qualidade/<int:id>', methods=['GET'])
def get_qualidade_por_id(id):
    try:
        qualidade = Qualidade.query.get(id)
        if not qualidade:
            return gera_resposta(404, {}, f"Qualidade com ID {id} não encontrada.")
        return gera_resposta(200, qualidade.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, {}, "Ocorreu um erro interno no servidor.")
    
@app.route('/recomendacao', methods=['POST'])
def cria_recomendacao():
    body = request.get_json()
    try:
        nova_recomendacao = Recomendacao(
            idLeitura=body.get('idLeitura'),
            publico_alvo=body.get('publico_alvo'),
            recomendacao=body.get('recomendacao')
        )
        mydb.session.add(nova_recomendacao)
        mydb.session.commit()
        return gera_resposta(201, nova_recomendacao.to_json(), "Recomendação criada com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(400, {}, "Erro ao criar recomendação.")

@app.route('/recomendacao', methods=['GET'])
def get_recomendacoes():
    try:
        recomendacoes = Recomendacao.query.all()
        if not recomendacoes:
            return gera_resposta(404, [], "Nenhuma recomendação encontrada.")
        
        recomendacoes_json = [r.to_json() for r in recomendacoes]
        return gera_resposta(200, recomendacoes_json)
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, {}, "Ocorreu um erro interno no servidor.")

@app.route('/recomendacao/<int:id>', methods=['GET'])
def get_recomendacao_por_id(id):
    try:
        recomendacao = Recomendacao.query.get(id)
        if not recomendacao:
            return gera_resposta(404,{}, f"Recomendação com ID {id} não encontrada.")
        return gera_resposta(200, recomendacao.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, {}, "Ocorreu um erro interno no servidor.")

    
# -----------------------------
# Função auxiliar de resposta
# -----------------------------
def gera_resposta(status, conteudo, mensagem=False):
    body = {"conteudo": conteudo}
    if mensagem:
        body["mensagem"] = mensagem
    return Response(json.dumps(body), status=status, mimetype="application/json")

if __name__ == "__main__":
    app.run(port=5000, host="localhost", debug=True)
