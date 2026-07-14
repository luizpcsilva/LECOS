>**Nota sobre Sistemas Operacionais:**
> Este laboratório foi construído para a família **Ubuntu/Debian**. Os comandos abaixo utilizam o gerenciador de pacotes `apt` e nomenclaturas específicas desta distribuição. 
> Se você utiliza **Fedora**, **Arch Linux** ou outras distros, será necessário adaptar os pacotes no seu respectivo gerenciador (Ex: `dnf` ou `pacman`). O Docker, por exemplo, é frequentemente chamado apenas de `docker`, e o `venv` já costuma vir embutido no pacote `python` padrão dessas distribuições.

Para o andamento do minicurso, efetue a instalação das ferramentas e dependências abaixo:

## Instalação das Ferramentas de Sistema

Precisamos instalar a ferramenta `stress-ng` (para gerar a carga na CPU), o `docker.io` (para executar o Scaphandre de forma isolada) e as bibliotecas base do Python para criar ambientes virtuais.

Abra o terminal e execute o comando abaixo:
```bash
sudo apt update
sudo apt install stress-ng docker.io python3-venv python-is-python3
```
## Configurar Ambiente virtual Python

Para a execução dos scripts, precisamos estar em um ambiente virtual Python com as seguintes bibliotecas: `numpy`, `matplotlib`, `codecarbon`.

Siga os passos abaixo para a configuração:
1. **Abra o terminal e vá para a raiz do repositório.**

2. **Crie um ambiente virtual e inicialize-o:**
```bash
python3 -m venv venv
source venv/bin/activate
```
3. **Instale as Bibliotecas necessárias:**
```bash
pip install -r requirements.txt
```
O arquivo `requirements.txt` contém as dependências necessárias.

## Navegação
[⬅️ README Principal](../README.md) | [➡️ Passo Seguinte: Medição com Powercap](01_medicao_powercap.md)
