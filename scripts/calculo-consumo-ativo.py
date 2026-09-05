import time
import argparse
import csv
from datetime import datetime

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("media_consumo_total", type=float, help="media do consumo total registrado")
parser.add_argument("media_residual", type=float, help="media do consumo residual total")

args = parser.parse_args()

ativo = args.media_consumo_total - args.media_residual
print(ativo)

nome = f"ativo-{args.media_consumo_total}-{args.media_residual}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#anexando valor final no log de testes
with open("../log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([nome, ativo, "null"])

