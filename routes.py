from flask import render_template, request, redirect, url_for, jsonify, Response
from app import app, db
from models import Item, Categoria, Subcategoria, Localizacao, Historico
from datetime import datetime
import csv
import io
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'imagens')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    itens      = Item.query.filter_by(item_pai_id=None).all()
    categorias = Categoria.query.all()
    return render_template('index.html', itens=itens, categorias=categorias)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    categorias    = Categoria.query.all()
    subcategorias = Subcategoria.query.all()
    itens_pai     = Item.query.filter_by(item_pai_id=None).order_by(Item.nome).all()

    if request.method == 'POST':
        localizacao = Localizacao(
            ambiente        = request.form.get('ambiente') or None,
            codigo_etiqueta = request.form.get('codigo_etiqueta') or None
        )
        db.session.add(localizacao)
        db.session.flush()

        imagem_url = None
        arquivo = request.files.get('imagem')
        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(UPLOAD_FOLDER, filename))
            imagem_url = filename

        novo_item = Item(
            nome               = request.form['nome'],
            descricao          = request.form.get('descricao'),
            categoria_id       = request.form.get('categoria_id') or None,
            subcategoria_id    = request.form.get('subcategoria_id') or None,
            condicao           = request.form.get('condicao'),
            disponibilidade    = request.form.get('disponibilidade'),
            patrimonio_utfpr   = request.form.get('patrimonio_utfpr') == 'sim',
            patrimonio_escola  = request.form.get('patrimonio_escola') == 'sim',
            nome_escola        = request.form.get('nome_escola') or None,
            localizacao_id     = localizacao.id,
            unidade_medida     = request.form.get('unidade_medida'),
            quantidade         = request.form.get('quantidade') or 1,
            imagem_url         = imagem_url,
            item_pai_id        = request.form.get('item_pai_id') or None
        )
        db.session.add(novo_item)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('cadastrar.html', categorias=categorias, subcategorias=subcategorias, itens_pai=itens_pai)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    item          = Item.query.get_or_404(id)
    categorias    = Categoria.query.all()
    subcategorias = Subcategoria.query.filter_by(categoria_id=item.categoria_id).all() if item.categoria_id else []
    itens_pai     = Item.query.filter(Item.id != id, Item.item_pai_id == None).order_by(Item.nome).all()

    if request.method == 'POST':
        item.nome              = request.form['nome']
        item.descricao         = request.form.get('descricao')
        item.categoria_id      = request.form.get('categoria_id') or None
        item.subcategoria_id   = request.form.get('subcategoria_id') or None
        item.condicao          = request.form.get('condicao')
        item.disponibilidade   = request.form.get('disponibilidade')
        item.patrimonio_utfpr  = request.form.get('patrimonio_utfpr') == 'sim'
        item.patrimonio_escola = request.form.get('patrimonio_escola') == 'sim'
        item.nome_escola       = request.form.get('nome_escola') or None
        item.unidade_medida    = request.form.get('unidade_medida')
        item.quantidade        = request.form.get('quantidade') or 1
        item.item_pai_id       = request.form.get('item_pai_id') or None

        arquivo = request.files.get('imagem')
        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(UPLOAD_FOLDER, filename))
            item.imagem_url = filename

        if item.localizacao:
            item.localizacao.ambiente        = request.form.get('ambiente') or None
            item.localizacao.codigo_etiqueta = request.form.get('codigo_etiqueta') or None
        else:
            loc = Localizacao(
                ambiente        = request.form.get('ambiente') or None,
                codigo_etiqueta = request.form.get('codigo_etiqueta') or None
            )
            db.session.add(loc)
            db.session.flush()
            item.localizacao_id = loc.id

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('editar.html', item=item, categorias=categorias, subcategorias=subcategorias, itens_pai=itens_pai)

@app.route('/item/<int:id>')
def detalhe_item(id):
    item = Item.query.get_or_404(id)
    return render_template('detalhe.html', item=item)

@app.route('/buscar')
def buscar():
    termo      = request.args.get('q', '')
    categorias = Categoria.query.all()
    resultados = Item.query.filter(Item.nome.contains(termo)).all()
    return render_template('index.html', itens=resultados, categorias=categorias)

@app.route('/categoria/<int:categoria_id>')
def por_categoria(categoria_id):
    categorias      = Categoria.query.all()
    categoria_atual = Categoria.query.get(categoria_id)
    subcategoria_id = request.args.get('subcategoria_id', type=int)

    if subcategoria_id:
        itens = Item.query.filter_by(categoria_id=categoria_id, subcategoria_id=subcategoria_id).all()
    else:
        itens = Item.query.filter_by(categoria_id=categoria_id).all()

    return render_template('index.html',
        itens=itens,
        categorias=categorias,
        categoria_atual=categoria_atual,
        subcategoria_id_atual=subcategoria_id
    )

@app.route('/item/deletar/<int:id>', methods=['GET', 'POST'])
def deletar_item(id):
    item = Item.query.get_or_404(id)
    motivo = request.form.get('motivo', '') if request.method == 'POST' else request.args.get('motivo', '')

    historico = Historico(
        nome_item         = item.nome,
        descricao         = item.descricao,
        categoria         = item.categoria.nome if item.categoria else '—',
        subcategoria      = item.subcategoria.nome if item.subcategoria else '—',
        condicao          = item.condicao,
        quantidade        = item.quantidade,
        unidade           = item.unidade_medida,
        patrimonio_utfpr  = item.patrimonio_utfpr,
        patrimonio_escola = item.patrimonio_escola,
        nome_escola       = item.nome_escola,
        motivo            = motivo
    )
    db.session.add(historico)

    if item.localizacao_id:
        loc = Localizacao.query.get(item.localizacao_id)
        if loc:
            db.session.delete(loc)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/historico')
def historico():
    registros = Historico.query.order_by(Historico.data_exclusao.desc()).all()
    return render_template('historico.html', registros=registros)

@app.route('/exportar')
def exportar():
    categoria_id = request.args.get('categoria_id', type=int)
    condicao     = request.args.get('condicao', '')

    query = Item.query
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if condicao:
        query = query.filter_by(condicao=condicao)
    itens = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Item Pai', 'Categoria', 'Subcategoria', 'Condição', 'Disponibilidade',
                     'Quantidade', 'Unidade', 'Patrimônio UTFPR', 'Patrimônio Escola',
                     'Nome da Escola', 'Ambiente', 'Etiqueta', 'Data Cadastro'])

    for item in itens:
        writer.writerow([
            item.nome,
            item.item_pai.nome if item.item_pai else '—',
            item.categoria.nome if item.categoria else '—',
            item.subcategoria.nome if item.subcategoria else '—',
            item.condicao,
            item.disponibilidade,
            item.quantidade,
            item.unidade_medida,
            'Sim' if item.patrimonio_utfpr else 'Não',
            'Sim' if item.patrimonio_escola else 'Não',
            item.nome_escola or '—',
            item.localizacao.ambiente if item.localizacao else '—',
            item.localizacao.codigo_etiqueta if item.localizacao else '—',
            item.data_cadastro.strftime('%d/%m/%Y') if item.data_cadastro else '—'
        ])

    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=inventario_ler3.csv'}
    )

@app.route('/exportar/pagina')
def exportar_pagina():
    categorias = Categoria.query.all()
    return render_template('exportar.html', categorias=categorias)

@app.route('/exportar/historico')
def exportar_historico():
    registros = Historico.query.order_by(Historico.data_exclusao.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Categoria', 'Subcategoria', 'Condição', 'Quantidade',
                     'Unidade', 'Patrimônio UTFPR', 'Patrimônio Escola',
                     'Nome da Escola', 'Motivo', 'Data Exclusão'])

    for r in registros:
        writer.writerow([
            r.nome_item,
            r.categoria,
            r.subcategoria,
            r.condicao,
            r.quantidade,
            r.unidade,
            'Sim' if r.patrimonio_utfpr else 'Não',
            'Sim' if r.patrimonio_escola else 'Não',
            r.nome_escola or '—',
            r.motivo or '—',
            r.data_exclusao.strftime('%d/%m/%Y %H:%M') if r.data_exclusao else '—'
        ])

    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=historico_ler3.csv'}
    )
@app.route('/item/remover-imagem/<int:id>')
def remover_imagem(id):
    item = Item.query.get_or_404(id)
    if item.imagem_url:
        caminho = os.path.join(UPLOAD_FOLDER, item.imagem_url)
        if os.path.exists(caminho):
            os.remove(caminho)
        item.imagem_url = None
        db.session.commit()
    return redirect(url_for('editar', id=id))
@app.route('/gerenciar')
def gerenciar():
    categorias    = Categoria.query.all()
    subcategorias = Subcategoria.query.all()
    return render_template('gerenciar.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/categoria/criar', methods=['POST'])
def criar_categoria():
    nome = request.form.get('nome')
    if nome:
        db.session.add(Categoria(nome=nome))
        db.session.commit()
    return redirect(url_for('gerenciar'))

@app.route('/subcategoria/criar', methods=['POST'])
def criar_subcategoria():
    nome         = request.form.get('nome')
    categoria_id = request.form.get('categoria_id')
    if nome and categoria_id:
        db.session.add(Subcategoria(nome=nome, categoria_id=categoria_id))
        db.session.commit()
    return redirect(url_for('gerenciar'))

@app.route('/categoria/deletar/<int:id>')
def deletar_categoria(id):
    categoria = Categoria.query.get(id)
    if categoria:
        Subcategoria.query.filter_by(categoria_id=id).delete()
        Item.query.filter_by(categoria_id=id).update({'categoria_id': None, 'subcategoria_id': None})
        db.session.delete(categoria)
        db.session.commit()
    return redirect(url_for('gerenciar'))

@app.route('/subcategoria/deletar/<int:id>')
def deletar_subcategoria(id):
    subcategoria = Subcategoria.query.get(id)
    if subcategoria:
        Item.query.filter_by(subcategoria_id=id).update({'subcategoria_id': None})
        db.session.delete(subcategoria)
        db.session.commit()
    return redirect(url_for('gerenciar'))

@app.route('/categoria/criar-inline', methods=['POST'])
def criar_categoria_inline():
    nome = request.json.get('nome')
    if nome:
        categoria = Categoria(nome=nome)
        db.session.add(categoria)
        db.session.commit()
        return jsonify({'id': categoria.id, 'nome': categoria.nome})
    return jsonify({'erro': 'Nome inválido'}), 400

@app.route('/subcategoria/criar-inline', methods=['POST'])
def criar_subcategoria_inline():
    nome         = request.json.get('nome')
    categoria_id = request.json.get('categoria_id')
    if nome and categoria_id:
        sub = Subcategoria(nome=nome, categoria_id=categoria_id)
        db.session.add(sub)
        db.session.commit()
        return jsonify({'id': sub.id, 'nome': sub.nome})
    return jsonify({'erro': 'Dados inválidos'}), 400

@app.route('/subcategorias/<int:categoria_id>')
def subcategorias_por_categoria(categoria_id):
    subs = Subcategoria.query.filter_by(categoria_id=categoria_id).all()
    return jsonify([{'id': s.id, 'nome': s.nome} for s in subs])

@app.route('/importar', methods=['GET', 'POST'])
def importar():
    categorias = Categoria.query.all()
    if request.method == 'POST':
        arquivo = request.files.get('arquivo_csv')
        if not arquivo:
            return redirect(url_for('importar'))

        stream = io.StringIO(arquivo.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)

        for row in reader:
            cat  = Categoria.query.filter_by(nome=row.get('Categoria', '—')).first()
            sub  = Subcategoria.query.filter_by(nome=row.get('Subcategoria', '—')).first()

            loc = Localizacao(
                ambiente        = row.get('Ambiente') or None,
                codigo_etiqueta = row.get('Etiqueta') or None
            )
            db.session.add(loc)
            db.session.flush()

            try:
                quantidade = float(row.get('Quantidade', 1))
            except:
                quantidade = 1

            item = Item(
                nome              = row.get('Nome', ''),
                descricao         = row.get('Descrição') or None,
                categoria_id      = cat.id if cat else None,
                subcategoria_id   = sub.id if sub else None,
                condicao          = row.get('Condição', 'sem_status').replace(' ', '_').lower(),
                disponibilidade   = row.get('Disponibilidade', 'disponivel').replace(' ', '_').lower(),
                quantidade        = quantidade,
                unidade_medida    = row.get('Unidade', 'unidade'),
                patrimonio_utfpr  = row.get('Patrimônio UTFPR', 'Não') == 'Sim',
                patrimonio_escola = row.get('Patrimônio Escola', 'Não') == 'Sim',
                nome_escola       = row.get('Nome da Escola') or None,
                localizacao_id    = loc.id
            )
            db.session.add(item)

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('importar.html', categorias=categorias)