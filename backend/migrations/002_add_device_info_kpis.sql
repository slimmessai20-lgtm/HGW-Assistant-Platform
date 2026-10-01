-- Migration 002 : Ajout des KPIs DeviceInfo (SerialNumber + BaseMAC)
-- DeviceInfo.SerialNumber? → serial_number
-- DeviceInfo.BaseMAC       → base_mac

ALTER TABLE gateways
  ADD COLUMN serial_number VARCHAR(64)  NULL COMMENT 'DeviceInfo.SerialNumber (ex: JD29V1W6000002)'  AFTER software_version,
  ADD COLUMN base_mac      VARCHAR(17)  NULL COMMENT 'DeviceInfo.BaseMAC (ex: 4c:22:f3:cb:57:20)'    AFTER serial_number;
