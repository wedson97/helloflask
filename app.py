"""
Este código contém funções para interagir com o banco de dados SQLite.

"""
from json import dumps, loads
from flask import Flask, request, jsonify
# Adicionei o 'g' ele guarda o contexto da aplicação

from helpers.logging import logger
# Logging


from helpers.database import get_db_connections

app = Flask(__name__)



@app.teardown_appcontext #Executa a função 'close_connection' quando o contexto é encerrado
def close_connection(exception):
    """
    É executado quando o contexto é encerrado

    - db = getattr(g, '_database', None):
        Pega a conexão que ta no contexto

    - db.close():
        Fecha a conexão
    """
    db = getattr(g, '_database', None) #Pega a conexão que ta no contexto e fecha ela
    if db is not None:
        db.close()
    if exception:
        print(exception)

def query_db(query, args=(), one=False):
    """
    Pega a conexão com o bd, executa a query e fecha a conexão depois

    Recebe a query e seus argumentos como parametro, o "one" se for true 
    ele retorna apenas um item, caso false ele retorna uma lista se houver

    - cur = get_db_connection().execute(query, args):
        Pega a conexão

    - rv = cur.fetchall():
        Pega todos os itens do resultado
    
    - cur.close():
        Fecha a conexão

    - return (rv[0] if rv else None) if one else rv:
        Logica por tras do parametro "one" se for true ele retorna apenas o 
        primeiro item da lista, se false ele retorna todos

    """
    cur = get_db_connection().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def query_db_with_commit(query, args=()):
    """
    É uma versão modificada da funcão query_db, pois essa aceita query que tem commit

    - cur = get_db_connection():
        Pega conexão
    
    - linhas_afetadas = cur.cursor().execute(query, args).rowcount:
        Executa a query e conta as linhas modificadas

    - cur.commit():
        Confirma a query

    - cur.close():
        Fecha a conexão
    """
    cur = get_db_connection()
    linhas_afetadas = cur.cursor().execute(query, args).rowcount
    cur.commit()
    cur.close()
    return f"Alterado: {linhas_afetadas} linha(s)"

@app.route("/")
def index():
    """
    Função padrão do flask, retorna a versão do código
    """
    logger.info("Rota padão")
    return (jsonify({"versao": 1}), 200)


def get_usuarios(): # Alterado de getUsuarios para get_usuarios
    """
    Função que pega todos os usuarios
    - resultset = query_db('SELECT * FROM tb_usuario'):
        Usa o query_db, que retorna todos os itens de tb_usuario

    - usuarios_json = [{"id":id,"nome":nome,"nascimento":nascimento}
    for id, nome, nascimento in resultset]:
        Cria uma lista de jsons com todos os itens retornados pelo query_db
    
    - loads(dumps(usuarios_json)):
        dumps serializa em um string json e o loads desserializa, não é 
        necessario fazer isso pois o json_usuarios já retorna uma lista de jsons
    """
    resultset = query_db('SELECT * FROM tb_usuario WHERE deleted_at is null ')
    usuarios_json = [{"id":id,"nome":nome,"nascimento":nascimento,
                    "created_at":created_at,"deleted_at":deleted_at}
                     for id, nome, nascimento,created_at,deleted_at in resultset]
    return loads(dumps(usuarios_json))

def set_usuario(data): #Alterado de setUsuario para set_usuario
    """
    Função utilizada para fazer um post de um novo usuario

    - linhas_modificadas = query_db_with_commit('INSERT INTO tb_usuario(nome, nascimento)
    values (?, ?)', (data.get('nome'), data.get('nascimento'))):
        Usa a função query_db_with_commit, pois nesse caso é necessario um commit
        Ela retorna o número de linhas modificadas com a query
    """
    linhas_modificadas = query_db_with_commit('''INSERT INTO tb_usuario(nome, nascimento)
                        values (?, ?)''',(data.get('nome'), data.get('nascimento')))
    return linhas_modificadas

@app.route("/usuarios", methods=['GET', 'POST'])
def usuarios():
    """
    Função que chama as funções get_usuarios ou set_usuario,
    dependendo de qual metodo for utilizado

    """
    if request.method == 'GET':
        # Listagem dos usuários
        response_usuarios = get_usuarios()
        return jsonify(response_usuarios), 200
        # Recuperar dados da requisição: json.
    data = request.json
    data = set_usuario(data)
    return jsonify(data), 201


def get_usuario_by_id(user_id): #Alterado de getUsuarioById para get_usuario_by_id
    """
    Função que pega um unico usuario, apartir do id

    - resultado = query_db('SELECT * FROM tb_usuario WHERE id = ?', (user_id,), True):
        Passo o select e o argumento id, o 'True' é para a função retornar apenas um 
        elemento, equivalente ao fetchone()
    """
    resultado = query_db('SELECT * FROM tb_usuario WHERE id = ?', (user_id,), True)
    if resultado is not None:
        json = {"id": resultado[0],"nome": resultado[1],"nascimento": resultado[2]}
        return json
    return None

def update_usuario(user_id, data): #Alterado de updateUsuario para update_usuario
    """
    Função utilizada para modificar um usuario apartir do id
    """
    linhas_modificadas = query_db_with_commit( '''UPDATE tb_usuario SET nome = ?, nascimento
                       = ? WHERE id = ?''',(data.get('nome'),data.get('nascimento'), user_id))
    return linhas_modificadas

def delete_usuario_fisico(user_id): #Alterado de deleteUsuario para delete_usuario
    """
    Função que deleta um usuario apartir do id
    """
    linhas_modificadas = query_db_with_commit( 'DELETE FROM tb_usuario WHERE id = ?',(user_id,))
    return linhas_modificadas


def delete_usuario_logico(user_id): #Alterado de deleteUsuario para delete_usuario
    """
    Função que deleta um usuario apartir do id
    """
    linhas_modificadas = query_db_with_commit( '''UPDATE tb_usuario SET
                       deleted_at = CURRENT_TIMESTAMP WHERE id = ?''',(user_id,))
    return linhas_modificadas

@app.route("/usuarios/<int:user_id>", methods=['GET', 'DELETE', 'PUT'])
def usuario(user_id):
    """
    Função que controla a chamada das funções 
    get_usuario_by_id, update_usuario e delete_usuario
    apartir do metodo que é utilizado na requisição
    """
    if request.method == 'GET':
        response_usuario = get_usuario_by_id(user_id)
        if response_usuario is not None:
            return jsonify(response_usuario), 200
    elif request.method == 'PUT':
        # Recuperar dados da requisição: json.
        data = request.json
        rowupdate = update_usuario(user_id, data)
        if rowupdate != 0:
            return (data, 201)
        return (data, 304)
    elif request.method == 'DELETE':
        linhas_modificadas = delete_usuario_fisico(user_id)
        if linhas_modificadas:
            return {"message": f"{linhas_modificadas}"}, 200
    return {},404

@app.route("/usuarios/logico/<int:user_id>", methods=['DELETE'])
def delete_usuario_com_metodo_logico(user_id):
    """
        Função que controla a chamada de
        deletar um usuario na forma logica
    """
    linhas_modificadas = delete_usuario_logico(user_id)
    if linhas_modificadas:
        return {"message": f"{linhas_modificadas}"}, 200
    return {},404
