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

#chame abaixo os novos scripts que realizarão o protocolo de testagem.
MEDIA_IDLE=$(sudo venv/bin/python scripts/medicao-idle.py 30 1)
MEDIA_RESIDUAL_TOTAL=$(sudo venv/bin/python scripts/medicao-consumo-residual.py 1 "taskset -c 0 stress-ng --cpu 1 --maximize -t 30")
sudo venv/bin/python scripts/calculo-residual.py $MEDIA_IDLE $MEDIA_RESIDUAL_TOTAL