#!/bin/bash

#carrega valores
source valores.sh

#seta frequency governor PERFORMANCE
sudo cpupower frequency-set -g performance

#ativa venv do python
source venv/bin/activate

#aborta o script no caso de erros
set -e

#lista de serviços que serão desativados
DAEMONS_RUIDOSOS="cron snapd ModemManager udisks2 upower tailscaled wpa_supplicant unattended-upgrades multipathd docker prometheus"

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
    sudo systemctl stop docker.socket
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

if [ -z "$CONSUMO_RESIDUAL" ]; then

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
    fi

    #medicao consumo residual
    echo "Iniciando medição do consumo residual..."
    CONSUMO_RESIDUAL=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "taskset -c 0 $ESTRESSOR_RESIDUAL")
    echo "$CONSUMO_RESIDUAL"
    sudo venv/bin/python scripts/salvar-residual.py "$ESTRESSOR_RESIDUAL" "$CONSUMO_RESIDUAL"
fi

# define a quantidade de núcleos com base no Isolamento
if [ "$DO_ISOLAMENTO" == "0" ]; then
    # ht ligado -> dobro de núcleos lógicos disponíveis
    CORES_SEQ=$((N_CORES * 2))
    CORES_PAR=$N_CORES
else
    #ht desligado -> apenas núcleos físicos
    CORES_SEQ=$N_CORES
    CORES_PAR=$((N_CORES / 2))
fi

#monta as strings dos estressores sequenciais
ESTRESSOR_1_SEQ="$TIPO_ESTRESSOR_1 $CORES_SEQ $METODO_ESTRESSOR_1 $T_DURACAO"
ESTRESSOR_2_SEQ="$TIPO_ESTRESSOR_2 $CORES_SEQ $METODO_ESTRESSOR_2 $T_DURACAO"

#monta as strings dos estressores paralelos
ESTRESSOR_1_PAR="$TIPO_ESTRESSOR_1 $CORES_PAR $METODO_ESTRESSOR_1 $T_DURACAO"
ESTRESSOR_2_PAR="$TIPO_ESTRESSOR_2 $CORES_PAR $METODO_ESTRESSOR_2 $T_DURACAO"

if [ -z "$CONSUMO_ATIVO_P1" ]; then

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
    fi

    echo "Iniciando medição sequencial da aplicação 1..."
    CONSUMO_TOTAL_P1=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "$ESTRESSOR_1_SEQ")
    echo "Consumo Total P1: $CONSUMO_TOTAL_P1"
    CONSUMO_ATIVO_P1=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P1" "$CONSUMO_RESIDUAL")
    echo "Consumo Ativo P1: $CONSUMO_ATIVO_P1"
fi

if [ -z "$CONSUMO_ATIVO_P2" ]; then

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
    fi

    echo "Iniciando medição sequencial da aplicação 2..."
    CONSUMO_TOTAL_P2=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "$ESTRESSOR_2_SEQ")
    echo "Consumo Total P2: $CONSUMO_TOTAL_P2"
    CONSUMO_ATIVO_P2=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P2" "$CONSUMO_RESIDUAL")
    echo "Consumo Ativo P2: $CONSUMO_ATIVO_P2"
fi

if [ -z "$CONSUMO_ATIVO_P1_P2" ]; then

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
    resfriar_componentes
    fi

    echo "Iniciando Medição Paralela P1 + P2"
    CONSUMO_TOTAL_P1_P2=$(sudo venv/bin/python scripts/medicao-estressor.py 1 "$ESTRESSOR_1_PAR" "$ESTRESSOR_2_PAR")
    echo "Consumo Total P1+P2: $CONSUMO_TOTAL_P1_P2"
    CONSUMO_ATIVO_P1_P2=$(sudo venv/bin/python scripts/calculo-consumo-ativo.py "$CONSUMO_TOTAL_P1_P2" "$CONSUMO_RESIDUAL")
    echo "Consumo Ativo P1_P2: $CONSUMO_ATIVO_P1_P2"
fi

if [ -z "$BASELINE_P1" ] || [ -z "$BASELINE_P2" ]; then

    #calculo do baseline
    { read BASELINE_P1; read BASELINE_P2; } <<< "$(sudo venv/bin/python scripts/calculo-baseline.py "$CONSUMO_ATIVO_P1_P2" "$CONSUMO_ATIVO_P1" "$CONSUMO_ATIVO_P2")"
    echo "Baseline P1: $BASELINE_P1"
    echo "Baseline P2: $BASELINE_P2"
    
    # Conversão explícita para float na soma final para evitar erros do interpretador caso a variável venha nula
    SOMA_BASELINES=$(python3 -c "print(float('${BASELINE_P1:-0}') + float('${BASELINE_P2:-0}'))")
    echo "Soma dos baselines: $SOMA_BASELINES (esperado: $CONSUMO_ATIVO_P1_P2)"
fi

#inicia medicao scaphandre:
if [ -z "$CONSUMO_SCAPHANDRE" ]; then
    #o docker foi parado por isolar_ambiente; o scaphandre roda em container.
    #o container em si e subido e derrubado por medicao-scaphandre.py
    sudo systemctl start docker.socket docker.service

    if [ "$DO_RESFRIAMENTO" == "1" ]; then
        resfriar_componentes
    fi

    echo "Iniciando estressores em paralelo..."
    echo "DEBUG: P1=[$ESTRESSOR_1_PAR] P2=[$ESTRESSOR_2_PAR]"
    { read CE_P1; read CE_P2; } <<< "$(venv/bin/python scripts/medicao-scaphandre.py 1 \
    "$ESTRESSOR_1_PAR" "$ESTRESSOR_2_PAR")"
    echo "Ce P1: $CE_P1"
    echo "Ce P2: $CE_P2"

    echo "Estressores finalizados."
fi