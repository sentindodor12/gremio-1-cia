from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
import sqlite3
import os
from datetime import datetime
import bcrypt
import secrets

app = Flask(__name__, 
            template_folder='.', 
            static_folder='.',    
            static_url_path='')   
app.secret_key = secrets.token_hex(16)
CORS(app)

# ===== CONFIGURAÇÃO DO EMAIL =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'limpaplus.sup1@gmail.com'
app.config['MAIL_PASSWORD'] = 'pizu mgal rblk zenm'
app.config['MAIL_DEFAULT_SENDER'] = 'limpaplus.sup1@gmail.com'
app.config['MAIL_DEBUG'] = True

mail = Mail(app)

# ===== BANCO DE DADOS =====
DATABASE = 'gremio.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de membros (com nome_guerra)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nome_guerra TEXT,
            pelotao TEXT NOT NULL,
            email TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de sugestões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sugestoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail TEXT NOT NULL,
            nome TEXT NOT NULL,
            pelotao TEXT NOT NULL,
            texto TEXT NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            acao TEXT NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuários padrão
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    count = cursor.fetchone()[0]
    
    if count == 0:
        senha_admin = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, role)
            VALUES (?, ?, ?, ?)
        ''', ('Administrador', 'admin@gremio.com', senha_admin, 'adm'))
        
        senha_dev = bcrypt.hashpw("dev123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, role)
            VALUES (?, ?, ?, ?)
        ''', ('Desenvolvedor', 'dev@gremio.com', senha_dev, 'dev'))
    
    # Inserir membros padrão com nome_guerra
    cursor.execute('SELECT COUNT(*) FROM membros')
    count_membros = cursor.fetchone()[0]
    
    if count_membros == 0:
        membros_padrao = [
            # 1° Pelotão
            ('Paulo Ryan de Oliveira Tomaz', 'TOMAZ', '1° Pelotão', ''),
            ('Carlos Eduardo Cardoso Curcino', 'CARDOSO', '1° Pelotão', ''),
            ('Elias Gabriel da Silva Luciano', 'ELIAS', '1° Pelotão', ''),
            ('Matheus Rutina Kowalski', 'KOWALSKI', '1° Pelotão', ''),
            ('Gustavo Luis de Sousa da Costa', 'S COSTA', '1° Pelotão', ''),
            ('Vinicius Henrique Sampaio Costa', 'SAMPAIO', '1° Pelotão', ''),
            ('Kauã Rodrigues dos Santos', 'R SANTOS', '1° Pelotão', ''),
            ('Julio Cesar Bohn Nobre Costa e Silva', 'CESAR', '1° Pelotão', ''),
            ('Lucas Ribeiro Gomes', 'RIBEIRO', '1° Pelotão', ''),
            ('Victor Hugo Magalhães Soares', 'MAGALHÃES', '1° Pelotão', ''),
            ('Felipe Lucas Gonçalves Silva', 'L GONÇALVES', '1° Pelotão', ''),
            ('Gabriel Carvalho Leite', 'G. LEITE', '1° Pelotão', ''),
            ('João Gabriel Rodrigues dos Santos', 'GABRIEL', '1° Pelotão', ''),
            ('Jose Henrique Ribeiro Alves', 'JOSE', '1° Pelotão', ''),
            ('Enzo Sá dos Passos', 'PASSOS', '1° Pelotão', ''),
            ('Glauter Rian Coimbra Rabelo', 'GLAUTER', '1° Pelotão', ''),
            
            # 2° Pelotão
            ('João Bernardo Alves Santos Silva', 'SANTOS SILVA', '2° Pelotão', ''),
            ('Cauã Felipe Targino dos Santos', 'TARGINO', '2° Pelotão', ''),
            ('Benjamim Gabriel Gonçalves Carvalho de Lima', 'BENJAMIM', '2° Pelotão', ''),
            ('Marcos Vinicius Alves Ribeiro da Silva', 'M. ALVES', '2° Pelotão', ''),
            ('Davi Lores Bernardes', 'DAVI LORES', '2° Pelotão', ''),
            ('Luiz Henrique Boaventura Coutinho', 'BOAVENTURA', '2° Pelotão', ''),
            ('Matheus Thiago Lourena Mendes', 'MENDES', '2° Pelotão', ''),
            ('Luiz Fernando Ferreira Bezerra', 'BEZERRA', '2° Pelotão', ''),
            ('Gabriel Borges Lopes', 'LOPES', '2° Pelotão', ''),
            ('Carlos Eduardo Espíndola Macêdo', 'ESPINDOLA', '2° Pelotão', ''),
            ('Eduardo Kevenn Fernandes Pereira', 'KEVENN', '2° Pelotão', ''),
            ('Ryan Douglas Gomes de Melo', 'GOMES', '2° Pelotão', ''),
            ('Matheus de Souza Silva', 'SILVA', '2° Pelotão', ''),
            ('Marcos Samuel de Sousa Duarte', 'SOUSA', '2° Pelotão', ''),
            ('Davi Gomes Pires', 'D. GOMES', '2° Pelotão', ''),
            ('Fabrício Pereira do Carmo', 'DO CARMO', '2° Pelotão', ''),
            ('Guilherme Faria Santana', 'SANTANA', '2° Pelotão', ''),
            ('Luis Enrique Salviano dos Santos', 'SALVIANO', '2° Pelotão', ''),
            ('Thiago Alves Oliveira', 'AL T.ALVES', '2° Pelotão', ''),
            ('Allisson Araújo Lima', 'ALLISSON', '2° Pelotão', ''),
            ('Lucas Silva Primo', 'L. PRIMO', '2° Pelotão', ''),
            ('Ryan Cristhian de Oliveira Franca', 'EP CRISTHIAN', '2° Pelotão', ''),
            
            # 3° Pelotão
            ('Marcelo Costa Ribeiro', 'COSTA', '3° Pelotão', ''),
            ('Erick Ramalho de Oliveira', 'ERICK', '3° Pelotão', ''),
            ('Fernando Santos Silva', 'FERNANDO', '3° Pelotão', ''),
            ('Hadrian Divino Aquino de Sousa', 'DIVINO', '3° Pelotão', ''),
            ('Miguel da Silva Rodrigues', 'MIGUEL', '3° Pelotão', ''),
            ('Anthony Pierre Silva Nascimento', 'PIERRE', '3° Pelotão', ''),
            ('Victor Xavier Carvalho dos Santos', 'XAVIER', '3° Pelotão', ''),
            ('João Gabriel Souza de Paula', 'JOÃO', '3° Pelotão', ''),
            ('Leandro Lucas Lima dos Santos', 'L SANTOS', '3° Pelotão', ''),
            ('Bruno Durangue da Silva', 'BRUNO', '3° Pelotão', ''),
            ('Luan Silva dos Anjos', 'ANJOS', '3° Pelotão', ''),
            ('Vinicius Rodrigues Costas', 'VINICIUS', '3° Pelotão', ''),
            ('Thiago de Jesus dos Santos Lima', 'DE JESUS', '3° Pelotão', ''),
            ('Ítalo Alef Ramos da Conceição', 'CONCEIÇÃO', '3° Pelotão', ''),
            ('Ytalo Vinicius Meireles e Souza', 'MEIRELES', '3° Pelotão', ''),
            ('Daniel Sousa Ferreira', 'DANIEL', '3° Pelotão', ''),
            ('Victor Gabriel Lopes do Carmo', 'VICTOR', '3° Pelotão', ''),
            ('Marcos Vinicius Santos Rodrigues', 'MARCOS VINICIUS', '3° Pelotão', ''),
            ('Marcos Gabriel Rodrigues da Silva', 'MARCOS', '3° Pelotão', ''),
            ('Wallace Barreto Alcantara', 'BARRETO', '3° Pelotão', ''),
            ('Wendel Santos de Lima', 'WENDEL', '3° Pelotão', ''),
            ('Igor Patrick Martins de Oliveira', 'PATRICK', '3° Pelotão', ''),
            
            # ENC-MAT
            ('Kelvyn Samuel Bagnhuk de Melo', 'EP BAGNHUK', 'ENC-MAT', ''),
            ('Vinicios Soares Batista', 'EP SOARES', 'ENC-MAT', ''),
            ('Isaack Lopes de Oliveira', 'EP LOPES', 'ENC-MAT', ''),
            ('Adair Cardoso de Andrade', 'ST ADAIR', 'ENC-MAT', ''),
            ('Thiago Ayrton Gomes da Silva', 'CB AYRTON', 'ENC-MAT', '')
        ]
        cursor.executemany('''
            INSERT INTO membros (nome, nome_guerra, pelotao, email)
            VALUES (?, ?, ?, ?)
        ''', membros_padrao)
    
    conn.commit()
    conn.close()
    print('Banco de dados inicializado com sucesso!')

init_db()

# ===== ROTAS DAS PÁGINAS =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/lista')
def lista_page():
    return render_template('lista.html')

@app.route('/avaliacao')
def avaliacao_page():
    return render_template('avaliacao.html')

@app.route('/configuracoes')
def configuracoes_page():
    return render_template('configuracoes.html')

@app.route('/<path:filename>')
def static_files(filename):
    if filename.startswith('data/') or filename == 'gremio.db':
        return '', 404
    return send_from_directory('.', filename)

# ===== API - LOGIN =====
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Email ou senha incorretos'}), 401

    if not bcrypt.checkpw(senha.encode('utf-8'), user['senha'].encode('utf-8')):
        return jsonify({'error': 'Email ou senha incorretos'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (usuario, email, role, acao)
        VALUES (?, ?, ?, ?)
    ''', (user['nome'], user['email'], user['role'], 'login'))
    conn.commit()
    conn.close()

    session['user_id'] = user['id']
    session['user_nome'] = user['nome']
    session['user_email'] = user['email']
    session['user_role'] = user['role']

    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'nome': user['nome'],
            'email': user['email'],
            'role': user['role']
        }
    })

# ===== API - VERIFICAR SESSÃO =====
@app.route('/api/verificar_sessao', methods=['GET'])
def verificar_sessao():
    if 'user_id' in session:
        return jsonify({
            'logado': True,
            'user': {
                'id': session['user_id'],
                'nome': session['user_nome'],
                'email': session['user_email'],
                'role': session['user_role']
            }
        })
    return jsonify({'logado': False})

# ===== API - LOGOUT =====
@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

# ===== API - MEMBROS =====
@app.route('/api/membros', methods=['GET'])
def api_get_membros():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM membros ORDER BY id')
    membros = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(membros)

@app.route('/api/membros', methods=['POST'])
def api_add_membro():
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    user_role = session.get('user_role')
    if user_role not in ['adm', 'dev']:
        return jsonify({'error': 'Permissao negada'}), 403

    data = request.get_json()
    nome = data.get('nome')
    nome_guerra = data.get('nome_guerra', '')
    pelotao = data.get('pelotao')
    email = data.get('email', '')

    if not nome or not pelotao:
        return jsonify({'error': 'Nome e pelotao sao obrigatorios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO membros (nome, nome_guerra, pelotao, email)
        VALUES (?, ?, ?, ?)
    ''', (nome.strip(), nome_guerra.strip(), pelotao.strip(), email.strip()))
    conn.commit()
    
    novo_id = cursor.lastrowid
    cursor.execute('SELECT * FROM membros WHERE id = ?', (novo_id,))
    novo_membro = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'membro': novo_membro})

@app.route('/api/membros/<int:id>', methods=['PUT'])
def api_edit_membro(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    user_role = session.get('user_role')
    if user_role not in ['adm', 'dev']:
        return jsonify({'error': 'Permissao negada'}), 403

    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM membros WHERE id = ?', (id,))
    membro = cursor.fetchone()
    
    if not membro:
        conn.close()
        return jsonify({'error': 'Membro nao encontrado'}), 404

    campos = []
    valores = []
    
    if 'nome' in data and data['nome']:
        campos.append('nome = ?')
        valores.append(data['nome'].strip())
    if 'nome_guerra' in data:
        campos.append('nome_guerra = ?')
        valores.append(data['nome_guerra'].strip())
    if 'pelotao' in data and data['pelotao']:
        campos.append('pelotao = ?')
        valores.append(data['pelotao'].strip())
    if 'email' in data:
        campos.append('email = ?')
        valores.append(data['email'].strip())
    
    if campos:
        valores.append(id)
        query = f"UPDATE membros SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
    
    cursor.execute('SELECT * FROM membros WHERE id = ?', (id,))
    membro_atualizado = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'membro': membro_atualizado})

@app.route('/api/membros/<int:id>', methods=['DELETE'])
def api_delete_membro(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    user_role = session.get('user_role')
    if user_role not in ['adm', 'dev']:
        return jsonify({'error': 'Permissao negada'}), 403

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM membros WHERE id = ?', (id,))
    membro = cursor.fetchone()
    
    if not membro:
        conn.close()
        return jsonify({'error': 'Membro nao encontrado'}), 404

    cursor.execute('DELETE FROM membros WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ===== API - SUGESTÕES =====
@app.route('/api/sugestoes', methods=['GET'])
def api_get_sugestoes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sugestoes ORDER BY id DESC')
    sugestoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sugestoes)

@app.route('/api/sugestoes', methods=['POST'])
def api_add_sugestao():
    data = request.get_json()
    gmail = data.get('gmail')
    nome = data.get('nome')
    pelotao = data.get('pelotao')
    texto = data.get('texto')

    if not gmail or not nome or not pelotao or not texto:
        return jsonify({'error': 'Todos os campos sao obrigatorios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sugestoes (gmail, nome, pelotao, texto)
        VALUES (?, ?, ?, ?)
    ''', (gmail.strip(), nome.strip(), pelotao.strip(), texto.strip()))
    conn.commit()
    
    novo_id = cursor.lastrowid
    cursor.execute('SELECT * FROM sugestoes WHERE id = ?', (novo_id,))
    nova_sugestao = dict(cursor.fetchone())
    conn.close()

    # ===== ENVIAR EMAIL DE CONFIRMAÇÃO =====
    try:
        msg = Message(
            subject='Sugestao Recebida - Gremio 1ª Cia',
            recipients=[gmail],
            html=f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Sugestao Recebida</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #0a0a0a;">
                <div style="max-width: 600px; margin: 20px auto; background: #0a0a0a; border-radius: 10px; border: 2px solid #8b0000; padding: 0; overflow: hidden;">
                    
                    <!-- HEADER COM LOGO -->
                    <div style="background: #000000; padding: 20px; text-align: center; border-bottom: 2px solid #8b0000;">
                        <img src="1cia.png" alt="Gremio 1ª Cia" style="width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px;">
                        <h1 style="color: #fff; margin: 0; letter-spacing: 3px; font-size: 24px;">GREMIO 1ª CIA</h1>
                        <p style="color: #888; margin: 5px 0 0 0; font-size: 12px;">Sistema de Gestao</p>
                    </div>
                    
                    <!-- CONTEUDO -->
                    <div style="padding: 30px 25px; background: #0a0a0a;">
                        <h2 style="color: #e74c3c; margin: 0 0 10px 0; font-size: 22px;">Sugestao Recebida com Sucesso!</h2>
                        
                        <p style="color: #ccc; font-size: 15px; line-height: 1.6;">
                            Olá <strong style="color: #fff;">{nome}</strong>,
                        </p>
                        <p style="color: #ccc; font-size: 15px; line-height: 1.6;">
                            Recebemos sua sugestao e agradecemos por contribuir para melhorar o <strong style="color: #fff;">Gremio 1ª Cia</strong>!
                        </p>
                        
                        <!-- SUGESTAO -->
                        <div style="background: #1a1a1a; padding: 15px 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #8b0000;">
                            <p style="color: #888; font-size: 11px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 1px;">Sua sugestao:</p>
                            <p style="color: #fff; font-size: 14px; margin: 0; line-height: 1.5;">{texto}</p>
                        </div>
                        
                        <!-- HORARIO DE FUNCIONAMENTO -->
                        <div style="background: #1a1a1a; padding: 15px 20px; border-radius: 8px; margin: 15px 0;">
                            <h3 style="color: #fff; font-size: 15px; margin: 0 0 10px 0; text-align: center;">HORARIO DE FUNCIONAMENTO</h3>
                            <div style="border-bottom: 1px solid #2a2a2a; padding: 8px 0; display: flex; justify-content: space-between; color: #ccc; font-size: 13px;">
                                <span>Segunda a Quinta</span>
                                <span style="color: #e74c3c; font-weight: bold;">11:30 - 12:30 e 16:30 - 22:00</span>
                            </div>
                            <div style="border-bottom: 1px solid #2a2a2a; padding: 8px 0; display: flex; justify-content: space-between; color: #ccc; font-size: 13px;">
                                <span>Sexta</span>
                                <span style="color: #e74c3c; font-weight: bold;">12:00 - 22:00</span>
                            </div>
                            <div style="padding: 8px 0; display: flex; justify-content: space-between; color: #ccc; font-size: 13px;">
                                <span>Finais de Semana e Feriados</span>
                                <span style="color: #e74c3c; font-weight: bold;">08:00 - 22:00</span>
                            </div>
                        </div>
                        
                        <p style="color: #888; font-size: 13px; text-align: center; margin: 15px 0 0 0;">
                            Fique por dentro do horario de funcionamento do Gremio!
                        </p>
                    </div>
                    
                    <!-- FOOTER -->
                    <div style="background: #000000; padding: 15px 20px; text-align: center; border-top: 1px solid #1a1a1a;">
                        <p style="color: #555; font-size: 11px; margin: 0;">
                            &copy; 2026 Gremio 1ª Cia - Todos os direitos reservados
                        </p>
                        <p style="color: #444; font-size: 10px; margin: 3px 0 0 0;">
                            Desenvolvido para a 1ª Companhia
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        )
        mail.send(msg)
        print(f'Email enviado com sucesso para: {gmail}')
    except Exception as e:
        print(f'Erro ao enviar email: {e}')

    return jsonify({'success': True, 'sugestao': nova_sugestao})

@app.route('/api/sugestoes/<int:id>', methods=['DELETE'])
def api_delete_sugestao(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    user_role = session.get('user_role')
    if user_role not in ['adm', 'dev']:
        return jsonify({'error': 'Permissao negada'}), 403

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM sugestoes WHERE id = ?', (id,))
    sugestao = cursor.fetchone()
    
    if not sugestao:
        conn.close()
        return jsonify({'error': 'Sugestao nao encontrada'}), 404

    cursor.execute('DELETE FROM sugestoes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ===== API - USUARIOS =====
@app.route('/api/usuarios', methods=['GET'])
def api_get_usuarios():
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    if session.get('user_role') != 'dev':
        return jsonify({'error': 'Permissao negada'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, email, role FROM usuarios')
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(usuarios)

@app.route('/api/usuarios', methods=['POST'])
def api_add_usuario():
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    if session.get('user_role') != 'dev':
        return jsonify({'error': 'Permissao negada'}), 403

    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    role = data.get('role', 'adm')

    if not nome or not email or not senha:
        return jsonify({'error': 'Nome, email e senha sao obrigatorios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email ja cadastrado'}), 400

    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute('''
        INSERT INTO usuarios (nome, email, senha, role)
        VALUES (?, ?, ?, ?)
    ''', (nome.strip(), email.strip(), senha_hash, role))
    conn.commit()
    
    novo_id = cursor.lastrowid
    cursor.execute('SELECT id, nome, email, role FROM usuarios WHERE id = ?', (novo_id,))
    novo_usuario = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'usuario': novo_usuario})

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def api_delete_usuario(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    if session.get('user_role') != 'dev':
        return jsonify({'error': 'Permissao negada'}), 403

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Usuario nao encontrado'}), 404

    if user['id'] == session['user_id']:
        conn.close()
        return jsonify({'error': 'Nao e possivel excluir o proprio usuario'}), 400

    cursor.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ===== API - LOGS =====
@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    if session.get('user_role') != 'dev':
        return jsonify({'error': 'Permissao negada'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 100')
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

# ===== INICIAR SERVIDOR =====
if __name__ == '__main__':
    print('=' * 50)
    print(' GREMIO 1ª CIA - Sistema de Gestao')
    print('=' * 50)
    print(f' Banco de dados: {DATABASE}')
    print(f' Email: limpaplus.sup1@gmail.com')
    print(' Credenciais padrao:')
    print('   - admin@gremio.com / admin123 (ADM)')
    print('   - dev@gremio.com / dev123 (DEV)')
    print('=' * 50)
    print(' Servidor rodando em: http://localhost:5000')
    print('=' * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)