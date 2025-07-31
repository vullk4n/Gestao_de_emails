# 📧 Sistema de Gestão de Emails

Um sistema simples e eficiente para gerenciar emails usando Python e SQLite, com funcionalidades de categorização, busca e organização.

## 🚀 Características

- **Banco de dados SQLite** para armazenamento local e eficiente
- **Categorização automática** de emails (Trabalho, Pessoal, Spam, etc.)
- **Sistema de busca** por texto no assunto e corpo dos emails
- **Marcação de status** (lido, importante, arquivado)
- **Gestão de anexos** com metadados
- **Estatísticas detalhadas** sobre o uso
- **Transações seguras** com rollback automático
- **Prepared statements** para performance otimizada

## 📊 Estrutura do Banco de Dados

### Tabelas Principais

- **`usuarios`**: Informações dos usuários
- **`categorias`**: Categorias para organização dos emails
- **`emails`**: Dados principais dos emails
- **`anexos`**: Arquivos anexados aos emails

### Categorias Padrão

- 🏢 **Trabalho** - Emails relacionados ao trabalho
- 👤 **Pessoal** - Emails pessoais
- 🚫 **Spam** - Emails não desejados
- ⭐ **Importante** - Emails importantes
- 🎯 **Promoções** - Emails promocionais
- 📰 **Newsletter** - Newsletters e boletins


## 🔍 Funcionalidades Avançadas

### Busca Inteligente
- Busca por texto no assunto e corpo
- Filtros por categoria, status de leitura
- Ordenação por data de envio

### Performance
- Conexão persistente com o banco
- Prepared statements reutilizáveis
- Índices otimizados para consultas frequentes
- Modo WAL para melhor concorrência

### Segurança
- Transações com rollback automático
- Validação de dados de entrada
- Prepared statements para prevenir SQL injection