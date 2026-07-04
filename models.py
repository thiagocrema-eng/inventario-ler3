from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Categoria(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(50), nullable=False)
    subcategorias = db.relationship('Subcategoria', backref='categoria', lazy=True)

class Subcategoria(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    nome         = db.Column(db.String(50), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)

class Localizacao(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    ambiente        = db.Column(db.String(50))
    codigo_etiqueta = db.Column(db.String(50))

class Item(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    nome                = db.Column(db.String(100), nullable=False)
    descricao           = db.Column(db.String(500))
    categoria_id        = db.Column(db.Integer, db.ForeignKey('categoria.id'))
    subcategoria_id     = db.Column(db.Integer, db.ForeignKey('subcategoria.id'))
    condicao            = db.Column(db.String(20), default='funcionando')
    disponibilidade     = db.Column(db.String(20), default='disponivel')
    patrimonio_utfpr    = db.Column(db.Boolean, default=False)
    patrimonio_escola   = db.Column(db.Boolean, default=False)
    nome_escola         = db.Column(db.String(100))
    localizacao_id      = db.Column(db.Integer, db.ForeignKey('localizacao.id'))
    imagem_url          = db.Column(db.String(200))
    unidade_medida      = db.Column(db.String(20), default='unidade')
    quantidade          = db.Column(db.Float, default=1)
    data_cadastro       = db.Column(db.DateTime, default=datetime.utcnow)

    # campo para cadastro hierárquico
    item_pai_id         = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    subitens            = db.relationship('Item', backref=db.backref('item_pai', remote_side='Item.id'), lazy=True)

    categoria    = db.relationship('Categoria', backref='itens')
    subcategoria = db.relationship('Subcategoria', backref='itens')
    localizacao  = db.relationship('Localizacao', backref='itens')

class Historico(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    nome_item         = db.Column(db.String(100))
    descricao         = db.Column(db.String(500))
    categoria         = db.Column(db.String(50))
    subcategoria      = db.Column(db.String(50))
    condicao          = db.Column(db.String(20))
    quantidade        = db.Column(db.Float)
    unidade           = db.Column(db.String(20))
    patrimonio_utfpr  = db.Column(db.Boolean)
    patrimonio_escola = db.Column(db.Boolean)
    nome_escola       = db.Column(db.String(100))
    data_exclusao     = db.Column(db.DateTime, default=datetime.utcnow)
    motivo            = db.Column(db.String(200))