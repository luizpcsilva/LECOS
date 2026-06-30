#checa se o usuário é root
if ["$EUID" -ne 0]; then
    echo "Erro: Execute o script como sudo"
    exit 1

#obtem o nome da interface de rede
INTERFACE_REDE=$(ip route | grep default | awk '{print $5}' | head -n 1)

restaurar_sistema() {
    echo -e "/n Restaurando alterações do sistema..."


}