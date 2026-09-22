# DVA Dashboard

## Health

The *Overview* and *Gateway status* pages show the readiness of every service, and the reason when not `pass`, from the API module’s `/info/health` (fetched as `/api/info/health`).
The dashboard’s own `/livez` and `/readyz` always pass.
See [`docs/health-checks.md`](../docs/health-checks.md).

## Vue3 + Vite

This project uses Vue 3 `<script setup>` SFCs; check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.
