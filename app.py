import sqlite3
# Adicionei o 'g' ele guarda o contexto da aplicação
from flask import Flask, request, jsonify, g
from Globals import DATABASE_NAME
from json import dumps, loads

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
    conn = getattr(g, '_database', None) # Pega o '_database' do 'g', se n'ao tiver ele retorna none e conecta depois (Fica no contexto)
    if conn is None:
        conn = g._database = sqlite3.connect(DATABASE_NAME) #Coloca no "_database" database do contexto a conexão com o sqlite3 e coloca a conexão em contexto dentro do conn
        conn.row_factory = sqlite3.Row # O resultado da query vem em um objeto do sqlite3 que se comporta como dicionario
    return conn

@app.teardown_appcontext #Executa a função 'close_connection' quando o contexto é encerrado
def close_connection(exception):
    db = getattr(g, '_database', None) #Pega a conexão que ta no contexto e fecha ela
    if db is not None:
        db.close()

def query_db(query, args=(), one=False): #Recebe a query e seus argumentos como parametro, o "one" se for true ele retorna apenas um item, caso false ele retorna uma lista se houver
    cur = get_db_connection().execute(query, args)
    rv = cur.fetchall() #Pega todos os itens do resultado
    cur.close() #Fecha a conexão
    return (rv[0] if rv else None) if one else rv #Logica por tras do parametro "one" se for true ele retorna apenas o primeiro item da lista, se false ele retorna todos

def query_db_with_commit(query, args=()): #Fiz uma modificao para aceitar commit, pois o query_db do site serve para select apenas
    cur = get_db_connection()
    linhas_afetadas = cur.cursor().execute(query, args).rowcount #Executa a query e conta as linhas modificadas
    cur.commit() #Confirma a query
    cur.close() #Fecha a conexão
    return f"Alterado: {linhas_afetadas} linha(s)"

@app.route("/")
def index():
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


def getUsuarios():
    resultset = query_db('SELECT * FROM tb_usuario')
    usuarios = [{"id":id,"nome":nome,"nascimento":nascimento} for id, nome, nascimento in resultset]
    return loads(dumps(usuarios)) # dumps serializa em um string json e o loads desserializa, não é necessario fazer isso pois o json_usuarios já retorna uma lista de jsons


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


def setUsuario(data):
    linhas_modificadas = query_db_with_commit('INSERT INTO tb_usuario(nome, nascimento) values (?, ?)', (data.get('nome'), data.get('nascimento')))
    return linhas_modificadas

@app.route("/usuarios", methods=['GET', 'POST'])
def usuarios():
    if request.method == 'GET':
        # Listagem dos usuários
        usuarios = getUsuarios()
        return jsonify(usuarios), 200
    elif request.method == 'POST':
        # Recuperar dados da requisição: json.
        data = request.json
        data = setUsuario(data)
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


def getUsuarioById(id):
    resultado = query_db('SELECT * FROM tb_usuario WHERE id = ?', (id,), True) #Passo o select e o argumento id, o 'True' é para a função retornar apenas um elemento, equivalente ao fetchone()
    if resultado is not None:
        json = {"id": resultado[0],"nome": resultado[1],"nascimento": resultado[2]}
        return json
    else:
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

def updateUsuario(id, data):
    linhas_modificadas = query_db_with_commit( 'UPDATE tb_usuario SET nome = ?, nascimento = ? WHERE id = ?',(data.get('nome'),data.get('nascimento'), id))
    return linhas_modificadas

def deleteUsuario(id):
    linhas_modificadas = query_db_with_commit( 'DELETE FROM tb_usuario WHERE id = ?',(id,))
    return linhas_modificadas
  
@app.route("/usuarios/<int:id>", methods=['GET', 'DELETE', 'PUT'])
def usuario(id):
    if request.method == 'GET':
        usuario = getUsuarioById(id)
        if usuario is not None:
            return jsonify(usuario), 200
        else:
            return {}, 404
    elif request.method == 'PUT':
        # Recuperar dados da requisição: json.
        data = request.json
        rowupdate = updateUsuario(id, data)
        if rowupdate != 0:
            return (data, 201)
        else:
            return (data, 304)
    elif request.method == 'DELETE':
        linhas_modificadas = deleteUsuario(id)
        if linhas_modificadas:
            return {"message": f"{linhas_modificadas}"}, 200 
