from flask import Flask, jsonify
from main import app, con

app.route('/livro', methods=['GET'])
def livros():
    cursor = con.cursor()
    cursor.execute("select id_livro, titulo, autor, ano_publicado from Livros")
    livros = cursor.fetchall()
    livros_dic = []
    for livro in livros:
        livros_dic.append({
            'id_livro': livro[0],
            'titulo': livro[1],
            'autor': livro[2],
            'ano_publicado': livro[3]
        })
        return jsonify(mensagem= 'lista de livros', livros=livros_dic)
