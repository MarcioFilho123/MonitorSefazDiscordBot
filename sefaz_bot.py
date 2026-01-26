import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import re
import requests
import aiohttp
from bs4 import BeautifulSoup

# Carrega o .env  - necessário (tem que estar na mesma pasta)
load_dotenv(Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_NOTIFICACAO = int(os.getenv("CANAL_NOTIFICACAO", 0))  # Canal que vai ser colocado - falta definir no .en

if not BOT_TOKEN:
    raise ValueError("❌ ERRO: Token não encontrado. Verifique o arquivo .env (BOT_TOKEN=...)")

if CANAL_NOTIFICACAO == 0:
    print("⚠️ Atenção: CANAL_NOTIFICACAO não definido no .env")

#Configuração do bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

#SEFAZ - necessário, é o site da SEFAZ e mostra o status dele
SEFAZ_URLS = {
    "acre": "https://www.sefaz.ac.gov.br",
    "amazonas": "https://www.sefaz.am.gov.br", 
    "rondonia": "https://www.sefin.ro.gov.br"
    #se for adicionar um outro estado, procura o link da sefaz e coloca nesse padrão
    #"estado": "https://linkdosefazdoestado"
}

#Monitor TecnoSpeed - mostra a VELOCIDADE da conexão
MONITOR_URLS = {
    "acre": "https://monitor.tecnospeed.com.br/?filter-uf=ac&filter-type-chart=line&filter-doc=nfce",
    "amazonas": "https://monitor.tecnospeed.com.br/?filter-uf=am&filter-type-chart=line&filter-doc=nfce",
    "rondonia": "https://monitor.tecnospeed.com.br/?filter-uf=ro&filter-type-chart=line&filter-doc=nfce"
    #se for adicionar um outro estado, procura no site do monitor tecnospeed e coloca nesse padrão
    #"estado": "https://linkdomonitordoestado"
}

#User-Agents - necessário para poder acessar o site
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0 (Edition GX)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
]

def gerar_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

def classificar_tempo_resposta(tempo_segundos: float) -> str: #cria os parâmetros em relação a VELOCIDADE
    """
    Classifica o tempo de resposta conforme a tabela do monitor:
    - 🟢 Normal: <= 2s
    - 🟡 Lento: <= 5s  
    - 🟠 Muito lento: < 30s
    - 🔴 Temporal: > 30s
    """
    if tempo_segundos <= 2:
        return f"🟢 {tempo_segundos}s (Normal)"
    elif tempo_segundos <= 5:
        return f"🟡 {tempo_segundos}s (Lento)"
    elif tempo_segundos < 30:
        return f"🟠 {tempo_segundos}s (Muito lento)"
    else:
        return f"🔴 {tempo_segundos}s (Temporal)"

#Testa o site da SEFAZ - necessário, mostra o status do SITE
def verificar_site(url):
    try:
        resposta = requests.get(url, timeout=5, headers=gerar_headers())
        if resposta.status_code == 200:
            return "🟢 Online"
        else:
            return f"🟡 Instável (código {resposta.status_code})"
    except requests.exceptions.RequestException:
        return "🔴 Fora do ar"

#Procura o tempo de resposta no HTML usando o scraping HTML - necessário pro Monitor
async def buscar_tempo_resposta(uf: str):
    url = MONITOR_URLS[uf]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=gerar_headers(), timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    #Método 1: Procurar em scripts JavaScript - necessário
                    padroes_script = [
                        r'data:\s*\[([^\]]+)\]',  # Procura arrays data: [1.2, 3.4, 5.6]
                        r'\[([0-9.,\s]+)\]',  # Procura arrays numéricos
                        r'y:\s*([0-9.]+)',  # Procura valores y: 1.23
                    ]
                    
                    #Procura em todas as tags script - necessário
                    soup = BeautifulSoup(html, 'html.parser')
                    scripts = soup.find_all('script')                    
                    todos_valores = []
                    for script in scripts:
                        if script.string:
                            script_text = script.string
                            
                            #Procura por arrays de dados - necessário
                            for padrao in padroes_script:
                                matches = re.findall(padrao, script_text)
                                for match in matches:
                                    #Se for uma string com múltiplos valores
                                    if ',' in str(match):
                                        try:
                                            valores = [float(x.strip()) for x in str(match).split(',') if x.strip() and x.replace('.', '').isdigit()]
                                            todos_valores.extend(valores)
                                        except:
                                            continue
                                    #Se for um valor único
                                    else:
                                        try:
                                            valor = float(match)
                                            if valor > 0:  #Filtra os valores e só retorna ok válidos
                                                todos_valores.append(valor)
                                        except:
                                            continue
                    
                    #Pega o último valor encontrado (ou seja o que vai ser mostrado)
                    if todos_valores:
                        ultimo_valor = todos_valores[-1]
                        return classificar_tempo_resposta(ultimo_valor)
                    
                    #Método 2 (se não achar):Procura em elementos HTML por textos com segundos
                    padrao_segundos = r'([0-9]+\.?[0-9]*)\s*s'
                    matches_segundos = re.findall(padrao_segundos, html)
                    if matches_segundos:
                        try:
                            ultimo_segundo = float(matches_segundos[-1])
                            return classificar_tempo_resposta(ultimo_segundo)
                        except:
                            pass
                    
                    return "❌ Dados não encontrados"
                else:
                    return f"⚠️ Site retornou erro {response.status}"
                    
    #os erros - necessário até certo ponto
    except asyncio.TimeoutError:
        return "⚠️ Timeout na consulta"
    except aiohttp.ClientError as e:
        return f"⚠️ Erro de conexão: {e}"
    except Exception as e:
        return f"⚠️ Erro inesperado: {e}"

#Histórico de status para notificação - necessário
historico_status = {
    "acre": None,
    "amazonas": None,
    "rondonia": None
}

async def checar_volta_ao_ar():
    channel = bot.get_channel(CANAL_NOTIFICACAO)
    if not channel:
        return
    for uf in ["acre", "amazonas", "rondonia"]:
        status = verificar_site(SEFAZ_URLS[uf])
        if historico_status[uf] in ["🔴 Fora do ar", "🟡 Instável"] and status == "🟢 Online":
            await channel.send(f"✅ **{uf.capitalize()}** voltou ao ar!")
        historico_status[uf] = status

#Inicialização - necessário
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user} (id: {bot.user.id})")
    checagem_periodica.start()

#Checagem a cada 10 minutos - botei um tempo alto pra economizar tempo e cache - opcional
@tasks.loop(minutes=10)
async def checagem_periodica():
    try:
        await checar_volta_ao_ar()
    except Exception as e:
        print(f"❌ Erro na checagem periódica: {e}")

#COMANDOS DO /
#Acre
@bot.tree.command(name="acre", description="Verifica o status da SEFAZ e tempo de resposta do Acre")
async def acre(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    status = verificar_site(SEFAZ_URLS["acre"])
    tempo = await buscar_tempo_resposta("acre")
    historico_status["acre"] = status
    await interaction.followup.send(f"🌎 **SEFAZ Acre:** {status}\n📈 **Tempo de resposta:** {tempo}")

#Amazonas
@bot.tree.command(name="amazonas", description="Verifica o status da SEFAZ e tempo de resposta do Amazonas")
async def amazonas(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    status = verificar_site(SEFAZ_URLS["amazonas"])
    tempo = await buscar_tempo_resposta("amazonas")
    historico_status["amazonas"] = status
    await interaction.followup.send(f"🌎 **SEFAZ Amazonas:** {status}\n📈 **Tempo de resposta:** {tempo}")

#Rondônia
@bot.tree.command(name="rondonia", description="Verifica o status da SEFAZ e tempo de resposta de Rondônia")
async def rondonia(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    status = verificar_site(SEFAZ_URLS["rondonia"])
    tempo = await buscar_tempo_resposta("rondonia")
    historico_status["rondonia"] = status
    await interaction.followup.send(f"🌎 **SEFAZ Rondônia:** {status}\n📈 **Tempo de resposta:** {tempo}")

#Verestados
@bot.tree.command(name="verestados", description="Mostra o status e tempo de resposta dos 3 estados (AC, AM, RO)")
async def verestados(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    resultados = []
    for uf in ["acre", "amazonas", "rondonia"]: #verifica os 3 e salva para aparecer depois
        status = verificar_site(SEFAZ_URLS[uf])
        tempo = await buscar_tempo_resposta(uf)
        historico_status[uf] = status
        resultados.append(f"**{uf.capitalize()}** → {status} | ⏱️ {tempo}")    
    mensagem = "\n".join(resultados)
    await interaction.followup.send(f"📊 **Monitoramento SEFAZ**\n{mensagem}")

#se for adicionar um outro estado, não se esqueça de colocar o nome do estado em:
#name, def, SEFAZ_URLS[], buscar_tempo_resposta, histórico_status

#bot.run e bot_token - necessário
if __name__ == "__main__":
    bot.run(BOT_TOKEN)