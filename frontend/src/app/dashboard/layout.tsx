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
  LogOut,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import AuthGuard from "@/components/auth/AuthGuard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  const getInitials = (name?: string | null) => {
    if (!name) return "U";
    const parts = name.split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return parts[0][0].toUpperCase();
  };

  const initials = getInitials(user?.full_name || user?.email);
  const fullName = user?.full_name || "Utilisateur";
  const userRole = user?.role === "admin" ? "Administrateur" : "Utilisateur";

  const navigation = [
    { name: "Tableau de Bord", href: "/dashboard", icon: LayoutDashboard },
    { name: "Agent IA Chat", href: "/dashboard/chat", icon: MessageSquare },
    { name: "Configuration", href: "/dashboard/settings", icon: Settings, disabled: false },
  ];


  return (
    <AuthGuard>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r border-slate-200/80 bg-white">
        <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
          {/* Logo Section */}
          <div className="flex items-center flex-shrink-0 px-6 gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/10">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-800">
                SmartERP AI
              </span>
              <span className="block text-[10px] text-blue-600 font-semibold tracking-wider uppercase">
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
                    <div className="group flex items-center px-4 py-3 text-sm font-medium rounded-xl text-slate-300 cursor-not-allowed select-none">
                      <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                      <span>{item.name}</span>
                      <span className="ml-auto text-[9px] bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded font-mono uppercase tracking-wider">
                        Bientôt
                      </span>
                    </div>
                  ) : (
                    <Link
                      href={item.href}
                      className={`group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                        isActive
                          ? "bg-blue-50 text-blue-700 border-l-2 border-blue-600 shadow-sm"
                          : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      <Icon
                        className={`mr-3 h-5 w-5 flex-shrink-0 transition-colors ${
                          isActive ? "text-blue-600" : "text-slate-400 group-hover:text-slate-700"
                        }`}
                      />
                      {item.name}
                    </Link>
                  )}
                </div>
              );
            })}
            
            {/* Bouton de déconnexion */}
            <button
              onClick={logout}
              className="w-full group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 text-slate-400 hover:bg-red-50 hover:text-red-600 mt-4 cursor-pointer text-left"
            >
              <LogOut className="mr-3 h-5 w-5 flex-shrink-0 transition-colors text-slate-400 group-hover:text-red-500" />
              Déconnexion
            </button>
          </nav>
        </div>

        {/* Status indicator bar in sidebar footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="text-xs text-slate-400 font-semibold mb-3 px-2 uppercase tracking-wider">
            Statut Systèmes
          </div>
          <div className="space-y-2 px-2">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <Database className="h-3.5 w-3.5 text-slate-400" />
              <span>PostgreSQL Cache</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <ShieldCheck className="h-3.5 w-3.5 text-slate-400" />
              <span>Odoo API (v17)</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="h-2 w-2 rounded-full bg-blue-500"></span>
              <Cpu className="h-3.5 w-3.5 text-slate-400" />
              <span>Groq LLM</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="md:pl-64 flex flex-col flex-1 w-0">
        {/* Header */}
        <header className="sticky top-0 z-10 flex-shrink-0 flex h-16 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
          <div className="flex-1 px-6 flex justify-between">
            {/* Search bar wrapper */}
            <div className="flex-1 flex">
              <form className="w-full flex md:ml-0" action="#" method="GET">
                <label htmlFor="search-field" className="sr-only">
                  Rechercher
                </label>
                <div className="relative w-full text-slate-400 focus-within:text-slate-600 flex items-center">
                  <div className="absolute inset-y-0 left-0 flex items-center pointer-events-none">
                    <Search className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <input
                    id="search-field"
                    className="block w-full h-full pl-8 pr-3 py-2 border-transparent text-slate-800 placeholder-slate-400 focus:outline-none focus:placeholder-slate-300 focus:ring-0 focus:border-transparent sm:text-sm bg-transparent"
                    placeholder="Rechercher des KPIs, ventes, commandes..."
                    type="search"
                    name="search"
                  />
                </div>
              </form>
            </div>

            {/* Notification and User actions */}
            <div className="ml-4 flex items-center md:ml-6 gap-4">
              {/* Bouton de déconnexion rapide */}
              <button
                type="button"
                onClick={logout}
                className="p-1.5 rounded-xl text-slate-500 hover:text-red-600 focus:outline-none bg-slate-50 hover:bg-slate-100 transition-colors border border-slate-200/80 cursor-pointer"
                title="Déconnexion"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
              </button>

              <div className="h-4 w-px bg-slate-200"></div>

              {/* Profile dropdown */}
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white shadow-sm shadow-blue-500/10">
                  {initials}
                </div>
                <div className="hidden lg:block text-left">
                  <span className="block text-xs font-semibold text-slate-700">
                    {fullName}
                  </span>
                  <span className="block text-[10px] text-slate-400 font-medium">
                    {userRole}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none bg-slate-50 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      </div>
    </AuthGuard>
  );
}
