CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT,
    cor TEXT DEFAULT '#007bff'
);

CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remetente TEXT NOT NULL,
    destinatario TEXT NOT NULL,
    assunto TEXT NOT NULL,
    corpo TEXT,
    categoria_id INTEGER,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_recebimento TIMESTAMP,
    lido BOOLEAN DEFAULT 0,
    importante BOOLEAN DEFAULT 0,
    arquivado BOOLEAN DEFAULT 0,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    nome_arquivo TEXT NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    tamanho INTEGER,
    tipo_mime TEXT,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO categorias (nome, descricao, cor) VALUES
    ('Trabalho', 'Emails relacionados ao trabalho', '#28a745'),
    ('Pessoal', 'Emails pessoais', '#007bff'),
    ('Spam', 'Emails não desejados', '#dc3545'),
    ('Importante', 'Emails importantes', '#ffc107'),
    ('Promoções', 'Emails promocionais', '#6f42c1'),
    ('Newsletter', 'Newsletters e boletins', '#17a2b8');

CREATE INDEX IF NOT EXISTS idx_emails_remetente ON emails(remetente);
CREATE INDEX IF NOT EXISTS idx_emails_destinatario ON emails(destinatario);
CREATE INDEX IF NOT EXISTS idx_emails_data ON emails(data_envio);
CREATE INDEX IF NOT EXISTS idx_emails_categoria ON emails(categoria_id);
CREATE INDEX IF NOT EXISTS idx_emails_lido ON emails(lido); 
