import subprocess
import argparse
import time
from pyJoules.device.rapl_device import RaplCoreDomain
from pyJoules.handler.csv_handler import CSVHandler
from pyJoules.energy_meter import EnergyContext


def stress():
	parser = argparse.ArgumentParser(description="")
	parser.add_argument("func1", type=str, help="função 1 com todos os argumentos padrao stress-ng")
	parser.add_argument("func2", type=str, help="função 2 com todos os argumentos padrao stress-ng")
	parser.add_argument("nomearq", type=str, default="energia.csv", help="nome do arquivo para salvar resultados .csv")
	
	args = parser.parse_args()

	cmd1 = args.func1.split()
	cmd2 = args.func2.split()
	 
	csv_handler = CSVHandler(args.nomearq)
	
	with EnergyContext(domains=[RaplCoreDomain(0)], handler=csv_handler) as ctx:
		p1 = subprocess.Popen(cmd1)
		p2 = subprocess.Popen(cmd2)

		while p1.poll() is None or p2.poll() is None:
			ctx.record(tag="stress")
			time.sleep(1)
			
	csv_handler.save_data()
 
stress()

