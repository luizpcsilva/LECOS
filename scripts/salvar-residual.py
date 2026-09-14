import time
import argparse
import csv
from datetime import datetime

#configuração dos argumentos passados via terminal
parser = argparse.ArgumentParser(description="")
parser.add_argument("comando_estresse", type=str, help="comando utilizado para estresse:")
parser.add_argument("media_residual_total", type=float, help="media do consumo residual total")
args = parser.parse_args()

nome_estresse = "residual-"+args.comando_estresse.replace(" ", "-") + "-" + datetime.now().strftime('%Y%m%d_%H%M%S')

residual = args.media_residual_total

#anexando valor final no log de testes
with open("log.csv", mode="a") as log_csv:
    escritor = csv.writer(log_csv)
    escritor.writerow([nome_estresse, residual, "null"])

