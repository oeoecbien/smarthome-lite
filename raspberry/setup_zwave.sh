#!/bin/bash
# Script d'aide pour configurer Z-Wave JS UI

echo "=========================================="
echo "Configuration Z-Wave JS UI"
echo "=========================================="
echo ""

# Vérifier que Docker est disponible
if ! command -v docker &> /dev/null; then
    echo "ERREUR: Docker n'est pas installe"
    exit 1
fi

# Déterminer la commande Docker à utiliser (avec ou sans sudo)
DOCKER_CMD="docker"
if ! docker ps &> /dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

# Vérifier que le container tourne
echo "1. Verification du container Z-Wave JS UI..."
CONTAINER_RUNNING=false

# Essayer sans sudo d'abord
if docker ps 2>/dev/null | grep -q zwave-js; then
    CONTAINER_RUNNING=true
    DOCKER_CMD="docker"
# Essayer avec sudo
elif sudo docker ps 2>/dev/null | grep -q zwave-js; then
    CONTAINER_RUNNING=true
    DOCKER_CMD="sudo docker"
fi

if [ "$CONTAINER_RUNNING" = true ]; then
    echo "   OK: Container zwave-js est en cours d'execution"
    # Afficher les informations du container
    echo "   Informations du container:"
    $DOCKER_CMD ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep zwave-js || $DOCKER_CMD ps | grep zwave-js
else
    # Vérifier aussi avec sudo si la première vérification a échoué
    if sudo docker ps 2>/dev/null | grep -q zwave-js; then
        echo "   OK: Container zwave-js est en cours d'execution (detecte avec sudo)"
        echo "   Informations du container:"
        sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep zwave-js || sudo docker ps | grep zwave-js
    else
        echo "   ATTENTION: Container zwave-js n'est pas detecte comme en cours d'execution"
        echo "   (Peut-etre un probleme de permissions - le container peut etre demarre)"
        echo ""
        echo "   Pour verifier manuellement:"
        echo "     sudo docker ps | grep zwave-js"
        echo ""
        echo "   Pour demarrer le container:"
        echo "     cd /home/admin/zwave-js"
        echo "     sudo docker compose up -d"
    fi
fi

# Vérifier les ports
echo ""
echo "2. Verification des ports..."
if netstat -tuln 2>/dev/null | grep -q ":8091"; then
    echo "   OK: Port 8091 est ouvert (interface web)"
else
    echo "   ATTENTION: Port 8091 n'est pas accessible"
fi

if netstat -tuln 2>/dev/null | grep -q ":3000"; then
    echo "   OK: Port 3000 est ouvert (WebSocket - si active)"
else
    echo "   INFO: Port 3000 n'est pas ouvert (WebSocket non active)"
fi

# Vérifier l'accessibilité de l'interface web
echo ""
echo "3. Test de l'interface web..."
if curl -s http://localhost:8091 | grep -qi "Z-Wave\|zwave"; then
    echo "   OK: Interface web accessible sur http://localhost:8091"
    echo "   URL: http://10.109.150.133:8091"
else
    echo "   ATTENTION: Interface web non accessible ou reponse inattendue"
    echo "   Test de connexion:"
    curl -s -o /dev/null -w "   Status HTTP: %{http_code}\n" http://localhost:8091
fi

# Vérifier le dongle
echo ""
echo "4. Verification du dongle Z-Wave..."
if lsusb | grep -qi "silicon\|cp210"; then
    echo "   OK: Dongle Z-Wave detecte"
    lsusb | grep -i "silicon\|cp210"
else
    echo "   ATTENTION: Dongle Z-Wave non detecte"
fi

# Vérifier les logs récents
echo ""
echo "5. Logs recents du container (dernieres 5 lignes)..."
if [ "$CONTAINER_RUNNING" = true ] || sudo docker ps 2>/dev/null | grep -q zwave-js; then
    $DOCKER_CMD logs --tail 5 zwave-js 2>/dev/null || sudo docker logs --tail 5 zwave-js 2>/dev/null || echo "   Impossible de recuperer les logs (permissions)"
fi

# Instructions
echo ""
echo "=========================================="
echo "INSTRUCTIONS"
echo "=========================================="
echo ""
echo "ETAT ACTUEL:"
echo "  - Interface web: http://10.109.150.133:8091 (accessible)"
echo "  - WebSocket: Non active (port 3000 non ouvert)"
echo ""
echo "Pour activer le WebSocket:"
echo "1. Ouvrir http://10.109.150.133:8091 dans un navigateur"
echo "2. Aller dans Settings (icone en haut a droite ou menu lateral)"
echo "3. Scroller jusqu'a la section 'Home Assistant'"
echo "4. Activer l'option 'Enable Z-Wave JS websocket server'"
echo "5. Sauvegarder les parametres (bouton en bas de la page)"
echo "6. Redemarrer le container si necessaire:"
echo "   cd /home/admin/zwave-js && sudo docker compose restart zwave-js"
echo ""
echo "Pour tester la connexion WebSocket apres activation:"
echo "  python test_zwave_connection.py"
echo ""
echo "Pour plus de details, consultez CONFIGURATION_ZWAVE.md"
echo ""
