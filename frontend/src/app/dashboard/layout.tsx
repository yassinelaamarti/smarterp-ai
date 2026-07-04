"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  Bell,
  Search,
  Database,
  Cpu,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const navigation = [
    { name: "Tableau de Bord", href: "/dashboard", icon: LayoutDashboard },
    { name: "Agent IA Chat", href: "/dashboard/chat", icon: MessageSquare, disabled: true },
    { name: "Configuration", href: "/dashboard/settings", icon: Settings, disabled: true },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r border-slate-900 bg-slate-950/80 backdrop-blur-xl">
        <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
          {/* Logo Section */}
          <div className="flex items-center flex-shrink-0 px-6 gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/20">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                SmartERP AI
              </span>
              <span className="block text-[10px] text-indigo-400 font-medium tracking-wider uppercase">
                Analytics Agent
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="mt-8 flex-1 px-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <div key={item.name}>
                  {item.disabled ? (
                    <div className="group flex items-center px-4 py-3 text-sm font-medium rounded-xl text-slate-600 cursor-not-allowed select-none">
                      <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                      <span>{item.name}</span>
                      <span className="ml-auto text-[9px] bg-slate-900 text-slate-500 px-1.5 py-0.5 rounded font-mono uppercase tracking-wider">
                        Bientôt
                      </span>
                    </div>
                  ) : (
                    <Link
                      href={item.href}
                      className={`group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                        isActive
                          ? "bg-indigo-600/10 text-indigo-400 border-l-2 border-indigo-500 shadow-sm"
                          : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                      }`}
                    >
                      <Icon
                        className={`mr-3 h-5 w-5 flex-shrink-0 transition-colors ${
                          isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-100"
                        }`}
                      />
                      {item.name}
                    </Link>
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* Status indicator bar in sidebar footer */}
        <div className="p-4 border-t border-slate-900 bg-slate-950/40">
          <div className="text-xs text-slate-500 font-semibold mb-3 px-2 uppercase tracking-wider">
            Statut Systèmes
          </div>
          <div className="space-y-2 px-2">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <Database className="h-3.5 w-3.5 text-slate-500" />
              <span>PostgreSQL Cache</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <ShieldCheck className="h-3.5 w-3.5 text-slate-500" />
              <span>Odoo API (v17)</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-indigo-500"></span>
              <Cpu className="h-3.5 w-3.5 text-slate-500" />
              <span>Groq LLM</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="md:pl-64 flex flex-col flex-1 w-0">
        {/* Header */}
        <header className="sticky top-0 z-10 flex-shrink-0 flex h-16 border-b border-slate-900 bg-slate-950/80 backdrop-blur-xl">
          <div className="flex-1 px-6 flex justify-between">
            {/* Search bar wrapper */}
            <div className="flex-1 flex">
              <form className="w-full flex md:ml-0" action="#" method="GET">
                <label htmlFor="search-field" className="sr-only">
                  Rechercher
                </label>
                <div className="relative w-full text-slate-400 focus-within:text-slate-200 flex items-center">
                  <div className="absolute inset-y-0 left-0 flex items-center pointer-events-none">
                    <Search className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <input
                    id="search-field"
                    className="block w-full h-full pl-8 pr-3 py-2 border-transparent text-slate-100 placeholder-slate-500 focus:outline-none focus:placeholder-slate-400 focus:ring-0 focus:border-transparent sm:text-sm bg-transparent"
                    placeholder="Rechercher des KPIs, ventes, commandes..."
                    type="search"
                    name="search"
                  />
                </div>
              </form>
            </div>

            {/* Notification and User actions */}
            <div className="ml-4 flex items-center md:ml-6 gap-4">
              <button
                type="button"
                className="p-1 rounded-full text-slate-400 hover:text-slate-200 focus:outline-none bg-slate-900/50 hover:bg-slate-900 transition-colors border border-slate-800"
              >
                <span className="sr-only">Notifications</span>
                <Bell className="h-4 w-4" aria-hidden="true" />
              </button>

              <div className="h-4 w-px bg-slate-900"></div>

              {/* Profile dropdown */}
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white shadow shadow-indigo-500/20">
                  YL
                </div>
                <div className="hidden lg:block text-left">
                  <span className="block text-xs font-semibold text-slate-300">
                    Yassine Laamarti
                  </span>
                  <span className="block text-[10px] text-slate-500 font-medium">
                    Administrateur
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none bg-slate-950 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
