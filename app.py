"""
Este código contém funções para interagir com o banco de dados SQLite.

"""
import sqlite3
from json import dumps, loads
from flask import Flask, request, jsonify, g
from Globals import DATABASE_NAME
# Adicionei o 'g' ele guarda o contexto da aplicação

app = Flask(__name__)


# def get_db_connection():
#     conn = None
#     try:
#         conn = sqlite3.connect(DATABASE_NAME)
#         conn.row_factory = sqlite3.Row
#     except sqlite3.Error as e:
#         print('Não foi possível conectar')

#     return conn

def get_db_connection():
    """
    gera um conexão com banco de dados, armazenando informações no contexto da aplicação

    - conn = getattr(g, '_database', None)
        Pega o '_database' do 'g', se n'ao tiver ele retorna none e conecta depois 
        (Fica no contexto)
        
    - conn = g._database = sqlite3.connect(DATABASE_NAME)
        Coloca no "_database" database do contexto a conexão com o sqlite3 e coloca a conexão em 
        contexto dentro do conn

    -conn.row_factory = sqlite3.Row
        O resultado da query vem em um objeto do sqlite3 que se comporta como dicionario
    
    """
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = g._database = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
    return conn

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
    return (jsonify({"versao": 1}), 200)


# def getUsuarios():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     resultset = cursor.execute('SELECT * FROM tb_usuario').fetchall()
#     usuarios = []
#     for linha in resultset:
#         id = linha[0]
#         nome = linha[1]
#         nascimento = linha[2]
#         # usuarioObj = Usuario(nome, nascimento)
#         usuarioDict = {
#             "id": id,
#             "nome": nome,
#             "nascimento": nascimento
#         }
#         usuarios.append(usuarioDict)
#     conn.close()
#     return usuarios


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
    resultset = query_db('SELECT * FROM tb_usuario')
    usuarios_json = [{"id":id,"nome":nome,"nascimento":nascimento}
                     for id, nome, nascimento in resultset]
    return loads(dumps(usuarios_json))


# def setUsuario(data):
#     # Criação do usuário.
#     nome = data.get('nome')
#     nascimento = data.get('nascimento')
#     # Persistir os dados no banco.
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         f'INSERT INTO tb_usuario(nome, nascimento) values ("{nome}", "{nascimento}")')
#     conn.commit()
#     id = cursor.lastrowid
#     data['id'] = id
#     conn.close()
#     # Retornar o usuário criado.
#     return data


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


# def getUsuarioById(id):
#     usuarioDict = None
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     linha = cursor.execute(
#         f'SELECT * FROM tb_usuario WHERE id = {id}').fetchone()
#     if linha is not None:
#         id = linha[0]
#         nome = linha[1]
#         nascimento = linha[2]
#         # usuarioObj = Usuario(nome, nascimento)
#         usuarioDict = {
#             "id": id,
#             "nome": nome,
#             "nascimento": nascimento
#         }
#     conn.close()
#     return usuarioDict


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

# def updateUsuario(id, data):
#     # Criação do usuário.
#     nome = data.get('nome')
#     nascimento = data.get('nascimento')
#     # Persistir os dados no banco.
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         'UPDATE tb_usuario SET nome = ?, nascimento = ? WHERE id = ?', (nome, nascimento, id))
#     conn.commit()

#     rowupdate = cursor.rowcount

#     conn.close()
#     # Retornar a quantidade de linhas.
#     return rowupdate

def update_usuario(user_id, data): #Alterado de updateUsuario para update_usuario
    """
    Função utilizada para modificar um usuario apartir do id
    """
    linhas_modificadas = query_db_with_commit( '''UPDATE tb_usuario SET nome = ?, nascimento
                       = ? WHERE id = ?''',(data.get('nome'),data.get('nascimento'), user_id))
    return linhas_modificadas

def delete_usuario(user_id): #Alterado de deleteUsuario para delete_usuario
    """
    Função que deleta um usuario apartir do id
    """
    linhas_modificadas = query_db_with_commit( 'DELETE FROM tb_usuario WHERE id = ?',(user_id,))
    return linhas_modificadas

@app.route("/usuarios/<int:id>", methods=['GET', 'DELETE', 'PUT'])
def usuario(user_id):
    """
    Função que controla a chamada das funções 
    get_usuario_by_id, update_usuario e delete_usuario
    apartir do metodo que é utilizado na requisição
    """
    if request.method == 'GET':
        response_usuario = get_usuario_by_id(id)
        if usuario is not None:
            return jsonify(response_usuario), 200
    elif request.method == 'PUT':
        # Recuperar dados da requisição: json.
        data = request.json
        rowupdate = update_usuario(user_id, data)
        if rowupdate != 0:
            return (data, 201)
        return (data, 304)
    elif request.method == 'DELETE':
        linhas_modificadas = delete_usuario(user_id)
        if linhas_modificadas:
            return {"message": f"{linhas_modificadas}"}, 200
    return {},404
