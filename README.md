## Iniciar o Projeto

Este projeto é um web app básico construído com Flask. Para iniciá-lo e entender seu funcionamento, siga as instruções abaixo:

### Dependências

Certifique-se de ter Python 3 instalado em seu sistema. As demais dependências do projeto são gerenciadas via `requirements.txt`.

### Como Executar

1. Clone o repositório (se aplicável).
2. Navegue até o diretório raiz do projeto no terminal.
3. Instale as dependências: `pip install -r requirements.txt`
4. Execute o servidor de desenvolvimento: `python main.py`
5. O aplicativo estará disponível em `http://127.0.0.1:5000/`.

###  Objetivo e Como Funciona

Este projeto se chama **Ticket AI**, capacidade de rodar servidor flask local com Gemini para resolução de problemas de usuários que abrirem um ticket, um chamado. Ótimo para pequenas equipes. Rastreamento e otimização com assistente Gemini AI.

Três rotas;

/ -> Página inicial.
/admin -> Para os administradores com acesso Token único.
/admin/ticket -> Tickets abertos com geração de resposta Gemini AI.
/admin/ticket/$numero -> Sessão do ticket aberto.
/ticket -> Para usuários que abriram um ticket.

Imagine um usuário que tem algum problema referente aplicação da plataforma criada por um Xdev. Após o usuário ter criado um ticket, um administrador poderá checar esse problema, feedback ou dúvida. Gemini irá gerar uma resposta pré-definida para o usuário a ser enviado para o e-mail. 
Isso facilita o tempo de resposta que um ser humano precisava para resolver um problema. 
IA usada do Gemini é o modelo `gemini-1.5-flash-latest`. Rápido e eficiente.

> [!warning]
> Observação, no arquivo `main.py` deve ser alterado a API KEY na linha 18. 
> `GEMINI_API_KEY = "AIzaSyA....." # Sua chave API mais recente`
> Obtenha em: https://aistudio.google.com/app/apikey
> Substitua o token na linha 11 no arquivo `main.py` e não compartilhe.
> `ADMIN_TOKEN = "seu-token-super-secreto-123"`

Agora veja algumas imagens:

