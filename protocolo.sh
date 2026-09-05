#!/bin/bash

#aborta o script no caso de erros
set +e

#lista de serviços que serão desativados
DAEMONS_RUIDOSOS="cron snapd ModemManager udisks2 upower tailscaled wpa_supplicant unattended-upgrades multipathd"

restaurar_ambiente() {
    echo "Religando placas de rede..."
    for placa in $INTERFACES_FISICAS; do
        sudo ip link set "$placa" up
        echo "    - placa de rede $placa religada."
    done

    sleep 5

    echo "Restaurando configurações..."
    sudo systemctl start snapd.socket
    sudo systemctl start multipathd.socket
    sudo systemctl start $DAEMONS_RUIDOSOS
    echo "Processos religados"
}

resfriar_componentes(){
    echo "Iniciando timer para reesfriar componentes (180s)..."
    sleep(180)
}

#chama restaurar ambiente no caso de erros e no fim da execução
trap 'restaurar_ambiente' EXIT ERR SIGINT

#desliga processos de fundo:
echo "Desligando processos de fundo..."
sudo systemctl stop snapd.socket
sudo systemctl stop multipathd.socket
sudo systemctl stop $DAEMONS_RUIDOSOS
echo "Processos de fundo desligados"

#identifica placas de rede do sistema:
INTERFACES_FISICAS=$(ls /sys/class/net/ | grep -E '^(en|wl|eth)')

#desliga placas de rede identificadas
echo "Desligando placas de rede..."
for placa in $INTERFACES_FISICAS; do
    sudo ip link set "$placa" down
    echo "    - placa de rede $placa desligada."
done

#abaixo os scripts que realizarão o protocolo de testagem:

#medicao idle
echo "Iniciando medição idle..."
MEDIA_IDLE=$(sudo venv/bin/python scripts/medicao-idle.py 30 1)
echo $MEDIA_IDLE

#medicao consumo residual
echo "Iniciando medição do consumo residual..."
MEDIA_RESIDUAL_TOTAL=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "taskset -c 0 stress-ng --cpu 1 --maximize -t 30")
CONSUMO_RESIDUAL=$(sudo venv/bin/python scripts/calculo-residual.py $MEDIA_IDLE $MEDIA_RESIDUAL_TOTAL)



#medicao sequencial aplicação 1
echo "Iniciando medição sequencial da aplicação 1..."
CONSUMO_TOTAL_P1=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "stress-ng --cpu 0 --maximize -t 30")
echo "Consumo Total P1: $CONSUMO_TOTAL_P1"
CONSUMO_ATIVO_P1=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py $CONSUMO_TOTAL_P1 $CONSUMO_RESIDUAL)
echo "Consumo Ativo P1: $CONSUMO_ATIVO_P1"

