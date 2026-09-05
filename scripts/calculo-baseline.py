import time
import argparse
import csv
from datetime import datetime

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("consumo-ativo-total", type=float, help="consumo ativo total da medicao paralela")
parser.add_argument("consumo-ativo-P1", type=float, help="media do consumo ativo de p1")
parser.add_argument("consumo-ativo-P2", type=float, help="media do consumo ativo de p2")

args = parser.parse_args()

baseline_p1 = args.consumo_ativo_total * (args.consumo_ativo_P1 / args.consumo_ativo_P1 + args.consumo_ativo_P2)
print(baseline_p1)
baseline_p2 = args.consumo_ativo_total * (args.consumo_ativo_P2 / args.consumo_ativo_P1 + args.consumo_ativo_P2)
print(baseline_p2)

nome1 = f"baselineP1-{baseline_p1}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
nome2 = f"baselineP2-{baseline_p2}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#anexando valor final no log de testes
with open("../log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([nome1, baseline_p1, "null"])
    escritor.writerow([nome2, baseline_p2, "null"])

