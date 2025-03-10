from flask import Flask, jsonify, request
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
import re
import jwt

app.config.from_pyfile('config.py')
senha_secreta = app.config['SECRET_KEY']
def generate_token(user_id):
    payload = {'id_usuario': user_id}
    token = jwt.encode(payload, senha_secreta, algorithm='HS256')
    return token
def remover_bearer(token):

    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token
@app.route('/livro', methods=['GET'])
def livro():
    cur = con.cursor()
    cur.execute("SELECT id_livro, titulo, autor, ano_publicado FROM livros")
    livros = cur.fetchall()
    livros_dic = []
    for livro in livros:
        livros_dic.append({
            'id_livro': livro[0],
            'titulo': livro[1],
            'autor': livro[2],
            'ano_publicado': livro[3],})
    return jsonify(mensagem="Lista de Livros", livros=livros_dic)


@app.route('/livros', methods=['POST'])
def criar_livro():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'mensagem': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'mensagem': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensagem': 'Token inválido'}), 401

    data = request.get_json()

    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM livros WHERE TITULO = ?", (titulo,))
    if cursor.fetchone():
        return jsonify({"error": "Livro já cadastrado"}), 400

    cursor.execute("INSERT INTO livros (TITULO, AUTOR, ANO_PUBLICACAO) VALUES (?, ?, ?)",
                   (titulo, autor, ano_publicacao))
    con.commit()
    cursor.close()

    return jsonify({
        'message': "Livro cadastrado com sucesso!",
        'livro': {
            'titulo': titulo,
            'autor': autor,
            'ano_publicacao': ano_publicacao
        }
    }), 201


@app.route('/livro_imagem', methods=['POST'])
def livro_imagem():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'mensagem': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'mensagem': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensagem': 'Token inválido'}), 401

    if 'imagem' not in request.files:
        return jsonify({'mensagem': 'Nenhum arquivo enviado'}), 400

    arquivo = request.files['imagem']
    if arquivo.filename == '':
        return jsonify({'mensagem': 'Nome de arquivo inválido'}), 400

    return jsonify({'mensagem': 'Imagem salva com sucesso', 'caminho': caminho}), 201
@app.route('/livro/<int:id>', methods=['PUT'])
def livro_put(id):
    cur = con.cursor()
    cur.execute("SELECT id_livro FROM livros WHERE id_livro = ?", (id,))

    if not cur.fetchone():
        return jsonify(mensagem="Livro não encontrado"), 404

    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicado = data.get('ano_publicado')

    cur.execute("UPDATE livros SET titulo = ?, autor = ?, ano_publicado = ? WHERE id_livro = ?",
                (titulo, autor, ano_publicado, id))
    con.commit()

    return jsonify({
        'mensagem': 'Livro atualizado com sucesso',
        'livro': {'id_livro': id, 'titulo': titulo, 'autor': autor, 'ano_publicado': ano_publicado}
    })


@app.route('/livro/<int:id>', methods=['DELETE'])
def livro_delete(id):
    cur = con.cursor()
    cur.execute("SELECT 1 FROM livros WHERE id_livro = ?", (id,))

    if not cur.fetchone():
        return jsonify({'Error': "Livro não encontrado"}), 404

    cur.execute("DELETE FROM livros WHERE id_livro = ?", (id,))
    con.commit()

    return jsonify({'message': "Livro excluído com sucesso!", 'id_livro': id})


@app.route('/usuario', methods=['GET'])
def usuario():
    cur = con.cursor()
    cur.execute("SELECT id_usuario, nome, email FROM usuarios")
    usuarios = cur.fetchall()
    usuarios_dic = []
    for usuario in usuarios:
        usuarios_dic.append({
            'id_usuario': usuario[0],
            'nome': usuario[1],
            'email': usuario[2]
        })

    return jsonify(mensagem="Lista de usuários", usuarios=usuarios_dic)


@app.route('/usuario', methods=['POST'])
def usuario_post():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    # Validação da senha
    if (len(senha) < 8 or not re.search(r"[A-Z]", senha) or not re.search(r"[a-z]", senha) or
            not re.search(r"\d", senha) or not re.search(r"[@$!%*?&]", senha)):
        return jsonify(
            mensagem="A senha deve ter pelo menos 8 caracteres, uma letra maiúscula, uma letra minúscula, um número e um caractere especial."), 400

    senha = generate_password_hash(senha).decode('utf-8')

    cur = con.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE nome = ?", (nome,))

    if cur.fetchone():
        return jsonify(mensagem="Usuário já cadastrado"), 400

    cur.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
    con.commit()

    return jsonify({
        'mensagem': 'Usuário cadastrado com sucesso',
        'usuario': {'nome': nome, 'email': email, 'senha': senha}
    }), 201


@app.route('/usuario/<int:id>', methods=['PUT'])
def usuario_put(id):
    cur = con.cursor()
    cur.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = ?", (id,))

    if not cur.fetchone():
        return jsonify(mensagem="Usuário não encontrado"), 404

    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    cur.execute("UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id_usuario = ?",
                (nome, email, senha, id))
    con.commit()

    return jsonify({
        'mensagem': 'Usuário atualizado com sucesso',
        'usuario': {'id_usuario': id, 'nome': nome, 'email': email}
    })


@app.route('/usuario/<int:id>', methods=['DELETE'])
def usuario_delete(id):
    cur = con.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE id_usuario = ?", (id,))

    if not cur.fetchone():
        return jsonify({'Error': "Usuário não encontrado"}), 404

    cur.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id,))
    con.commit()

    return jsonify({'message': "Usuário excluído com sucesso!", 'id_usuario': id})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    cursor = con.cursor()

    cursor.execute("SELECT senha, id_usuario FROM usuarios WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    cursor.close()
    if not resultado:
        return jsonify({"error": "Usuário não encontrado"}), 404
    senha_hash = resultado[0]
    id_usuario = resultado[1]

    if email and check_password_hash(senha_hash, senha):
        token = generate_token(id_usuario)
        return jsonify({'mensagem': 'Login com sucesso', 'token': token}), 200
    else:
        return jsonify({'mensagem': 'Email ou senha inválido'}), 401
