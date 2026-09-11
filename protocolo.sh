#!/bin/bash

#carrega valores
source valores.sh

#ativa venv do python
source venv/bin/activate

#aborta o script no caso de erros
set -e

#lista de serviços que serão desativados
DAEMONS_RUIDOSOS="cron snapd ModemManager udisks2 upower tailscaled wpa_supplicant unattended-upgrades multipathd prometheus docker"

restaurar_ambiente(){
    #desliga o abort automático dentro do trap para garantir a restauração completa
    set +e
    
    echo "Religando placas de rede..."
    for placa in $INTERFACES_FISICAS; do
        sudo ip link set "$placa" up
        echo "    - placa de rede $placa religada."
    done

    sleep 5

    echo "Restaurando configurações..."
    echo "0" > /sys/devices/system/cpu/intel_pstate/no_turbo
    echo on > /sys/devices/system/cpu/smt/control
    sudo systemctl start snapd.socket
    sudo systemctl start multipathd.socket
    sudo systemctl start prometheus.socket
    sudo systemctl start docker.socket
    sudo systemctl start $DAEMONS_RUIDOSOS
    sleep 5
    echo "Processos religados"
}

isolar_ambiente(){
    echo "Desativando TurboBoost..."
    echo "1" > /sys/devices/system/cpu/intel_pstate/no_turbo

    echo "Desativando Hyperthreading..."
    echo off > /sys/devices/system/cpu/smt/control

    #desliga processos de fundo:
    echo "Desligando processos de fundo..."
    sudo systemctl stop snapd.socket
    sudo systemctl stop multipathd.socket
    sudo systemctl stop prometheus.socket
    sudo systemctl stop $DAEMONS_RUIDOSOS

    #identifica placas de rede do sistema:
    INTERFACES_FISICAS=$(ls /sys/class/net/ | grep -E '^(en|wl|eth)')

    #desliga placas de rede identificadas
    echo "Desligando placas de rede..."
    for placa in $INTERFACES_FISICAS; do
        sudo ip link set "$placa" down
        echo "    - placa de rede $placa desligada."
    done
}

resfriar_componentes(){
    echo "Iniciando timer para reesfriar componentes (180s)..."
    sleep 180
}

if [ "$DO_ISOLAMENTO" == "1" ]; then
    trap 'restaurar_ambiente' EXIT ERR SIGINT
    isolar_ambiente
fi

if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
fi

if [ -z "$CONSUMO_RESIDUAL" ]; then
    #medicao consumo residual
    echo "Iniciando medição do consumo residual..."
    CONSUMO_RESIDUAL=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "taskset -c 0 stress-ng --cpu 1 -t 30")
    sudo venv/bin/python scripts/salvar-residual.py "$CONSUMO_RESIDUAL"
    echo "$CONSUMO_RESIDUAL"
fi

if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
fi

if [ -z "$BASELINE_P1" ] || [ -z "$BASELINE_P2" ]; then

    if [ -z "$CONSUMO_ATIVO_P1" ]; then
        #medicao sequencial aplicação 1
        echo "Iniciando medição sequencial da aplicação 1..."
        CONSUMO_TOTAL_P1=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "sudo stress-ng --cpu 6 -t 30")
        echo "Consumo Total P1: $CONSUMO_TOTAL_P1"
        CONSUMO_ATIVO_P1=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P1" "$CONSUMO_RESIDUAL")
        echo "Consumo Ativo P1: $CONSUMO_ATIVO_P1"
    fi

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
        resfriar_componentes
    fi

    if [ -z "$CONSUMO_ATIVO_P2" ]; then
        #medicao sequencial aplicação 2
        echo "Iniciando medição sequencial da aplicação 2..."
        CONSUMO_TOTAL_P2=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "sudo stress-ng --matrix 6 -t 30")
        echo "Consumo Total P2: $CONSUMO_TOTAL_P2"
        CONSUMO_ATIVO_P2=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P2" "$CONSUMO_RESIDUAL")
        echo "Consumo Ativo P2: $CONSUMO_ATIVO_P2"
    fi

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
        resfriar_componentes
    fi

    if [ -z "$CONSUMO_ATIVO_P1_P2" ]; then
        #medicao paralela p1 + p2
        echo "Iniciando Medição Paralela P1 + P2"
        CONSUMO_TOTAL_P1_P2=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "sudo stress-ng --cpu 3 -t 30" "sudo stress-ng --matrix 3 -t 30")
        echo "Consumo Total P1+P2: $CONSUMO_TOTAL_P1_P2"
        CONSUMO_ATIVO_P1_P2=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P1_P2" "$CONSUMO_RESIDUAL")
        echo "Consumo Ativo P1_P2: $CONSUMO_ATIVO_P1_P2"
    fi

    #calculo do baseline
    { read BASELINE_P1; read BASELINE_P2; } <<< "$(sudo venv/bin/python scripts/calculo-baseline.py "$CONSUMO_ATIVO_P1_P2" "$CONSUMO_ATIVO_P1" "$CONSUMO_ATIVO_P2")"
    echo "Baseline P1: $BASELINE_P1"
    echo "Baseline P2: $BASELINE_P2"
    
    # Conversão explícita para float na soma final para evitar erros do interpretador caso a variável venha nula
    SOMA_BASELINES=$(python3 -c "print(float('${BASELINE_P1:-0}') + float('${BASELINE_P2:-0}'))")
    echo "Soma dos baselines: $SOMA_BASELINES (esperado: $CONSUMO_ATIVO_P1_P2)"

fi