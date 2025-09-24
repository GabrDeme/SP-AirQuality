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
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:senai%40134@127.0.0.1/db_carro"

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

class Recomendacao(mybd.Model):
    __tablename__ = 'tb_recomendacao'
    idRecomendacao = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.String(255))
    publico_alvo = mybd.Column(mybd.String(255))
    recomendacao = mybd.Column(mybd.String(1000))
    