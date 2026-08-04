from flask import Flask, render_template, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from flask_mail import Mail, Message
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import sqlite3
import os
from datetime import datetime
import bcrypt
import secrets
import io

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
    rows = cursor.fetchall()
    conn.close()
    
    membros = []
    for row in rows:
        membros.append({
            'id': row[0],
            'nome': row[1],
            'nome_guerra': row[2] if row[2] else '',
            'pelotao': row[3] if row[3] else '',
            'email': row[4] if row[4] else ''
        })
    
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
    row = cursor.fetchone()
    conn.close()
    
    novo_membro = {
        'id': row[0],
        'nome': row[1],
        'nome_guerra': row[2] if row[2] else '',
        'pelotao': row[3] if row[3] else '',
        'email': row[4] if row[4] else ''
    }

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
    row = cursor.fetchone()
    
    if not row:
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
    row = cursor.fetchone()
    conn.close()
    
    membro_atualizado = {
        'id': row[0],
        'nome': row[1],
        'nome_guerra': row[2] if row[2] else '',
        'pelotao': row[3] if row[3] else '',
        'email': row[4] if row[4] else ''
    }

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
    row = cursor.fetchone()
    
    if not row:
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
    rows = cursor.fetchall()
    conn.close()
    
    sugestoes = []
    for row in rows:
        sugestoes.append({
            'id': row[0],
            'gmail': row[1],
            'nome': row[2],
            'pelotao': row[3],
            'texto': row[4],
            'data': row[5]
        })
    
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
    row = cursor.fetchone()
    conn.close()
    
    nova_sugestao = {
        'id': row[0],
        'gmail': row[1],
        'nome': row[2],
        'pelotao': row[3],
        'texto': row[4],
        'data': row[5]
    }

    # Enviar email de confirmação
    try:
        msg = Message(
            subject='Sugestao Recebida - Gremio 1ª Cia',
            recipients=[gmail],
            html=f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Sugestao Recebida</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #0a0a0a;">
                <div style="max-width: 600px; margin: 20px auto; background: #0a0a0a; border-radius: 10px; border: 2px solid #8b0000; padding: 0; overflow: hidden;">
                    <div style="background: #000000; padding: 20px; text-align: center; border-bottom: 2px solid #8b0000;">
                        <h1 style="color: #fff; margin: 0; letter-spacing: 3px; font-size: 24px;">GREMIO 1ª CIA</h1>
                        <p style="color: #888; margin: 5px 0 0 0; font-size: 12px;">Sistema de Gestao</p>
                    </div>
                    <div style="padding: 30px 25px; background: #0a0a0a;">
                        <h2 style="color: #e74c3c; margin: 0 0 10px 0; font-size: 22px;">Sugestao Recebida com Sucesso!</h2>
                        <p style="color: #ccc; font-size: 15px; line-height: 1.6;">
                            Olá <strong style="color: #fff;">{nome}</strong>,
                        </p>
                        <p style="color: #ccc; font-size: 15px; line-height: 1.6;">
                            Recebemos sua sugestao e agradecemos por contribuir para melhorar o <strong style="color: #fff;">Gremio 1ª Cia</strong>!
                        </p>
                        <div style="background: #1a1a1a; padding: 15px 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #8b0000;">
                            <p style="color: #888; font-size: 11px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 1px;">Sua sugestao:</p>
                            <p style="color: #fff; font-size: 14px; margin: 0; line-height: 1.5;">{texto}</p>
                        </div>
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
                    </div>
                    <div style="background: #000000; padding: 15px 20px; text-align: center; border-top: 1px solid #1a1a1a;">
                        <p style="color: #555; font-size: 11px; margin: 0;">
                            &copy; 2026 Gremio 1ª Cia - Todos os direitos reservados
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
    row = cursor.fetchone()
    
    if not row:
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
    rows = cursor.fetchall()
    conn.close()
    
    usuarios = []
    for row in rows:
        usuarios.append({
            'id': row[0],
            'nome': row[1],
            'email': row[2],
            'role': row[3]
        })
    
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
    row = cursor.fetchone()
    conn.close()
    
    novo_usuario = {
        'id': row[0],
        'nome': row[1],
        'email': row[2],
        'role': row[3]
    }

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
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Usuario nao encontrado'}), 404

    if row[0] == session['user_id']:
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
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        logs.append({
            'id': row[0],
            'usuario': row[1],
            'email': row[2],
            'role': row[3],
            'acao': row[4],
            'data': row[5]
        })
    
    return jsonify(logs)

# ===== API - BAIXAR PDF DINÂMICO =====
@app.route('/api/baixar-pdf', methods=['GET'])
def api_baixar_pdf():
    if 'user_id' not in session:
        return jsonify({'error': 'Nao autorizado'}), 401
    
    user_role = session.get('user_role')
    if user_role not in ['adm', 'dev']:
        return jsonify({'error': 'Permissao negada'}), 403

    try:
        # Buscar TODOS os membros do banco de dados
        conn = sqlite3.connect('gremio.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela membros existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='membros'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Tabela membros nao encontrada'}), 404
        
        # Buscar todos os membros
        cursor.execute('SELECT * FROM membros ORDER BY pelotao, nome')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return jsonify({'error': 'Nenhum membro encontrado no banco de dados'}), 404

        # Converter para lista de dicionários
        membros = []
        for row in rows:
            membros.append({
                'id': row[0],
                'nome': row[1],
                'nome_guerra': row[2] if row[2] else '-',
                'pelotao': row[3] if row[3] else 'Sem pelotão',
                'email': row[4] if row[4] else ''
            })

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Estilos
        styles = getSampleStyleSheet()
        
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=20,
            textColor=colors.HexColor('#8b0000'),
            fontName='Helvetica-Bold',
            spaceAfter=8
        )
        
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            textColor=colors.HexColor('#555555'),
            spaceAfter=5
        )
        
        data_style = ParagraphStyle(
            'Data',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=11,
            textColor=colors.HexColor('#888888'),
            spaceAfter=25
        )
        
        cabecalho_style = ParagraphStyle(
            'Cabecalho',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=10,
            textColor=colors.HexColor('#ffffff'),
            fontName='Helvetica-Bold'
        )
        
        celula_style = ParagraphStyle(
            'Celula',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=10,
            textColor=colors.HexColor('#000000')
        )
        
        pelotao_style = ParagraphStyle(
            'Pelotao',
            parent=styles['Heading2'],
            alignment=TA_LEFT,
            fontSize=14,
            textColor=colors.HexColor('#ffffff'),
            fontName='Helvetica-Bold',
            spaceAfter=10,
            spaceBefore=20
        )
        
        rodape_style = ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            textColor=colors.HexColor('#888888'),
            spaceBefore=20
        )

        elementos = []

        # Título
        elementos.append(Paragraph('RELAÇÃO DE PAGAMENTO DO GRÊMIO — 1ª CIA', titulo_style))
        elementos.append(Paragraph('Somente os militares que efetuaram o pagamento', subtitulo_style))
        elementos.append(Paragraph(
            f'Gerado em: {datetime.now().strftime("%d/%m/%Y")} às {datetime.now().strftime("%H:%M")}',
            data_style
        ))

        # Agrupar por pelotão
        pelotoes = {}
        for membro in membros:
            pelotao = membro['pelotao']
            if pelotao not in pelotoes:
                pelotoes[pelotao] = []
            pelotoes[pelotao].append(membro)

        # Ordenar pelotões
        ordem_pelotoes = ['1° Pelotão', '2° Pelotão', '3° Pelotão', 'ENC-MAT']
        pelotoes_ordenados = [p for p in ordem_pelotoes if p in pelotoes]

        for pelotao in pelotoes_ordenados:
            membros_pelotao = pelotoes[pelotao]
            
            # Título do pelotão
            elementos.append(Paragraph(pelotao, pelotao_style))
            
            # Dados da tabela
            data = []
            data.append([
                Paragraph('N°', cabecalho_style),
                Paragraph('NOME COMPLETO', cabecalho_style),
                Paragraph('NOME DE GUERRA', cabecalho_style),
                Paragraph('SITUAÇÃO', cabecalho_style)
            ])
            
            for idx, m in enumerate(membros_pelotao, 1):
                data.append([
                    Paragraph(str(idx), celula_style),
                    Paragraph(m['nome'], celula_style),
                    Paragraph(m['nome_guerra'], celula_style),
                    Paragraph('PAGO', celula_style)
                ])
            
            # Criar tabela
            table = Table(data, colWidths=[0.8*cm, 7*cm, 5*cm, 2.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b0000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elementos.append(table)
            elementos.append(Spacer(1, 0.5*cm))
        
        # Rodapé
        elementos.append(Paragraph('_____________________________________________', rodape_style))
        elementos.append(Paragraph('ST ADAIR - SEÇ CMDO', rodape_style))
        elementos.append(Paragraph('&copy; 2026 Grêmio 1ª Cia - Todos os direitos reservados', rodape_style))

        # Gerar PDF
        doc.build(elementos)
        buffer.seek(0)

        # Retornar PDF
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'Relacao de Pagamento - Gremio 1ª Cia.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f'Erro ao gerar PDF: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro ao gerar PDF: {str(e)}'}), 500

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