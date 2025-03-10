from flask import Flask, jsonify, request
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
import re
import jwt


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


@app.route('/livro', methods=['POST'])
def livro_post():
    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicado = data.get('ano_publicado')

    cur = con.cursor()
    cur.execute("SELECT 1 FROM livros WHERE titulo = ?", (titulo,))

    if cur.fetchone():
        return jsonify(mensagem="Livro já cadastrado"), 400

    cur.execute("INSERT INTO livros (titulo, autor, ano_publicado) VALUES (?, ?, ?)",
                (titulo, autor, ano_publicado))
    con.commit()

    return jsonify({
        'mensagem': 'Livro cadastrado com sucesso',
        'livro': {'titulo': titulo, 'autor': autor, 'ano_publicado': ano_publicado}
    }), 201


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
    cur = con.cursor()
    cur.execute("SELECT senha FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    senha = cur.fetcheone
    cur.close()

    if not senha:
        return jsonify({'error': "Email ou senha inválidos"}), 401
    senha_hash = senha[0]

    if not check_password_hash(senha_hash, senha):
        return jsonify({'error': "Email ou senha inválidos"}), 401

    return jsonify({'mensagem': "Login realizado com sucesso"})