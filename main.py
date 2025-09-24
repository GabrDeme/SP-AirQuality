# SQL_ALCHEMY
# PERMITE a conexão da API COM o banco de dados
# FLASK - Permite a criação da API com Python
# Response e Request -> Requisição
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
import json 


app = Flask('AirQuality')

# Rasrear as modificações realizadas
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Configuração de conexão com o banco
# %40 -> faz o papel de @
# 1 - Usuario (root) 2 - Senha(Senai540134) 3 - localhost (127.0.0.1) 4 - nome do banco
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Senai%40134@127.0.0.1/db_aqi"

mybd = SQLAlchemy(app)

# Classe para definir o modelo dos dados que correspondem a tabela do banco de dados
class Leituras(mybd.Model):
    __tablename__ = 'tb_leituras'
    idLeitura = mybd.Column(mybd.Integer, primary_key=True)
    data_hora = mybd.Column(mybd.String(255))
    co2 = mybd.Column(mybd.String(255))
    umidade = mybd.Column(mybd.String(255))
    pressao = mybd.Column(mybd.String(255))
    temperatura = mybd.Column(mybd.String(255))
    poeira_1 = mybd.Column(mybd.String(255))
    poeira_2= mybd.Column(mybd.String(255))
    altitude = mybd.Column(mybd.String(255))

class Poluentes(mybd.Model):
    __tablename__ = 'tb_poluentes'
    idPoluente = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.String(255))
    nome = mybd.Column(mybd.String(255))
    valor = mybd.Column(mybd.String(255))
    unidade = mybd.Column(mybd.String(255))

class Qualidade(mybd.Model):
    __tablename__ = 'tb_qualidade'
    idQualidade = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.String(255))
    aqi = mybd.Column(mybd.String(255))
    red = mybd.Column(mybd.String(255))
    green = mybd.Column(mybd.String(255))
    blue = mybd.Column(mybd.String(255))
    category = mybd.Column(mybd.String(255))
    poluenteDominante = mybd.Column(mybd.String(255))
    
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

class Recomendacao(mybd.Model):
    __tablename__ = 'tb_recomendacao'
    idRecomendacao = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.String(255))
    publico_alvo = mybd.Column(mybd.String(255))
    recomendacao = mybd.Column(mybd.String(1000))
    
    def to_json(self):
        return {
            "idRecomendacao": self.idRecomendacao,
            "idLeitura": self.idLeitura,
            "publico_alvo": self.publico_alvo,
            "recomendacao": self.recomendacao
        }
    

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
        mybd.session.add(nova_qualidade)
        mybd.session.commit()
        return gera_resposta(201, "qualidade", nova_qualidade.to_json(), "Registro de qualidade criado com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(400, "erro", {}, "Erro ao criar registro de qualidade.")

@app.route('/qualidade', methods=['GET'])
def get_qualidades():
    try:
        qualidades = Qualidade.query.all()
        if not qualidades:
            return gera_resposta(404, "qualidades", [], "Nenhuma qualidade encontrada.")
        
        qualidades_json = [q.to_json() for q in qualidades]
        return gera_resposta(200, "qualidades", qualidades_json)
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, "erro", {}, "Ocorreu um erro interno no servidor.")
    
@app.route('/qualidade/<int:id>', methods=['GET'])
def get_qualidade_por_id(id):
    try:
        qualidade = Qualidade.query.get(id)
        if not qualidade:
            return gera_resposta(404, "qualidade", {}, f"Qualidade com ID {id} não encontrada.")
        return gera_resposta(200, "qualidade", qualidade.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, "erro", {}, "Ocorreu um erro interno no servidor.")
    
@app.route('/recomendacao', methods=['POST'])
def cria_recomendacao():
    body = request.get_json()
    try:
        nova_recomendacao = Recomendacao(
            idLeitura=body.get('idLeitura'),
            publico_alvo=body.get('publico_alvo'),
            recomendacao=body.get('recomendacao')
        )
        mybd.session.add(nova_recomendacao)
        mybd.session.commit()
        return gera_resposta(201, "recomendacao", nova_recomendacao.to_json(), "Recomendação criada com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(400, "erro", {}, "Erro ao criar recomendação.")

@app.route('/recomendacao', methods=['GET'])
def get_recomendacoes():
    try:
        recomendacoes = Recomendacao.query.all()
        if not recomendacoes:
            return gera_resposta(404, "recomendacoes", [], "Nenhuma recomendação encontrada.")
        
        recomendacoes_json = [r.to_json() for r in recomendacoes]
        return gera_resposta(200, "recomendacoes", recomendacoes_json)
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, "erro", {}, "Ocorreu um erro interno no servidor.")

@app.route('/recomendacao/<int:id>', methods=['GET'])
def get_recomendacao_por_id(id):
    try:
        recomendacao = Recomendacao.query.get(id)
        if not recomendacao:
            return gera_resposta(404, "recomendacao", {}, f"Recomendação com ID {id} não encontrada.")
        return gera_resposta(200, "recomendacao", recomendacao.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_resposta(500, "erro", {}, "Ocorreu um erro interno no servidor.")

    

def gera_resposta(status: int, nome_do_conteudo: str, conteudo: any, mensagem=False):
    body = {}
    body[nome_do_conteudo] = conteudo
    if(mensagem):
        body['mensagem'] = mensagem
        
    return Response(json.dumps(body), status=status, mimetype="application/json")

app.run(port=5000, host='localhost', debug=True)