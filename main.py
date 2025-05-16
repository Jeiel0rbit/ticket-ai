from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)

# Chave secreta para sessões e flash messages
app.secret_key = os.urandom(24)

# Token do administrador
ADMIN_TOKEN = "seu-token-super-secreto-123"

# "Banco de dados" em memória para os tickets
tickets_db = []
ticket_id_counter = 1

# Sua Chave API da Gemini
GEMINI_API_KEY = "AIzaSyYOUR_API_KEY" # Sua chave API mais recente

# Configuração da API Gemini
GEMINI_CONFIGURED_SUCCESSFULLY = False
model = None
MODEL_NAME = "gemini-1.5-flash-latest"

print("INFO: Tentando configurar a API Gemini...")
if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("AIzaSyYOUR_API_KEY"): # Evita usar um placeholder óbvio
    try:
        print(f"INFO: Usando a chave API Gemini: ...{GEMINI_API_KEY[-4:]}")
        genai.configure(api_key=GEMINI_API_KEY)
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 3072,
        }
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        print(f"INFO: Tentando carregar o modelo Gemini: {MODEL_NAME}")
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        GEMINI_CONFIGURED_SUCCESSFULLY = True
        print(f"INFO: API Gemini e modelo '{MODEL_NAME}' configurados com SUCESSO.")
    except Exception as e:
        print(f"ERRO CRÍTICO: Falha ao configurar a API Gemini ou o modelo '{MODEL_NAME}': {e}")
        GEMINI_CONFIGURED_SUCCESSFULLY = False
else:
    print("AVISO: Chave da API Gemini não fornecida ou é um placeholder.")
    print("AVISO: A funcionalidade de sugestão da IA estará desabilitada.")


@app.errorhandler(404)
def page_not_found(e):
    """Manipulador para erros 404 (Página Não Encontrada)."""
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tickets')
def api_tickets():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Não autorizado"}), 401
    sorted_tickets_with_urls = []
    for ticket_in_db in sorted(tickets_db, key=lambda t: t['id'], reverse=True):
        ticket_data = ticket_in_db.copy()
        ticket_data['view_url'] = url_for('view_ticket', ticket_id=ticket_in_db['id'])
        sorted_tickets_with_urls.append(ticket_data)
    return jsonify(sorted_tickets_with_urls)

@app.route('/ticket', methods=['GET', 'POST'])
def create_ticket():
    global ticket_id_counter
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        description = request.form.get('description')
        status = "Aberto"
        if not name or not email or not subject or not description:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('ticket.html', form_data=form_data)
        new_ticket = {
            "id": ticket_id_counter, "name": name, "email": email,
            "subject": subject, "description": description, "status": status,
        }
        tickets_db.append(new_ticket)
        ticket_id_counter += 1
        flash(f'Ticket #{new_ticket["id"]} criado com sucesso!', 'success')
        return redirect(url_for('create_ticket'))
    return render_template('ticket.html', form_data=form_data if request.method == 'POST' else {})

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        provided_token = request.form.get('token')
        if provided_token == ADMIN_TOKEN:
            session['admin_logged_in'] = True
            flash('Login de administrador bem-sucedido!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Token de administrador inválido. Tente novamente.', 'danger')
            return render_template('admin_login.html')
    if not session.get('admin_logged_in'):
        return render_template('admin_login.html')
    sorted_tickets = sorted(tickets_db, key=lambda t: t['id'], reverse=True)
    return render_template('admin.html', tickets=sorted_tickets)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/ticket/<int:ticket_id>')
def view_ticket(ticket_id):
    """
    Rota para visualizar detalhes de um ticket específico.
    A sugestão da IA é gerada aqui e passada para o template.
    """
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'warning')
        return redirect(url_for('admin_dashboard'))

    ticket = next((t for t in tickets_db if t['id'] == ticket_id), None)
    if not ticket:
        flash('Ticket não encontrado.', 'danger')
        return redirect(url_for('admin_dashboard'))

    gemini_suggestion = "Carregando sugestão da IA..." # Mensagem inicial enquanto carrega
    
    if GEMINI_CONFIGURED_SUCCESSFULLY and model:
        print(f"INFO: Solicitando sugestão da Gemini para o ticket ID {ticket_id} usando o modelo {model.model_name}...")
        try:
            prompt_parts = [
                f"Você é um assistente de suporte técnico prestativo e empático.",
                f"Analise o seguinte ticket de suporte e gere uma sugestão de resposta para o administrador enviar ao usuário. A resposta deve ser em Português do Brasil.\n",
                f"Detalhes do Ticket:",
                f"  ID do Ticket: {ticket['id']}",
                f"  Nome do Solicitante: {ticket['name']}",
                f"  Email do Solicitante: {ticket['email']}",
                f"  Assunto: {ticket['subject']}",
                f"  Descrição do Problema: {ticket['description']}\n",
                f"Instruções para a IA:",
                f"1. Seja cordial e profissional.",
                f"2. Demonstre que o problema foi compreendido.",
                f"3. Ofereça uma solução clara, se possível, ou próximos passos para diagnóstico.",
                f"4. Se precisar de mais informações, indique quais seriam úteis.",
                f"5. Formate a resposta de forma clara e organizada, usando parágrafos e quebras de linha onde apropriado.\n",
                f"Sugestão de Resposta para o Administrador (enviar para '{ticket['name']}'):"
            ]
            response = model.generate_content(prompt_parts)
            if response and response.text:
                gemini_suggestion = response.text
                print(f"INFO: Sugestão da Gemini recebida para o ticket ID {ticket_id}.")
            else:
                gemini_suggestion = "A IA Gemini retornou uma resposta vazia ou inválida. Verifique os logs do servidor."
                if response and response.prompt_feedback:
                    print(f"AVISO: Feedback do prompt da Gemini para o ticket {ticket_id}: {response.prompt_feedback}")
                else:
                    print(f"AVISO: Resposta da API Gemini para o ticket {ticket_id} foi vazia ou inválida. Resposta completa: {response}")
        except Exception as e:
            print(f"ERRO: Erro ao chamar a API Gemini para o ticket {ticket_id}: {e}")
            gemini_suggestion = f"Erro ao tentar gerar sugestão da IA Gemini: {str(e)}. Verifique os logs do servidor."
    elif not GEMINI_CONFIGURED_SUCCESSFULLY:
        gemini_suggestion = "A API Gemini não foi configurada corretamente ou a chave não foi fornecida. Verifique os logs do servidor para mais detalhes."
        print("AVISO: Tentativa de gerar sugestão, mas a API Gemini não está configurada.")
    
    return render_template('view_ticket_admin.html', ticket=ticket, gemini_suggestion=gemini_suggestion)

# A rota /api/ticket/<int:ticket_id>/generate_suggestion não é mais necessária para este fluxo.
# Pode ser removida ou comentada se não for usada para outros fins.
# @app.route('/api/ticket/<int:ticket_id>/generate_suggestion', methods=['POST'])
# def api_generate_ai_suggestion(ticket_id): ...

@app.route('/admin/ticket/update_status/<int:ticket_id>', methods=['POST'])
def update_ticket_status(ticket_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    new_status = request.form.get('status')
    ticket_to_update = next((t for t in tickets_db if t['id'] == ticket_id), None)
    if ticket_to_update and new_status:
        ticket_to_update['status'] = new_status
        flash(f'Status do Ticket ID {ticket_id} atualizado para "{new_status}".', 'success')
    elif not ticket_to_update:
        flash(f'Ticket ID {ticket_id} não encontrado.', 'danger')
    else:
        flash('Erro ao atualizar o status do ticket. Novo status não fornecido.', 'danger')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    print("INFO: Iniciando servidor Flask a partir de main.py...")
    app.run(debug=True, host='0.0.0.0', port=5000)