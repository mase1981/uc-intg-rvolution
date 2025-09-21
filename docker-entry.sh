#!/bin/bash

# Docker entry script for R_volution integration
set -e

echo "Starting R_volution Integration for Unfolded Circle Remote"
echo "Config directory: $UC_CONFIG_HOME"
echo "Integration interface: $UC_INTEGRATION_INTERFACE"
echo "Integration port: $UC_INTEGRATION_HTTP_PORT"

# Start the integration
exec python3 -m uc_intg_rvolution.driver