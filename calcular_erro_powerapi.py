# calcular_erro_powerapi.py
"""
Mesma logica de calcular_erro.py (Equacao 5, erro absoluto do modelo nos 55
pares), aplicada ao PowerAPI em vez do Scaphandre. Unica diferenca real: a
fonte do termo 1 (Ce) e o prefixo de papel no nome ("powerapi" em vez de
"scaphandre") -- dados/log_medicao_powerapi.csv e dados/filtro.ipynb que
converteu resultados_powerapifinal.csv pro mesmo formato. Termo 2 (baseline)
e C_S (dados/paralela.csv) sao os MESMOS arquivos ja usados pro Scaphandre --
o baseline e a mesma referencia de verdade pra qualquer modelo avaliado.
"""
import re
import pandas as pd

def par_de(nome):
    """extrai métodos de uma medição e transforma em tupla"""
    return tuple(sorted(re.findall(r'-method-([a-z0-9]+)--t-30', nome)))

def metodos_em_ordem(nome):
    """mesma busca acima, mas retorna como array (ordem importa)"""
    return re.findall(r'-method-([a-z0-9]+)--t-30', nome)


# --------------------- termo 1: Ce/C, nao depende de R ---------------------

pwr = pd.read_csv("dados/log_medicao_powerapi.csv", names=["nome", "ce_w", "std"])
#lembre-se que o df de medicao powerapi salva duas linhas por medicao: p1 e p2

pwr["par"] = pwr["nome"].apply(par_de)
pwr["papel"] = pwr["nome"].str.extract(r"^powerapi(P1|P2)-")
ordem = pwr["nome"].apply(metodos_em_ordem)
pwr["metodo"] = [m[0] if p == "P1" else m[1] for m, p in zip(ordem, pwr["papel"])]

ce_por_metodo = pwr.groupby(["par", "metodo"])["ce_w"].mean()  # media das 5 repeticoes

#mesma fonte de C_S ja usada e validada pro scaphandre (ver calcular_erro.py)
paralelo = pd.read_csv("dados/paralela.csv", index_col=0)
paralelo["par"] = paralelo["Stress-ng"].apply(par_de)
c_s_aprox = paralelo.groupby("par")["Média"].mean()

termo1 = (ce_por_metodo / c_s_aprox).rename("frac_ce")

faltando = set(pwr["par"]) - set(c_s_aprox.index)
if faltando:
    print(f"aviso: {len(faltando)} par(es) sem C_S em paralela.csv, serao ignorados: {faltando}")


# ------------- termo 2: baseline_Pi/A_S, ja calculado, um por cenario -------------

linhas_erro = []
detalhe = []

for tag in ("min", "max"):
    base = pd.read_csv(f"dados/baseline/baseline-R{tag}.csv")

    frac_baseline = {}
    for _, r in base.iterrows():
        par = tuple(sorted([r["P1"], r["P2"]]))
        frac_baseline[(par, r["P1"])] = r["baseline_P1"] / r["A_S"]
        frac_baseline[(par, r["P2"])] = r["baseline_P2"] / r["A_S"]

    frac_baseline = pd.Series(frac_baseline, name="frac_baseline")
    frac_baseline.index = pd.MultiIndex.from_tuples(frac_baseline.index, names=["par", "metodo"])

    comparacao = pd.DataFrame({"frac_ce": termo1, "frac_baseline": frac_baseline}).dropna()

    comparacao["erro_abs"] = (comparacao["frac_ce"] - comparacao["frac_baseline"]).abs()
    comparacao["cenario"] = tag
    detalhe.append(comparacao.reset_index())

    ae_por_par = comparacao.groupby(level="par")["erro_abs"].mean()
    for par, ae in ae_por_par.items():
        linhas_erro.append({"cenario": tag, "par": par, "AE": ae})

detalhe = pd.concat(detalhe, ignore_index=True)
detalhe.to_csv("dados/erro-detalhado-powerapi.csv", index=False)

erro = pd.DataFrame(linhas_erro)
erro.to_csv("dados/erro-por-par-powerapi.csv", index=False)

resumo = erro.groupby("cenario")["AE"].agg(media="mean", maximo="max")
print(resumo.to_string())
resumo.to_csv("dados/erro-resumo-powerapi.csv")

pior = erro.loc[erro.groupby("cenario")["AE"].idxmax()]
print()
print("pior par por cenario:")
print(pior.to_string(index=False))
