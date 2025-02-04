from flask import Flask, jsonify, request
from main import app, con

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
            'ano_publicado': livro[3]
        })

    return jsonify(mensagem="Lista de Livros", livros=livros_dic)

@app.route('/livro', methods=['POST'])
def livro_post():
    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicado = data.get('ano_publicado')
    cur = con.cursor()
    cur.execute("select 1 from LIVROS where titulo =?", (titulo,))
    if cur.fetchone():
        return jsonify(mensagem="Livro já cadastrado")
    else:
        cur.execute("INSERT INTO LIVROS (titulo, autor, ano_publicado) VALUES (?, ?, ?)",
                    (titulo, autor, ano_publicado))
        con.commit()
        con.close()

        return jsonify({
            'mensagem': 'Livro cadastrado com sucesso',
            'livro':{
                'titulo': titulo,
                'autor': autor,
                'ano_publicado': ano_publicado
            }
        })
@app.route('/livro/<int:id>', methods=['PUT'])
def livro_put(id):
    cur = con.cursor()
    cur.execute("select id_livro, titulo, autor, ano_publicado from livros where id_livro =?", (id,))
    livros_data = cur.fetchone()
    if not livros_data:
        cur.close()
        return jsonify(mensagem="Livro não encontrado")
    else:
        data = request.get_json()
        titulo = data.get('titulo')
        autor = data.get('autor')
        ano_publicado = data.get('ano_publicado')

        cur.execute("UPDATE LIVROS SET titulo = ?, autor = ?, ano_publicado = ? WHERE id_livro = ?",
                    (titulo, autor, ano_publicado, id))

        con.commit()
        cur.close()

        return jsonify({
            'mensagem': 'Livro atualizado com sucesso',
            'livro':{
                'id_livro': id,
                'titulo': titulo,
                'autor': autor,
                'ano_publicado': ano_publicado
            }
        })