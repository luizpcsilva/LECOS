import time
import argparse
import csv
import json
import os
import sys
import threading
from datetime import datetime
import subprocess

import pandas as pd

"""
Mede o consumo estimado (Ce) de DOIS estressores executados em paralelo, usando o
exportador JSON do scaphandre.

O exportador json amostra no proprio timer (--step), diferente do exportador
prometheus, em que a janela de medicao era definida por quem fazia a requisicao.
O relatorio sai no stdout do container (o scaphandre imprime no stdout quando -f
e omitido), e e acumulado em memoria ate os estressores terminarem - nada e
escrito em disco durante a janela medida.

Ao fim, imprime a media de Ce de P1 e de P2 (em watts) em linhas separadas, para
o protocolo.sh capturar com { read CE_P1; read CE_P2; }
"""

NOME_CONTAINER = "scaphandre"
MAX_CONSUMIDORES = 50   #o default de 10 corta workers do stress-ng
COM_RECURSOS = True     #flag --resources: habilita cpu_p1_pct/cpu_p2_pct
SALVAR_BRUTO = True     #arquiva o json cru DEPOIS da medicao, pra depurar
ESPERA = 2              #segundos ate os workers do stress-ng nascerem
JANELA = 10             #amostras da janela usada no calculo da media
TIMEOUT_PRONTO = 30     #segundos esperando as 2 primeiras amostras do scaphandre
TIMEOUT_PARADA = 30     #segundos esperando o container morrer apos o docker stop
BLOCO = 65536           #tamanho da leitura do pipe, em bytes

COLUNAS = [
    "epoch_s",        #host.timestamp do scaphandre
    "t_rel_s",        #segundos desde o inicio dos estressores
    "delta_t_s",      #espacamento ate a amostra anterior - detecta passo perdido
    "ce_p1_uw",
    "ce_p2_uw",
    "host_uw",        #host.consumption - psys quando a placa expoe o dominio
    "socket0_uw",     #sockets[id=0] - package, mesma base do rapl do lecos
    "soma_todos_uw",
    "cpu_p1_pct",
    "cpu_p2_pct",
    "n_pids_p1",
    "n_pids_p2",
]

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("freq", type=float, help="frequencia da amostragem (em segundos)")
parser.add_argument("estressor", type=str, help="estressor alvo P1")
parser.add_argument("estressor2", type=str, help="estressor alvo P2")

args = parser.parse_args()
nome_cenario = args.estressor + "-" + args.estressor2
args.estressor = args.estressor.split()
args.estressor2 = args.estressor2.split()


def descendentes(pid):
    """retorna o proprio pid e todos os seus descendentes, como um set"""
    encontrados = {pid}
    pilha = [pid]
    while pilha:
        atual = pilha.pop()
        try:
            tarefas = os.listdir(f"/proc/{atual}/task")
        except OSError:
            continue   # o processo morreu entre a enumeracao e a leitura
        for tid in tarefas:
            try:
                with open(f"/proc/{atual}/task/{tid}/children") as children:
                    filhos = children.read().split()
            except OSError:
                continue
            for filho in map(int, filhos):
                if filho not in encontrados:
                    encontrados.add(filho)
                    pilha.append(filho)
    return encontrados


def montar_comando():
    """monta a chamada do container do scaphandre com o exportador json.

    sem -f o relatorio vai para o stdout; sem -d porque precisamos desse stdout;
    sem -ti porque o tty mudaria o buffering; sem -p porque nao ha mais endpoint"""
    comando = [
        "docker", "run", "--rm", "--name", NOME_CONTAINER, "--privileged",
        "-v", "/sys/class/powercap:/sys/class/powercap",
        "-v", "/proc:/proc",
        "hubblo/scaphandre", "json",
        "-s", str(max(1, int(args.freq))),
        "--max-top-consumers", str(MAX_CONSUMIDORES),
    ]
    if COM_RECURSOS:
        comando.append("--resources")
    return comando


def drenar(fluxo, acumulador):
    """le o fluxo em blocos ate o eof, acumulando em memoria.

    precisa rodar em thread: o pipe do linux tem 64 kib de buffer e a saida do
    scaphandre com 50 consumidores passa disso facil. sem drenar, o scaphandre
    bloqueia no write e para de medir no meio da janela"""
    try:
        for bloco in iter(lambda: fluxo.read(BLOCO), ""):
            acumulador.append(bloco)
    except (ValueError, OSError):
        pass   # o fluxo foi fechado junto com o processo
    finally:
        fluxo.close()


def esperar_primeira_amostra(processo, blocos, blocos_erro, minimo=2):
    """espera o scaphandre emitir 'minimo' amostras ANTES de carregar a maquina.

    a primeira amostra nao tem janela anterior e vem zerada; esperar duas garante
    que o sensor completou um ciclo de leitura do rapl. substitui a sondagem do
    /metrics - achado de 2026-09-22, contador congelado por 8s sob carga.

    nao aborta no timeout: se o rust estiver bufferizando o stdout, as amostras
    podem chegar so no fim. a validacao real acontece depois do parse, quando se
    sabe quantas amostras caem dentro da janela dos estressores. mas aborta na
    hora se o container morreu, porque ai nao ha o que esperar"""
    inicio = time.time()
    while time.time() - inicio < TIMEOUT_PRONTO:
        if "".join(blocos).count('"host"') >= minimo:
            return True
        if processo.poll() is not None:
            sys.exit(f"container do scaphandre encerrou com codigo {processo.returncode} "
                     f"antes de emitir {minimo} amostras:\n{''.join(blocos_erro)}")
        time.sleep(0.5)

    print(f"aviso: scaphandre nao emitiu {minimo} amostras em {TIMEOUT_PRONTO}s; "
          f"seguindo mesmo assim", file=sys.stderr)
    return False


def carregar_relatorios(texto):
    """converte a saida do scaphandre em lista de amostras.

    o exportador json escreve um array incremental: abre com '[', vai anexando
    objetos separados por virgula e fecha com ']' na saida normal. como
    encerramos o container com 'docker stop' (sigterm), o ']' pode nao sair -
    entao fechamos o array por conta propria antes de desistir"""
    abertura = texto.find("[")
    if abertura == -1:
        sys.exit("saida do scaphandre nao contem nenhum relatorio json")
    texto = texto[abertura:].rstrip()

    #tenta em ordem: array completo; array a que falta so o ']' (caso comum do
    #sigterm, em que a ultima amostra esta inteira); array cujo ultimo objeto
    #ficou pela metade, ai descartado
    candidatos = [texto, texto + "]"]
    for marca in ("},", "}"):
        corte = texto.rfind(marca)
        if corte != -1:
            candidatos.append(texto[:corte + 1] + "]")

    for candidato in candidatos:
        try:
            relatorios = json.loads(candidato)
        except json.JSONDecodeError:
            continue
        if relatorios:
            return relatorios

    sys.exit("saida do scaphandre nao tem nenhuma amostra completa")


def cpu_do_consumidor(consumidor):
    """resources_usage so existe com a flag --resources e os campos vem como
    string. devolve 0 quando a flag esta desligada ou o campo nao parseia"""
    recursos = consumidor.get("resources_usage") or {}
    try:
        return float(recursos.get("cpu_usage", 0))
    except (TypeError, ValueError):
        return 0.0


def valor(dicionario, chave):
    """le um numero de um dicionario tolerando chave ausente e None"""
    bruto = dicionario.get(chave)
    try:
        return float(bruto)
    except (TypeError, ValueError):
        return 0.0


def agregar(relatorios, pids_p1, pids_p2, epoch_inicio, epoch_abertura, epoch_fim):
    """soma o consumo por conjunto de pid em cada amostra dentro da janela.

    a separacao e por arvore de pids porque o stress-ng apaga o metodo dos seus
    workers: filtrar por cmdline so funciona para --cpu contra --matrix, e em 10
    dos 12 testes da tabela iii os dois lados sao --cpu-method"""
    linhas = []
    epoch_anterior = None

    for amostra in relatorios:
        host = amostra.get("host") or {}
        epoch = valor(host, "timestamp")

        #so interessa o intervalo em que os dois estressores estavam de fato
        #rodando com a arvore de pids ja enumerada
        if not (epoch_abertura <= epoch <= epoch_fim):
            continue

        socket0_uw = 0.0
        for socket in amostra.get("sockets") or []:
            if socket.get("id") == 0:
                socket0_uw = valor(socket, "consumption")
                break

        ce_p1 = ce_p2 = soma_todos = cpu_p1 = cpu_p2 = 0.0
        n_p1 = n_p2 = 0

        for consumidor in amostra.get("consumers") or []:
            pid = consumidor.get("pid")
            potencia = valor(consumidor, "consumption")
            soma_todos += potencia
            if pid in pids_p1:
                ce_p1 += potencia
                cpu_p1 += cpu_do_consumidor(consumidor)
                n_p1 += 1
            elif pid in pids_p2:
                ce_p2 += potencia
                cpu_p2 += cpu_do_consumidor(consumidor)
                n_p2 += 1

        delta_t = epoch - epoch_anterior if epoch_anterior is not None else 0.0
        epoch_anterior = epoch

        linhas.append([epoch, epoch - epoch_inicio, delta_t, ce_p1, ce_p2,
                       valor(host, "consumption"), socket0_uw, soma_todos,
                       cpu_p1, cpu_p2, n_p1, n_p2])

    return linhas


def encerrar_estressores(*processos):
    """mata estressor que tenha sobrevivido a uma falha.

    no caminho normal os dois ja sairam pelo -t e isto e no-op. importa quando o
    segundo Popen falha: sem isso o primeiro ficaria queimando cpu e
    contaminaria a rodada seguinte do agendador"""
    for processo in processos:
        if processo is not None and processo.poll() is None:
            processo.kill()
            processo.wait()


def encerrar_scaphandre(processo, threads):
    """para o container e espera as threads de drenagem consumirem o resto.

    o docker rm -f garante que nao sobra container para a proxima rodada do
    agendador, que roda 165 vezes seguidas e quebraria no --name duplicado"""
    for comando in (["docker", "stop", NOME_CONTAINER],
                    ["docker", "rm", "-f", NOME_CONTAINER]):
        try:
            subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

    try:
        processo.wait(timeout=TIMEOUT_PARADA)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait()

    for thread in threads:
        thread.join(timeout=5)


#--------------------- Inicio Medição ----------------------
carimbo_execucao = datetime.now().strftime("%Y%m%d_%H%M%S")

processo_scaphandre = subprocess.Popen(
    montar_comando(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

blocos_json, blocos_erro = [], []
threads = []
for fluxo, destino in ((processo_scaphandre.stdout, blocos_json),
                       (processo_scaphandre.stderr, blocos_erro)):
    thread = threading.Thread(target=drenar, args=(fluxo, destino), daemon=True)
    thread.start()
    threads.append(thread)

processo_estressor = processo_estressor2 = None

try:
    #garante que o sensor ja completou um ciclo ANTES de carregar a maquina
    esperar_primeira_amostra(processo_scaphandre, blocos_json, blocos_erro)

    epoch_inicio = time.time()
    processo_estressor = subprocess.Popen(args.estressor, stdout=subprocess.DEVNULL)
    processo_estressor2 = subprocess.Popen(args.estressor2, stdout=subprocess.DEVNULL)

    #espera os workers nascerem e enumera a arvore de cada estressor uma unica vez
    time.sleep(ESPERA)
    pids_p1 = descendentes(processo_estressor.pid)
    pids_p2 = descendentes(processo_estressor2.pid)
    epoch_abertura = time.time()

    processo_estressor.wait()
    processo_estressor2.wait()
    epoch_fim = time.time()
finally:
    encerrar_estressores(processo_estressor, processo_estressor2)
    encerrar_scaphandre(processo_scaphandre, threads)
#--------------------- Fim Medição -------------------------

texto_json = "".join(blocos_json)
os.makedirs("testes/scaphandre", exist_ok=True)

#arquiva o json cru so agora, depois do fim da medicao
if SALVAR_BRUTO:
    os.makedirs("testes/scaphandre/bruto", exist_ok=True)
    with open(f"testes/scaphandre/bruto/{carimbo_execucao}.json", "w") as bruto:
        bruto.write(texto_json)

relatorios = carregar_relatorios(texto_json)
output = agregar(relatorios, pids_p1, pids_p2, epoch_inicio, epoch_abertura, epoch_fim)

if not output:
    sys.exit(f"nenhuma das {len(relatorios)} amostras do scaphandre caiu na janela "
             f"dos estressores; confira o passo (-s) e a duracao (-t)")

if len(output) < JANELA:
    print(f"aviso: apenas {len(output)} amostras dentro da janela dos estressores "
          f"(janela pede {JANELA}); usando a serie inteira", file=sys.stderr)

#criando output em csv do experimento
nome_csv = (
    nome_cenario.replace(" ", "-") + "-" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
)
caminho_csv = "testes/scaphandre/" + nome_csv
with open(caminho_csv, mode="w") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(COLUNAS)
    escritor.writerows(output)

#calcula a melhor media
df = pd.DataFrame(output, columns=COLUNAS)
soma_ce = df["ce_p1_uw"] + df["ce_p2_uw"]
df["frac_p1"] = (df["ce_p1_uw"] / soma_ce).where(soma_ce != 0)

#a janela e escolhida pela estabilidade da FRACAO, nao do total: numa deriva
#anticorrelacionada o total fica plano justamente quando a divisao muda mais rapido
tamanho_janela = min(JANELA, len(df))
desvio_padrao_janela = df["frac_p1"].rolling(window=tamanho_janela).std()
indice_melhor_janela = desvio_padrao_janela.idxmin()

if pd.isna(indice_melhor_janela):
    sys.exit("nao foi possivel calcular a janela: ce_p1 + ce_p2 e zero em todas as "
             "amostras; confira se os pids dos estressores aparecem no relatorio")

media_p1 = df["ce_p1_uw"].rolling(window=tamanho_janela).mean().loc[indice_melhor_janela]
media_p2 = df["ce_p2_uw"].rolling(window=tamanho_janela).mean().loc[indice_melhor_janela]
desvio_padrao = desvio_padrao_janela.loc[indice_melhor_janela]

#converte p watts
ce_p1 = media_p1 / 10**6
ce_p2 = media_p2 / 10**6

#anexando valores finais no log de testes
with open("log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow(["scaphandreP1-" + nome_csv, ce_p1, desvio_padrao])
    escritor.writerow(["scaphandreP2-" + nome_csv, ce_p2, desvio_padrao])

#imprimindo para protocolo.sh
print(ce_p1)
print(ce_p2)
