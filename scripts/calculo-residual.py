import time
import argparse
import csv
from datetime import datetime

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("media_idle", type=float, help="media do consumo idle")
parser.add_argument("media_residual_total", type=float, help="media do consumo residual total")

args = parser.parse_args()

residual = args.media_residual_total - args.media_idle
print(residual)

nome = f"residual-{args.media_residual_total}-{args.media_idle}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#anexando valor final no log de testes
with open("../log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([nome, residual, "null"])

