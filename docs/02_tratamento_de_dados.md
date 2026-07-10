No passo anterior, utilizamos um script para monitorar os contadores de energia do processador e o timestamp da medição. No entanto, para visualizarmos o comportamento da aplicação executada é necessário tratar os dados coletados. 

Nessa etapa, vamos automatizar o cálculo da **Potência Média (em Watts)** entre as medições realizadas e, em seguida, utilizaremos as bibliotecas `numpy` e `matplotlib` para gerarmos uma visualização gráfica do consumo de energia monitorado.
# Potência Média
A física nos diz que a Potência é a variação de energia dividida pela variação do tempo:
$$P = \frac{\Delta E}{\Delta t}$$

Logo, suponha que as duas medições abaixo foram extraídos do arquivo gerado na etapa anterior, sendo a primeira coluna referente a energia acumulada em microjoules e a segunda coluna o contador de tempo (timestamp) em segundos.
```
99981016814 1646987.469997645 
100036646188 1646988.470136542 
```
Com uma subtração básica, descobrimos a variação de tempo e energia:
$$\Delta E = 100036646188 - 99981016814 = 55629374$$
Convertendo para joules:
$$\Delta E = 55629374 \times 10^-6 \approx 55,6 \text{ joules} $$
$$\Delta t = 1646988.470136542 - 1646987.469997645 \approx 1 \text{ segundo} $$

Assim, a Potência Média será de **55,6 Watts**.
# Script para Conversão de Dados e Cálculo de Potência Média
Para automatizar essa tarefa, a função abaixo recebe o arquivo com os dados brutos e calcula a potência média entre todas as medições.
```python
leitura = []
with open(args.arquivoIn, "r") as inputFile:
    linhas = inputFile.readlines()
    linhaAnterior = linhas[0].split()
    tempoMedicao = 0
    tempo = []

    for i in range(1, len(linhas)):
        linha = linhas[i].split()
        
        deltaTempo = float(linha[1]) - float(linhaAnterior[1])

        deltaWatts = (float(linha[0]) - float(linhaAnterior[0])) * (10**-6)/deltaTempo

        #populando matriz para criar graficos depois
        leitura.append([deltaWatts, deltaTempo])
        arquivoOut.write(f"{deltaWatts} {deltaTempo}\n")
        tempoMedicao += deltaTempo
        tempo.append(tempoMedicao)



        linhaAnterior = linha
``` 

 Note que o loop da iteração for funciona da seguinte forma:
```
[ Iteração 1 ]
  ↳ Linha 0 (Anterior) ┐
  ↳ Linha 1 (Atual)    ┴→ Calcula a Potência (Watts) do Seg. 1

[ Iteração 2 ]
  ↳ Linha 1 (Anterior) ┐
  ↳ Linha 2 (Atual)    ┴→ Calcula a Potência (Watts) do Seg. 2

[ Iteração 3 ] ...

```
# Gerando o Gráfico
Após a execução do trecho de código acima, a matriz leitura passa a armazenar a potência média e a variaçao de tempo entre as medições. Com ela, podemos gerar um gráfico com `matplotlib` e `numpy`. O trecho de código abaixo realiza a criação desse gráfico: 

```python
dados = np.array(leitura)

delta = dados[:, 0]

plt.figure(figsize=(10, 5))
plt.plot(tempo, delta, linestyle='-', color='blue') # Plota Potência x Segundos Reais

# colocando os rótulos
plt.title("Variação de potência média ao longo do Experimento")
plt.xlabel("Segundos")
plt.ylabel("Potência Média (Watts)")
plt.grid(True)

# Adicionando linhas verticais
plt.axvline(x=10, color='red', linestyle='--', label='Início do Estresse')
plt.axvline(x=70, color='red', linestyle='--', label='Fim do Estresse')

plt.savefig("output/grafico_energia.png", dpi=300)

arquivoIn.close()
``` 

Assim, o gráfico gerado terá a seguinte forma:
![gráfico de variação de potência média ao longo do experimento](image.png)

# Como Executar?

Ambos o trechos de código acima estão presentes no arquivo `scripts/visualizar-dados.py`. Para executá-lo, será necessário criar um ambiente virtual e instalar as bibliotecas `matplotlib` e `numpy`. Siga os passos a seguir:

1. **Abra o terminal e mova para a raiz do repositório do minicurso.**

2. **Crie um ambiente virtual e inicialize-o:**
```bash
python3 -m venv venv
source venv/bin/activate
```
3. **Instale as Bibliotecas necessárias:**
```bash
pip install matplotlib numpy
```
4. **Execute o código:** 
```bash
python3 scripts/visualizar-dados.py scripts/
```
**TODO GERAR ARQUIVO OUT AUTOMATICAMENTE**
