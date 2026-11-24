-- Buzón único de contactos para los sitios del grupo.
-- Aplicar con: npx wrangler d1 execute buzon-contactos --remote --file schema.sql
CREATE TABLE IF NOT EXISTS contactos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  creado    TEXT NOT NULL,            -- fecha y hora UTC
  sitio     TEXT NOT NULL,            -- de qué página llegó (remates, estudio, inversiones)
  pagina    TEXT,
  nombre    TEXT NOT NULL,
  telefono  TEXT,
  email     TEXT,
  perfil    TEXT,
  mensaje   TEXT NOT NULL,
  ip        TEXT,
  pais      TEXT,
  estado    TEXT NOT NULL DEFAULT 'nuevo'   -- nuevo, contactado, reunión, cliente, descartado
);
CREATE INDEX IF NOT EXISTS idx_contactos_creado ON contactos (creado);
CREATE INDEX IF NOT EXISTS idx_contactos_sitio ON contactos (sitio, estado);
