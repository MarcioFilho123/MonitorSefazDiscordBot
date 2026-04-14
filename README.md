Este bot foi desenvolvido para monitorar a disponibilidade 
e o tempo de resposta (latência) dos servidores da SEFAZ 
dos estados do Acre, Amazonas e Rondônia.

---------------------------------------------------------
1. REQUISITOS
---------------------------------------------------------
Para rodar este bot, você precisará de:
* Python 3.8 ou superior
* Bibliotecas listadas em 'requirements.txt'
  (discord.py, python-dotenv, requests, aiohttp, bs4)

---------------------------------------------------------
2. INSTALAÇÃO
---------------------------------------------------------
1. Instale as dependências necessárias:
   pip install discord.py python-dotenv requests aiohttp beautifulsoup4

2. Crie um arquivo chamado '.env' na mesma pasta do script.
3. Adicione as seguintes informações no seu '.env':

   BOT_TOKEN=SEU_TOKEN_AQUI
   CANAL_NOTIFICACAO=ID_DO_CANAL_DE_TEXTO

---------------------------------------------------------
3. FUNCIONALIDADES
---------------------------------------------------------
* Monitoramento em Tempo Real: Verifica se o site da SEFAZ
  está Online, Instável ou Fora do Ar.
* Latência (TecnoSpeed): Faz scraping do Monitor TecnoSpeed
  para informar a velocidade da conexão (Normal, Lento, etc).
* Notificação Automática: Avisa no canal configurado quando
  um serviço que estava fora do ar volta a ficar online.
* Atualização Automática: O bot checa o status a cada 10 min.

---------------------------------------------------------
4. COMANDOS (Slash Commands /)
---------------------------------------------------------
/acre      - Status e latência da SEFAZ Acre.
/amazonas  - Status e latência da SEFAZ Amazonas.
/rondonia  - Status e latência da SEFAZ Rondônia.
/verestados - Relatório completo dos 3 estados de uma vez.

---------------------------------------------------------
5. COMO ADICIONAR NOVOS ESTADOS
---------------------------------------------------------
Para expandir o bot para outros estados, siga estes passos:

1. No dicionário 'SEFAZ_URLS', adicione o nome e o site.
2. No dicionário 'MONITOR_URLS', adicione o link do monitor.
3. No dicionário 'historico_status', adicione a chave do estado.
4. Crie um novo comando '@bot.tree.command' copiando a 
   estrutura dos comandos existentes.
