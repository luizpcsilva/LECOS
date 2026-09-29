import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

cons = pd.read_csv("log_medicao_sequencial.csv")
#cons = pd.read_csv("log_residual_com_frequency_demand.csv")
#cons = pd.read_csv("log_medicao_paralela.csv")

'''cons = cons.rename(columns={
    "stress-ng---cpu-6---cpu-method-queens--t-30-20260924_121141.csv": "Stress-ng",
    "24.4723993227684": "Info",
    "0.008322237037118985": "Média"
    })
'''

#print(cons.columns)

#cons = cons[~cons.astype(str).apply(lambda linha : linha.str.contains("n"),any(), axis=1)]

filtrado = cons.copy()

colunas = filtrado.columns.tolist()

colunas[0] = "Stress-ng"
colunas[1] = "Média"
colunas[2] = "Variância"

filtrado.columns = colunas
filtrado = filtrado.dropna(subset=["Variância"])

filtrado['método'] = filtrado['Stress-ng'].str.extract(r'-method-([^-]+)')

filtrado['cpu'] = filtrado["Stress-ng"].str.split('--').str[1]

filtrado['tempo'] = filtrado['Stress-ng'].str.extract(r't-([^-]+)')
#tempo = filtrado["Stress-ng"].str.split('--').str[3]
#filtrado['tempo'] = tempo.str.split('-').str[1]

filtrado['data'] = filtrado['Stress-ng'].str.extract(r't-30-([^-]+)')
#data = filtrado["Stress-ng"].str.split('-').str[14]
#filtrado["data"] = data.str.split('_').str[0]

grupo = filtrado.groupby("método")["Média"]
#variância = grupo.var()


repres = filtrado.plot(x="Média", y="método", kind="scatter", title="Média por método")



plt.show()
print(filtrado)
#print(variância)







