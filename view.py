from flask import Flask, jsonify, request, send_file
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_cors import CORS
import jwt
import os
import re
from fpdf import FPDF
from main import app, con

app.config.from_pyfile('config.py')
CORS(app)
senha_secreta = app.config['SECRET_KEY']
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']

def generate_token(user_id):
    payload = {'id_usuario': user_id}
    return jwt.encode(payload, senha_secreta, algorithm='HS256')

def remover_bearer(token):
    return token[len('Bearer '):] if token.startswith('Bearer ') else token

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    ano_publicacao = request.form.get('ano_publicacao')
    imagem = request.files.get('imagem')
    cursor.execute(
        "INSERT INTO livros (TITULO, AUTOR, ANO_PUBLICACAO) VALUES (?, ?, ?) RETURNING ID_livro",
        (titulo, autor, ano_publicacao)
    )
    livro_id = cursor.fetchone()[0]
    con.commit()
    if imagem:
        nome_imagem = f"{livro_id}.jpeg"
        pasta_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Livros")
        os.makedirs(pasta_destino, exist_ok=True)
        imagem_path = os.path.join(pasta_destino, nome_imagem)
        imagem.save(imagem_path)
    

# ======================================
# Rotas de Livros

@app.route('/livros', methods=['GET'])
def listar_livros():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
        livros = cur.fetchall()
        livros_dic = [{
            'id_livro': livro[0],
            'titulo': livro[1],
            'autor': livro[2],
            'ano_publicacao': livro[3]
        } for livro in livros]
        return jsonify(livros=livros_dic, mensagem="Lista de Livros")
    finally:
        cur.close()

@app.route('/livros', methods=['POST'])
def criar_livro():
    try:
        token = remover_bearer(request.headers.get('Authorization', ''))
        if not token:
            return jsonify({'mensagem': 'Token necessário'}), 401
            
        jwt.decode(token, senha_secreta, algorithms=['HS256'])
        
        data = request.form.to_dict()
        titulo = data.get('titulo')
        autor = data.get('autor')
        ano_publicacao = data.get('ano_publicacao')
        imagem = request.files.get('imagem')

        if not all([titulo, autor, ano_publicacao]):
            return jsonify({"error": "Campos obrigatórios faltando: titulo, autor, ano_publicacao"}), 400

        if imagem and imagem.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            filename = imagem.filename
            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return jsonify({'error': 'Tipo de arquivo não permitido. Use PNG, JPG, JPEG ou GIF'}), 400

        cur = con.cursor()
        cur.execute("SELECT 1 FROM livros WHERE titulo = ?", (titulo,))
        if cur.fetchone():
            return jsonify({"error": "Livro já cadastrado"}), 400

        cur.execute("""
            INSERT INTO livros (titulo, autor, ano_publicacao)
            VALUES (?, ?, ?) RETURNING id_livro
        """, (titulo, autor, ano_publicacao))
        livro_id = cur.fetchone()[0]
        con.commit()

        if imagem and imagem.filename:
            pasta_destino = os.path.join(UPLOAD_FOLDER, "Livros")
            os.makedirs(pasta_destino, exist_ok=True)
            imagem.save(os.path.join(pasta_destino, f"{livro_id}.jpeg"))

        return jsonify({
            'mensagem': 'Livro cadastrado com sucesso!',
            'livro_id': livro_id
        }), 201
    except jwt.PyJWTError:
        return jsonify({'mensagem': 'Token inválido ou expirado'}), 401
    finally:
        cur.close()

@app.route('/livros/<int:id>', methods=['PUT'])
def atualizar_livro(id):
    try:
        token = remover_bearer(request.headers.get('Authorization', ''))
        if not token:
            return jsonify({'mensagem': 'Token necessário'}), 401
        jwt.decode(token, senha_secreta, algorithms=['HS256'])
        
        data = request.get_json()
        data = request.get_json()
        cur = con.cursor()
        
        cur.execute("SELECT 1 FROM livros WHERE id_livro = ?", (id,))
        if not cur.fetchone():
            return jsonify(mensagem="Livro não encontrado"), 404

        cur.execute("""
            UPDATE livros 
            SET titulo = ?, autor = ?, ano_publicacao = ?
            WHERE id_livro = ?
        """, (data['titulo'], data['autor'], data['ano_publicacao'], id))
        con.commit()
        
        return jsonify({'mensagem': 'Livro atualizado com sucesso'})
    finally:
        cur.close()

@app.route('/livros/<int:id>', methods=['DELETE'])
def deletar_livro(id):
    try:
        token = remover_bearer(request.headers.get('Authorization', ''))
        if not token:
            return jsonify({'mensagem': 'Token necessário'}), 401
        jwt.decode(token, senha_secreta, algorithms=['HS256'])
        
        cur = con.cursor()
        cur.execute("SELECT 1 FROM livros WHERE id_livro = ?", (id,))
        if not cur.fetchone():
            return jsonify(error="Livro não encontrado"), 404
            
        cur.execute("DELETE FROM livros WHERE id_livro = ?", (id,))
        con.commit()
        return jsonify({'mensagem': 'Livro excluído com sucesso'})
    finally:
        cur.close()

# ======================================
# Rotas de Usuários


@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_usuario, nome, email FROM usuarios")
        usuarios = [{
            'id_usuario': usuario[0],
            'nome': usuario[1],
            'email': usuario[2]
        } for usuario in cur.fetchall()]
        return jsonify(usuarios=usuarios, mensagem="Lista de Usuários")
    finally:
        cur.close()

@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        data = request.get_json()
        senha = data['senha']

        # Validação de senha
        if (len(senha) < 8 or
            not re.search(r"[A-Z]", senha) or
            not re.search(r"[a-z]", senha) or
            not re.search(r"\d", senha) or
            not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", senha)):
            return jsonify(
                mensagem="Senha deve conter 8+ caracteres, maiúscula, minúscula, número e símbolo."
            ), 400

        # Verificar e-mail único
        cur = con.cursor()
        cur.execute("SELECT 1 FROM usuarios WHERE email = ?", (data['email'],))
        if cur.fetchone():
            return jsonify(mensagem="E-mail já cadastrado"), 400

        # Criar usuário
        senha_hash = generate_password_hash(senha).decode('utf-8')
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha)
            VALUES (?, ?, ?)
        """, (data['nome'], data['email'], senha_hash))
        con.commit()
        
        return jsonify({'mensagem': 'Usuário criado com sucesso'}), 201
    finally:
        cur.close()

@app.route('/usuarios/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    try:
        token = remover_bearer(request.headers.get('Authorization', ''))
        if not token:
            return jsonify({'mensagem': 'Token necessário'}), 401
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        usuario_id = payload['id_usuario']
        cur = con.cursor()
        cur.execute("SELECT 1 FROM usuarios WHERE id_usuario = ?", (id,))
        if not cur.fetchone():
            return jsonify(error="Usuário não encontrado"), 404
            
        cur.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id,))
        con.commit()
        return jsonify({'mensagem': 'Usuário excluído com sucesso'})
    finally:
        cur.close()

# ======================================
# Autenticação


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        cur = con.cursor()
        cur.execute("""
            SELECT senha, id_usuario 
            FROM usuarios 
            WHERE email = ?
        """, (data['email'],))
        
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({"mensagem": "Credenciais inválidas"}), 401
            
        senha_hash, id_usuario = resultado
        if check_password_hash(senha_hash, data['senha']):
            return jsonify({
                'mensagem': 'Login bem-sucedido',
                'token': generate_token(id_usuario)
            }), 200
            
        return jsonify({'mensagem': 'Credenciais inválidas'}), 401
    finally:
        cur.close()

# ======================================
#Relatório PDF

@app.route('/livros/relatorio', methods=['GET'])
def gerar_relatorio():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
        livros = cur.fetchall()
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(200, 10, "Relatorio de Livros", ln=True, align='C')
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", size=12)
        for livro in livros:
            pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)
            
        contador_livros = len(livros)
        pdf.ln(10)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')

        pdf_path = "relatorio_livros.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')
    finally:
        cur.close()