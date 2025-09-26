from datetime import datetime, timezone
from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import paho.mqtt.client as mqtt

from google_aqi_service import get_historical_air_quality

# ********************* CONEXÃO BANCO DE DADOS *********************************

app = Flask('leitura')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://grupo8:Senai%40134@projeto-integrador-grupo8.mysql.database.azure.com/db_aqi'
server_name = 'projeto-integrador-grupo8.mysql.database.azure.com'
port='3306'
username = 'grupo8'
password = 'Senai%40134'
database = 'db_aqi'

certificado = 'DigiCertGlobalRootG2.crt.pem'

uri = f"mysql://{username}:{password}@{server_name}:{port}/{database}"
ssl_certificado = f"?ssl_ca={certificado}"

app.config['SQLALCHEMY_DATABASE_URI'] = uri + ssl_certificado

app.config['SQLALCHEMY_ECHO'] = True  # Habilita o log de SQLAlchemy

mybd = SQLAlchemy(app)
# Cria uma instância do SQLAlchemy, passando a aplicação Flask como parâmetro.

# ********************* CONEXÃO SENSORES *********************************

mqtt_data = {}

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("projeto_integrado/SENAI134/Cienciadedados/grupo1")

def on_message(client, userdata, msg):
    global mqtt_data
    payload = msg.payload.decode('utf-8')
    mqtt_data = json.loads(payload)
    print(f"Received message: {mqtt_data}")

    # Adiciona o contexto da aplicação para a manipulação do banco de dados
    with app.app_context():
        try:
            temperatura = mqtt_data.get('temperature')
            pressao = mqtt_data.get('pressure')
            altitude = mqtt_data.get('altitude')
            umidade = mqtt_data.get('humidity')
            co2 = mqtt_data.get('CO2')
            timestamp_unix = mqtt_data.get('timestamp')

            if timestamp_unix is None:
                print("Timestamp não encontrado no payload")
                return

            # Converte timestamp Unix para datetime
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter timestamp: {str(e)}")
                return

            # Cria o objeto Leitura com os dados
            new_data = Leitura(
                temperatura=temperatura,
                pressao=pressao,
                altitude=altitude,
                umidade=umidade,
                co2=co2,
                data_hora=timestamp
            )

            # Adiciona o novo leitura ao banco de dados
            mybd.session.add(new_data)
            mybd.session.commit()
            print("Dados inseridos no banco de dados com sucesso")

            id_leitura = new_data.idLeitura

            # ***************************************************************
            # Início da nova lógica para chamar a API do Google e salvar os dados
            # ***************************************************************
            
            print("Chamando a API do Google Air Quality...")
            google_data, error = get_historical_air_quality(timestamp)
            
            if error:
                print(f"Erro ao buscar dados da API do Google: {error}")
            elif google_data:
                print("Dados da API do Google recebidos com sucesso. Processando...")
                
                # Assume que sempre haverá pelo menos um item em 'hoursInfo'
                info = google_data.get('hoursInfo')[0]
                
                # 1. Inserir dados na tabela tb_qualidade
                quality_index = next((item for item in info.get('indexes', []) if item.get('code') == 'uaqi'), None)
                if quality_index:
                    qualidade_data = Qualidade(
                        idLeitura=id_leitura,
                        aqi=quality_index.get('aqi'),
                        red=quality_index.get('color', {}).get('red'),
                        green=quality_index.get('color', {}).get('green'),
                        blue=quality_index.get('color', {}).get('blue'),
                        category=quality_index.get('category'),
                        poluenteDominante=quality_index.get('dominantPollutant')
                    )
                    mybd.session.add(qualidade_data)
                    print(f"Qualidade do ar inserida com sucesso (ID Leitura: {id_leitura})")

                # 2. Inserir dados na tabela tb_poluentes
                # A API do Google não retorna valores numéricos para poluentes, apenas os dados do poluente dominante.
                # Inserimos apenas o poluente dominante com valor NULL, pois o valor não é fornecido.
                pollutants = info.get('pollutants', [])

                # Iterando sobre a lista de poluentes
                for pollutant in pollutants:
                    try:
                        # Criando o objeto Poluentes para cada poluente
                        pollutant_data = Poluentes(
                            idLeitura=id_leitura,
                            nome=pollutant.get('displayName'),
                            valor=pollutant.get('concentration', {}).get('value'),
                            unidade=pollutant.get('concentration', {}).get('units'),
                        )

                        # Adicionando o poluente na sessão do banco de dados
                        mybd.session.add(pollutant_data)
                        mybd.session.commit()
                        print(f"Poluente '{pollutant.get('displayName')}' inserido com sucesso (ID Leitura: {id_leitura})")

                    except Exception as e:
                        # Caso ocorra um erro, ele será capturado e mostrado
                        print(f"Erro ao inserir poluente '{pollutant.get('displayName')}': {e}")


                # 3. Inserir dados na tabela tb_recomendacao
                recommendations = info.get('healthRecommendations', {})
                for publico_alvo, recomendacao in recommendations.items():
                    try:
                        # Criando o objeto Recomendacao para cada público-alvo
                        recomendacao_data = Recomendacao(
                            idLeitura=id_leitura,
                            publico_alvo=publico_alvo,
                            recomendacao=recomendacao
                        )
    
                        # Adicionando a recomendação na sessão do banco de dados
                        mybd.session.add(recomendacao_data)
                        mybd.session.commit()
                        print(f"Recomendação para '{publico_alvo}' inserida com sucesso (ID Leitura: {id_leitura})")
    
                    except Exception as e:
                        # Caso ocorra um erro, ele será capturado e mostrado
                        print(f"Erro ao inserir recomendação para '{publico_alvo}': {e}")


            # ***************************************************************
            # Fim da nova lógica
            # ***************************************************************

        except Exception as e:
            print(f"Erro ao processar os dados do MQTT: {str(e)}")
            mybd.session.rollback()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("test.mosquitto.org", 1883, 60)

def start_mqtt():
    mqtt_client.loop_start()

# ********************************************************************************************************

# Cadastrar
@app.route('/data', methods=['POST'])
def post_data():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Adiciona logs para depuração
        print(f"Dados recebidos: {data}")

        temperatura = data.get('temperatura')
        pressao = data.get('pressao')
        altitude = data.get('altitude')
        umidade = data.get('umidade')
        co2 = data.get('co2')
        timestamp_unix = data.get('data_hora')

        # Converte timestamp Unix para datetime
        try:
            timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
        except ValueError as e:
            print(f"Erro no timestamp: {str(e)}")
            return jsonify({"error": "Timestamp inválido"}), 400

        # Cria o objeto Leitura com os dados
        new_data = Leitura(
            temperatura=temperatura,
            pressao=pressao,
            altitude=altitude,
            umidade=umidade,
            co2=co2,
            data_hora=timestamp
        )

        # Adiciona o novo leitura ao banco de dados
        mybd.session.add(new_data)
        print("Adicionando o novo leitura")

        # Tenta confirmar a transação
        mybd.session.commit()
        print("Dados inseridos no banco de dados com sucesso")

        return jsonify({"message": "Data received successfully"}), 201

    except Exception as e:
        print(f"Erro ao processar a solicitação: {str(e)}")
        mybd.session.rollback()  # Reverte qualquer alteração em caso de erro
        return jsonify({"error": "Falha ao processar os dados"}), 500

# *************************************************************************************

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(mqtt_data)

class Leitura(mybd.Model):
    __tablename__ = 'tb_leituras'
    idLeitura = mybd.Column(mybd.Integer, primary_key=True, autoincrement=True)
    temperatura = mybd.Column(mybd.Numeric(10, 2))
    pressao = mybd.Column(mybd.Numeric(10, 2))
    altitude = mybd.Column(mybd.Numeric(10, 2))
    umidade = mybd.Column(mybd.Numeric(10, 2))
    co2 = mybd.Column(mybd.Numeric(10, 2))
    data_hora = mybd.Column(mybd.DateTime)

    def to_json(self):
        return {
            "idLeitura": self.idLeitura,
            "temperatura": float(self.temperatura),
            "pressao": float(self.pressao),
            "altitude": float(self.altitude),
            "umidade": float(self.umidade),
            "co2": float(self.co2),
            "data_hora": self.data_hora.strftime('%Y-%m-%d %H:%M:%S') if self.data_hora else None
        }

def gera_response(status, nome_do_conteudo, conteudo, mensagem=False):
    body = {}
    body[nome_do_conteudo] = conteudo
    if mensagem:
        body["mensagem"] = mensagem
    return Response(json.dumps(body), status=status, mimetype="application/json")

# =================================================================================== #
# Requisições API - Leituras
# =================================================================================== #

# GET
@app.route("/leitura", methods=["GET"])
def seleciona_leitura():
    leitura_objetos = Leitura.query.all()
    leitura_json = [leitura.to_json() for leitura in leitura_objetos]
    return gera_response(200, "leitura", leitura_json)

@app.route("/leitura/<idLeitura>", methods=["GET"])
def seleciona_leitura_id(idLeitura):
    leitura_objetos = Leitura.query.filter_by(id=idLeitura).first()
    if leitura_objetos:
        leitura_json = leitura_objetos.to_json()
        return gera_response(200, "leitura", leitura_json)
    else:
        return gera_response(404, "leitura", {}, "Leitura não encontrado")

# POST
@app.route("/leitura", methods=["POST"])
def criar_leitura():
    requisicao = request.get_json()
    try:
        leitura = Leitura(
            data_hora=requisicao["data_hora"],
            co2=requisicao["co2"],
            umidade=requisicao["umidade"],
            pressao=requisicao["pressao"],
            temperatura=requisicao["temperatura"],
            poeira_1=requisicao["poeira_1"],
            poeira_2=requisicao["poeira_2"],
            altitude=requisicao["altitude"],
        )
        mybd.session.add(leitura)
        mybd.session.commit()
        return gera_response(201, leitura.to_json(), "Leitura criada com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_response(400, {}, "Erro ao cadastrar leitura")

# DELETE
@app.route("/leitura/<idLeitura>", methods=["DELETE"])
def deleta_leitura(idLeitura):
    leitura_objetos = Leitura.query.filter_by(id=idLeitura).first()
    if leitura_objetos:
        try:
            mybd.session.delete(leitura_objetos)
            mybd.session.commit()
            return gera_response(200, "leitura", leitura_objetos.to_json(), "Deletado com sucesso")
        except Exception as e:
            print('Erro', e)
            mybd.session.rollback()
            return gera_response(400, "leitura", {}, "Erro ao deletar")
    else:
        return gera_response(404, "leitura", {}, "Leitura não encontrado")


# =================================================================================== #
# Modelo de dados - API Google Air Quality
# =================================================================================== #
class Poluentes(mybd.Model):
    __tablename__ = "tb_poluentes"
    idPoluente = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.Integer, mybd.ForeignKey('tb_leituras.idLeitura'), unique=True)
    nome = mybd.Column(mybd.String(255))
    valor = mybd.Column(mybd.String(255))
    unidade = mybd.Column(mybd.String(255))

    def to_json(self):
        return {
            "idPoluente": self.idPoluente,
            "idLeitura": self.idLeitura,
            "nome": self.nome,
            "valor": self.valor,
            "unidade": self.unidade,
            }

class Qualidade(mybd.Model):
    __tablename__ = 'tb_qualidade'
    idQualidade = mybd.Column(mybd.Integer, primary_key=True)
    idLeitura = mybd.Column(mybd.Integer, mybd.ForeignKey('tb_leituras.idLeitura'), unique=True)
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
    idLeitura = mybd.Column(mybd.Integer, mybd.ForeignKey('tb_leituras.idLeitura'), unique=True)
    publico_alvo = mybd.Column(mybd.String(255))
    recomendacao = mybd.Column(mybd.String(1000))
    
    def to_json(self):
        return {
            "idRecomendacao": self.idRecomendacao,
            "idLeitura": self.idLeitura,
            "publico_alvo": self.publico_alvo,
            "recomendacao": self.recomendacao
        }

# =================================================================================== #
# Requisições API - Poluentes
# =================================================================================== #

# GET 
@app.route("/poluente", methods=["GET"])
def get_poluentes():
    poluentes = Poluentes.query.all()
    poluentes_json = [p.to_json() for p in poluentes]
    return gera_response(200, poluentes_json)

@app.route("/poluente/<int:idPoluente>", methods=["GET"])
def get_poluente_id(idPoluente):
    poluente = Poluentes.query.filter_by(idPoluente=idPoluente).first()
    if not poluente:
        return gera_response(404, {}, "Poluente não encontrado")
    return gera_response(200, poluente.to_json())


# POST 
@app.route("/poluente", methods=["POST"])
def criar_poluente():
    requisicao = request.get_json()
    try:
        poluente = Poluentes(
            idLeitura=requisicao["idLeitura"],
            nome=requisicao["nome"],
            valor=requisicao["valor"],
            unidade=requisicao["unidade"],
        )
        mybd.session.add(poluente)
        mybd.session.commit()
        return gera_response(201, poluente.to_json(), "Poluente criado com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_response(400, {}, "Erro ao cadastrar poluente")


# PUT 
@app.route("/poluente/<int:idPoluente>", methods=["PUT"])
def atualizar_poluente(idPoluente):
    poluente = Poluentes.query.filter_by(idPoluente=idPoluente).first()
    if not poluente:
        return gera_response(404, {}, "Poluente não encontrado")

    requisicao = request.get_json()
    try:
        for campo in ["idLeitura", "nome", "valor", "unidade"]:
            if campo in requisicao:
                setattr(poluente, campo, requisicao[campo])

        mybd.session.commit()
        return gera_response(200, poluente.to_json(), "Poluente atualizado com sucesso")
    except Exception as e:
        print("Erro:", e)
        return gera_response(400, {}, "Erro ao atualizar poluente")

# =================================================================================== #
# Requisições API - Qualidade
# =================================================================================== #

# GET 
@app.route('/qualidade', methods=['GET'])
def get_qualidades():
    try:
        qualidades = Qualidade.query.all()
        if not qualidades:
            return gera_response(404, [], "Nenhuma qualidade encontrada.")
        
        qualidades_json = [q.to_json() for q in qualidades]
        return gera_response(200, qualidades_json)
    except Exception as e:
        print('Erro:', e)
        return gera_response(500, {}, "Ocorreu um erro interno no servidor.")
   
@app.route('/qualidade/<int:idQualidade>', methods=['GET'])
def get_qualidade_por_id(idQualidade):
    try:
        qualidade = Qualidade.query.get(idQualidade)
        if not qualidade:
            return gera_response(404, {}, f"Qualidade com ID {idQualidade} não encontrada.")
        return gera_response(200, qualidade.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_response(500, {}, "Ocorreu um erro interno no servidor.")

# POST
@app.route("/qualidade", methods=["POST"])
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
        return gera_response(201, nova_qualidade.to_json(), "Leitura de qualidade criado com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_response(400, {}, "Erro ao criar leitura de qualidade.")
    
# =================================================================================== #
# Requisições API - Recomendações
# =================================================================================== #

# GET 
@app.route('/recomendacao', methods=['GET'])
def get_recomendacoes():
    try:
        recomendacoes = Recomendacao.query.all()
        if not recomendacoes:
            return gera_response(404, [], "Nenhuma recomendação encontrada.")
        
        recomendacoes_json = [r.to_json() for r in recomendacoes]
        return gera_response(200, recomendacoes_json)
    except Exception as e:
        print('Erro:', e)
        return gera_response(500, {}, "Ocorreu um erro interno no servidor.")
    
@app.route('/recomendacao/<int:idRecomendacao>', methods=['GET'])
def get_recomendacao_por_id(idRecomendacao):
    try:
        recomendacao = Recomendacao.query.get(idRecomendacao)
        if not recomendacao:
            return gera_response(404,{}, f"Recomendação com ID {idRecomendacao} não encontrada.")
        return gera_response(200, recomendacao.to_json())
    except Exception as e:
        print('Erro:', e)
        return gera_response(500, {}, "Ocorreu um erro interno no servidor.")

# POST
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
        return gera_response(201, nova_recomendacao.to_json(), "Recomendação criada com sucesso.")
    except Exception as e:
        print('Erro:', e)
        return gera_response(400, {}, "Erro ao criar recomendação.")
    

















if __name__ == '__main__':
    with app.app_context():
        mybd.create_all()  # Cria as tabelas no banco de dados
    
    start_mqtt()
    app.run(port=5000, host='localhost', debug=True)