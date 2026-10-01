-- Migration 003 : Suppression des colonnes Bridge (bridge_br0/1/2/3 — toujours NULL, inutiles)
ALTER TABLE gateways
  DROP COLUMN bridge_br0,
  DROP COLUMN bridge_br1,
  DROP COLUMN bridge_br2,
  DROP COLUMN bridge_br3;
