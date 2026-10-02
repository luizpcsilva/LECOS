# dados/calcular_erro.py
"""
Aplica a Equacao 5 (erro absoluto do modelo) aos 55 pares.
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

#abre o df e da nome as colunas
sca = pd.read_csv("dados/log_medicao_scaphandre.csv", names=["nome", "ce_w", "std"])
#lembre-se que o df de medicaos caphandre salva duas linhas por medicao: p1 e p2

#extrai os dois estressores em tupla
sca["par"] = sca["nome"].apply(par_de)
#define se aquele gasto é p1 ou p2
sca["papel"] = sca["nome"].str.extract(r"^scaphandre(P1|P2)-")
#adiciona o nome do metodo na linha p1 x p2
ordem = sca["nome"].apply(metodos_em_ordem)
sca["metodo"] = [m[0] if p == "P1" else m[1] for m, p in zip(ordem, sca["papel"])]

#calcula a media agrupada
ce_por_metodo = sca.groupby(["par", "metodo"])["ce_w"].mean()  # media das 5 repeticoes

#abaixo, obtem a metrica host_uw via medicao paralela
paralelo = pd.read_csv("dados/paralela.csv", index_col=0)
paralelo["par"] = paralelo["Stress-ng"].apply(par_de) 
c_s_aprox = paralelo.groupby("par")["Média"].mean()  # aproximacao de host_uw (ver nota acima)

#calcula proporcao scaphandre e salva em Series
termo1 = (ce_por_metodo / c_s_aprox).rename("frac_ce")  # Series indexado por (par, metodo)

# checagem de cobertura: todo par do scaphandre precisa ter C_S aproximado
faltando = set(sca["par"]) - set(c_s_aprox.index)
if faltando:
    print(f"aviso: {len(faltando)} par(es) sem C_S em paralela.csv, serao ignorados: {faltando}")


# ------------- termo 2: baseline_Pi/A_S, ja calculado, um por cenario -------------

linhas_erro = []
detalhe = []

#itera pelo baseline min e baseline max
for tag in ("min", "max"):
    base = pd.read_csv(f"dados/baseline/baseline-R{tag}.csv")

    frac_baseline = {}
    for _, r in base.iterrows():
        #separa p1 e p2 do baseline e calcula a proporção dicionario metodo x tupla
        par = tuple(sorted([r["P1"], r["P2"]]))
        frac_baseline[(par, r["P1"])] = r["baseline_P1"] / r["A_S"]
        frac_baseline[(par, r["P2"])] = r["baseline_P2"] / r["A_S"]
        #ex: frac_baseline[(('ackermann','queens'), 'ackermann')] = 7,129463 / 14,617558 = 0,48773

    #converte o dicionario eum uma series
    frac_baseline = pd.Series(frac_baseline, name="frac_baseline")
    frac_baseline.index = pd.MultiIndex.from_tuples(frac_baseline.index, names=["par", "metodo"])

    #junta as series da proporcao scaphandre com proporcao baseline, unindo pelo indice
    comparacao = pd.DataFrame({"frac_ce": termo1, "frac_baseline": frac_baseline}).dropna()

    #calcula o erro absoluto p cada linha subtraindo as duas proporções
    comparacao["erro_abs"] = (comparacao["frac_ce"] - comparacao["frac_baseline"]).abs()
    #adiciona tag(min/max)
    comparacao["cenario"] = tag
    detalhe.append(comparacao.reset_index())

    #calcula o erro medio para os dois pares em cada cenario de medicao
    ae_por_par = comparacao.groupby(level="par")["erro_abs"].mean()  # media entre P1 e P2 do par
    for par, ae in ae_por_par.items():
        linhas_erro.append({"cenario": tag, "par": par, "AE": ae})

detalhe = pd.concat(detalhe, ignore_index=True)
detalhe.to_csv("dados/erro-detalhado.csv", index=False)

erro = pd.DataFrame(linhas_erro)
erro.to_csv("dados/erro-por-par.csv", index=False)

resumo = erro.groupby("cenario")["AE"].agg(media="mean", maximo="max")
print(resumo.to_string())
resumo.to_csv("dados/erro-resumo.csv")

pior = erro.loc[erro.groupby("cenario")["AE"].idxmax()]
print()
print("pior par por cenario:")
print(pior.to_string(index=False))