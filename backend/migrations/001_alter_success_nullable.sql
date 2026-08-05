-- Migration 001: Rendre la colonne 'success' nullable dans 'ai_action_log'
-- Motif: Permettre la traçabilité des recommandations ignorées (dismissed) avec success = NULL (sans écriture Odoo)
-- Date: 2026-08-05

ALTER TABLE ai_action_log ALTER COLUMN success DROP NOT NULL;
