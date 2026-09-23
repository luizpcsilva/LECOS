import pandas as pd
import argparse
import csv
import sys

"""
Reduz a serie do scaphandre (testes/scaphandre/*.csv) a dois escalares: o Ce
medio de P1 e o de P2, em watts.

Equivale ao calculo-melhor-media-e-std.py do caminho RAPL, com uma diferenca: la
ha uma serie so, entao a janela e escolhida pela estabilidade da propria grandeza
reportada. Aqui ha duas, e a janela e escolhida pela estabilidade da FRACAO
ce_p1/(ce_p1+ce_p2) - numa deriva anticorrelacionada P1 cai o quanto P2 sobe, e o
total fica plano justamente quando a divisao muda mais rapido. A fracao tambem e
simetrica por construcao (frac_p1 + frac_p2 = 1, logo desvios identicos), entao a
mesma janela vale para os dois - a Eq. 5 compara as duas fatias no MESMO instante.

Separado da medicao de proposito: da para re-reduzir um csv arquivado sem remedir,
e cada medicao custa 180s de resfriamento mais 30s de estresse.

Imprime os dois valores em linhas separadas, para o protocolo.sh capturar com
{ read CE_P1; read CE_P2; }
"""

JANELA = 10   #amostras da janela usada no calculo da media

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("nome_csv", type=str, help="nome do arquivo que sera salvo no log")
parser.add_argument("caminho_csv", type=str, help="caminho do csv para calcular a media")

args = parser.parse_args()

df = pd.read_csv(args.caminho_csv)

if len(df) < JANELA:
    print(f"aviso: apenas {len(df)} amostras (janela pede {JANELA}); "
          f"usando a serie inteira", file=sys.stderr)

#obtem a melhor janela amostral pela estabilidade da fracao
soma_ce = df["ce_p1_uw"] + df["ce_p2_uw"]
df["frac_p1"] = (df["ce_p1_uw"] / soma_ce).where(soma_ce != 0)

tamanho_janela = min(JANELA, len(df))
df["desvio_padrao_janela"] = df["frac_p1"].rolling(window=tamanho_janela).std()

#o idxmin do pandas 3 levanta ValueError quando a serie inteira e NA, em vez de
#devolver NaN - acontece quando ce_p1 + ce_p2 e zero em toda amostra
try:
    indice_melhor_janela = df["desvio_padrao_janela"].idxmin()
except ValueError:
    indice_melhor_janela = None

if indice_melhor_janela is None or pd.isna(indice_melhor_janela):
    sys.exit("ce_p1 + ce_p2 e zero em todas as amostras; confira se os pids dos "
             "estressores aparecem no relatorio do scaphandre")

media_p1 = df["ce_p1_uw"].rolling(window=tamanho_janela).mean().loc[indice_melhor_janela]
media_p2 = df["ce_p2_uw"].rolling(window=tamanho_janela).mean().loc[indice_melhor_janela]
desvio_padrao = df.loc[indice_melhor_janela, "desvio_padrao_janela"]

#converte p watts
ce_p1 = media_p1 / 10**6
ce_p2 = media_p2 / 10**6

#anexando valores finais no log de testes
with open("log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow(["scaphandreP1-" + args.nome_csv, ce_p1, desvio_padrao])
    escritor.writerow(["scaphandreP2-" + args.nome_csv, ce_p2, desvio_padrao])

#imprimindo para protocolo.sh
print(ce_p1)
print(ce_p2)
