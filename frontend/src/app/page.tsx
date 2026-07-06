"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import {
  TrendingUp,
  LayoutDashboard,
  MessageSquare,
  Bell,
  ShieldCheck,
  ArrowRight,
  Database,
  Sparkles,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isInitialized, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isInitialized, isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* ================= NAV ================= */}
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-slate-50/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/10">
              <TrendingUp className="h-4.5 w-4.5" />
            </div>
            <span className="text-base font-bold text-slate-800">SmartERP AI</span>
          </div>

          <Link
            href="/login"
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            Se connecter
          </Link>
        </div>
      </header>

      {/* ================= HERO ================= */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.06),transparent_45%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(79,70,229,0.05),transparent_45%)]" />

        <div className="relative mx-auto grid max-w-6xl gap-14 px-6 py-20 md:grid-cols-2 md:items-center md:py-28">
          {/* Texte */}
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
              <Sparkles className="h-3.5 w-3.5" />
              Conçu pour les PME marocaines sous Odoo
            </span>

            <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-slate-900 md:text-5xl">
              Vos données Odoo,{" "}
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                enfin exploitées
              </span>
            </h1>

            <p className="mt-5 max-w-md text-base leading-relaxed text-slate-500">
              SmartERP AI se connecte à votre Odoo en lecture seule et transforme vos
              ventes, votre CRM et votre stock en un tableau de bord clair — avec un
              agent IA qui explique pourquoi vos chiffres évoluent, pas seulement ce
              qu&apos;ils valent.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="/login"
                className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-blue-500/10 transition-all hover:from-blue-500 hover:to-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                Se connecter
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
              <a
                href="#fonctionnalites"
                className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                Voir les fonctionnalités
              </a>
            </div>
          </div>

          {/* Aperçu produit stylisé (signature) */}
          <div className="relative">
            <div className="rounded-2xl border border-slate-200/85 bg-white p-5 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Tableau de bord
                </span>
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-600">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Synchronisé
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <p className="text-[11px] font-medium text-slate-400">CA (mois)</p>
                  <p className="mt-1 text-lg font-bold text-slate-800">284 500 <span className="text-xs font-medium text-slate-400">MAD</span></p>
                  <p className="mt-1 text-[11px] font-semibold text-emerald-600">↑ 12.4%</p>
                </div>
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <p className="text-[11px] font-medium text-slate-400">Alertes stock</p>
                  <p className="mt-1 text-lg font-bold text-slate-800">3</p>
                  <p className="mt-1 text-[11px] font-semibold text-amber-600">À surveiller</p>
                </div>
              </div>

              {/* Mini sparkline décoratif */}
              <div className="mt-3 flex h-12 items-end gap-1 rounded-xl border border-slate-100 bg-slate-50 p-3">
                {[40, 55, 45, 65, 60, 78, 70, 85].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-sm bg-gradient-to-t from-blue-500 to-indigo-400 opacity-80"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>

              {/* Aperçu chat IA */}
              <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-start gap-2">
                  <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white">
                    <MessageSquare className="h-3 w-3" />
                  </div>
                  <p className="text-[11px] leading-relaxed text-slate-500">
                    « Le CA a progressé de 12% grâce aux ventes du segment Nord —
                    voulez-vous que je détaille par produit ? »
                  </p>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-4 -right-4 -z-10 h-40 w-40 rounded-full bg-gradient-to-tr from-blue-400/20 to-indigo-400/20 blur-2xl" />
          </div>
        </div>
      </section>

      {/* ================= STAT PROBLEME ================= */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center">
          <p className="text-5xl font-bold tracking-tight text-slate-900 md:text-6xl">
            85<span className="text-blue-600">%</span>
          </p>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-500">
            des PME marocaines utilisant Odoo n&apos;ont aujourd&apos;hui aucun outil d&apos;analyse
            IA pour exploiter leurs données de vente, de CRM ou de stock. SmartERP AI
            comble ce manque, sans concurrent local direct.
          </p>
        </div>
      </section>

      {/* ================= FONCTIONNALITES ================= */}
      <section id="fonctionnalites" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 max-w-lg">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
            Ce que SmartERP AI ajoute à votre Odoo
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Quatre briques, connectées à vos données réelles.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {[
            {
              icon: LayoutDashboard,
              title: "Dashboard temps réel",
              desc: "10 KPIs clés — ventes, CRM, stock — synchronisés automatiquement depuis Odoo, sans rafraîchissement manuel.",
            },
            {
              icon: MessageSquare,
              title: "Agent IA conversationnel",
              desc: "Posez vos questions en français, obtenez une explication, pas juste un chiffre — et une recommandation concrète.",
            },
            {
              icon: Bell,
              title: "Alertes automatiques",
              desc: "Stock bas, commandes en retard, chute d'activité : SmartERP AI vous prévient avant que ça devienne un problème.",
            },
            {
              icon: ShieldCheck,
              title: "Odoo non modifié",
              desc: "Connexion en lecture seule à votre installation existante — aucune donnée écrite, aucun risque pour votre ERP.",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-sm">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-slate-800">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= COMMENT CA MARCHE ================= */}
      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="mb-12 text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
            Trois étapes, aucune installation côté Odoo
          </h2>

          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                n: "01",
                icon: Database,
                title: "Connectez Odoo",
                desc: "Renseignez les identifiants API de votre instance Odoo 17 — en lecture seule, rien n'est modifié.",
              },
              {
                n: "02",
                icon: Sparkles,
                title: "L'agent analyse",
                desc: "Les KPIs sont calculés et mis en cache automatiquement, toutes les 15 minutes.",
              },
              {
                n: "03",
                icon: TrendingUp,
                title: "Décidez plus vite",
                desc: "Consultez le dashboard ou posez directement votre question à l'agent IA.",
              },
            ].map((s) => (
              <div key={s.n} className="relative pl-2">
                <span className="text-xs font-bold tracking-widest text-blue-600">{s.n}</span>
                <div className="mt-3 flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-600">
                  <s.icon className="h-4 w-4" />
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-800">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= CTA FINAL ================= */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="rounded-3xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-14 text-center shadow-xl shadow-blue-500/10">
          <h2 className="text-2xl font-bold text-white md:text-3xl">
            Prêt à voir vos données autrement ?
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-blue-100">
            Connectez-vous à votre espace SmartERP AI.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-blue-700 shadow-md transition-colors hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            Se connecter
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-slate-200">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-6 py-8 text-center">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white">
              <TrendingUp className="h-3 w-3" />
            </div>
            <span className="text-xs font-semibold text-slate-600">SmartERP AI</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Projet académique — PFA MGSI S8, en partenariat avec UrikaCloud.
          </p>
        </div>
      </footer>
    </div>
  );
}
