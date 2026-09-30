Nessa pasta, iremos calcular o consumo ativo das aplicações. Decidimos considerar o consumo residual como uma faixa de valor, sendo o menor consumo residual 9,5762 (metodo rand) e o maior 11,1111(metodo prod). A faixa de valores mostrou-se necessária pois o artigo do Cadorel não especifica qual estressor utilizar para obter o consumo residual da máquina.

Sendo assim, testamos o valor do consumo residual para 11 estressores cpu-bound e percebemos que esse valor varia.

Futuramente, vale a pena considerar uma interpolação via uma função linear do consumo de energia de processos ao ampliar o consumo da cpu. A partir de 1 nucleo totalmente ativado, esse aumento se torna praticamente linear e pode ser decomposto para obter o consumo ativo teórico de 0% de uso da cpu. Esse valor pode então ser subtraido do residual total, obtendo o consumo residua; "real" da máquina.

Porém, devido ao tempo e escopo do projeto, decidimos não explorar esse caminho e utilizar uma faixa de valores.

# Passos

1. Calcular o consumo ativo minimo para medicao sequencial e paralela
2. Calcular o consumo ativo máximo para medicao sequencial e paralela
