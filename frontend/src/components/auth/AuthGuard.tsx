"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Loader2 } from "lucide-react";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isInitialized, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      router.push("/login");
    }
  }, [isInitialized, isAuthenticated, router]);

  // Écran de chargement haut de gamme (pendant l'initialisation)
  if (!isInitialized) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-slate-950 text-slate-100">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.08),transparent_50%)]" />
        <div className="relative flex flex-col items-center gap-4">
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 shadow-xl shadow-indigo-500/20">
            <Loader2 className="h-8 w-8 animate-spin text-white" />
          </div>
          <div className="flex flex-col items-center">
            <h2 className="text-sm font-semibold tracking-wider text-slate-300 uppercase">
              SmartERP AI
            </h2>
            <p className="text-xs text-slate-500 mt-1 animate-pulse">
              Vérification de la session...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Redirection en cours dans le useEffect
  }

  return <>{children}</>;
}
