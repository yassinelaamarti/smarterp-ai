import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSegmentLabel(dimension: string, segmentRaw: string): string {
  if (!segmentRaw) return "";
  let clean = String(segmentRaw).trim();

  const prefixes = [
    "Catégorie client : Client : ", "Catégorie client : ", "Client : ",
    "Catégorie : ", "Région : ", "Commercial : ", "Étape : ", "Produit : "
  ];

  for (const prefix of prefixes) {
    if (clean.startsWith(prefix)) {
      clean = clean.slice(prefix.length).trim();
    }
  }

  if (clean.endsWith(" (US)")) {
    clean = clean.slice(0, -5).trim();
  }

  const dimClean: { [key: string]: string } = {
    region: "Région",
    product: "Produit",
    sales_rep: "Commercial",
    customer_category: "Client",
    customer: "Client",
  };

  const dimLabel = dimClean[dimension.toLowerCase()] || dimension;
  if (dimLabel && !clean.startsWith(dimLabel)) {
    return `${dimLabel} ${clean}`;
  }
  return clean;
}

export function translateOdooModel(model: string): string {
  switch (model) {
    case "sale.order":
      return "Commandes de vente (sale.order)";
    case "product.product":
      return "Catalogue des Produits (product.product)";
    case "crm.lead":
      return "Pistes & Opportunités CRM (crm.lead)";
    default:
      return model;
  }
}

export function translateOdooDomain(domain: string): string[] {
  const filters: string[] = [];
  
  if (domain.includes("'qty_available', '<', 5")) {
    filters.push("Stock disponible : Critique (quantité inférieure à 5 unités)");
  }
  if (domain.includes("'type', '=', 'product'") || domain.includes('"type", "=", "product"')) {
    filters.push("Type de produit : Articles stockables (hors services)");
  }
  if (domain.includes("'state', 'in', ['sale', 'done']") || domain.includes('"state", "in", ["sale", "done"]')) {
    filters.push("Statut de la transaction : Confirmée ou clôturée par l'administration");
  }
  if (domain.includes("date_order', '>='") || domain.includes('date_order", ">="')) {
    filters.push("Période analysée : Depuis le 1er jour du mois en cours");
  }
  if (domain.includes("commitment_date', '<'") || domain.includes('commitment_date", "<"')) {
    filters.push("Retard de livraison : Date de livraison prévue dépassée par rapport à aujourd'hui");
  }
  if (domain.includes("create_date', '>='") || domain.includes('create_date", ">="')) {
    filters.push("Date d'enregistrement : Opportunités créées ce mois-ci");
  }
  if (domain.includes("'type', '=', 'lead'") || domain.includes('"type", "=", "lead"')) {
    filters.push("Type de prospect : Simple piste commerciale non qualifiée (Lead)");
  }
  if (domain.includes("'type', '=', 'opportunity'") || domain.includes('"type", "=", "opportunity"')) {
    filters.push("Type de prospect : Opportunité qualifiée dans le pipeline de vente");
  }
  if (domain.includes("'stage_id.is_won', '=', True") || domain.includes('"stage_id.is_won", "=", True')) {
    filters.push("Statut commercial : Gagné / Contrat signé");
  }
  if (domain.includes("'stage_id.is_won', '=', False") || domain.includes('"stage_id.is_won", "=", False')) {
    filters.push("Statut commercial : En cours de négociation (ouvert)");
  }
  if (domain.includes("'active', '=', True") || domain.includes('"active", "=", True')) {
    filters.push("Fiche prospect : Active");
  }

  if (filters.length === 0) {
    if (domain.includes("Calculé")) {
      filters.push(domain);
    } else {
      filters.push("Extraction globale des données de l'exercice en cours");
    }
  }

  return filters;
}