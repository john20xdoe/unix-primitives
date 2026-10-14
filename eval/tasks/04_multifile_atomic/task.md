# Multi-Module Upgrade Task

Upgrade configuration schema across `services/auth` and `services/billing` to schema version 2.
Execute `./verify_services.sh` to validate the environment.
If the upgrade cannot complete cleanly across all services, restore all services to baseline state and log the transaction outcome to `tx_status.txt`.
