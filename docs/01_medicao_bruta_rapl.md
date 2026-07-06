# Medição de Energia via RAPL

A interface RAPL (Running Average Power Limit) é a referência para estimar o consumo de energia de processadores. A forma mais básica para acessar seus contadores de energia é por meio dos MSRs (Model Specific Registers). Trata-se de registradores de 32 ou 64 bits que são atualizados aproximadamente a cada 1 ms.

## Acesso via MSR
Abaixo, descrevemos um trecho de código que realiza o acesso direto a esses registradores via instruções RDMSR.

*TODO: CÓDIGO E DIFICULDADES*

## Acesso via Powercap
Em ambientes Linux é possível utilizar o Powercap (`sysfs powercap`). Trata-se de um framework do sistema operacional que provê uma interface de acesso no espaço de usuário via sysfs na forma de árvore de objetos de controle. 

Utilize o comando abaixo para verificar se o powercap está disponível no seu sistema:

```bash
ls /sys/class/powercap/
```
Se aparecer uma pasta chamada intel-rapl:0 ou semelhante, então está tudo 