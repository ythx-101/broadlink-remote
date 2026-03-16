#!/bin/bash
set -e

ROUTER_IP="${BL_ROUTER_IP:-YOUR_ROUTER_IP}"
ROUTER_USER="${BL_ROUTER_USER:-root}"
SCRIPT="${BL_SCRIPT_PATH:-/opt/broadlink-ac/bl_send.py}"

case "${1:-help}" in
    on)
        ssh -o StrictHostKeyChecking=accept-new "${ROUTER_USER}@${ROUTER_IP}" "python3 $SCRIPT power_on"
        ;;
    off)
        ssh -o StrictHostKeyChecking=accept-new "${ROUTER_USER}@${ROUTER_IP}" "python3 $SCRIPT power_off"
        ;;
    *)
        echo "Usage: $0 {on|off}"
        exit 1
        ;;
esac
