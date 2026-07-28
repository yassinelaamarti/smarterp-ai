"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { api } from "@/lib/api";
import { TrendingUp, Lock, Mail, Loader2, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, login, isInitialized, initialize } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // S'assurer que le store est initialisé
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Si déjà authentifié, rediriger vers le tableau de bord
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isInitialized, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const cleanEmail = email.trim();
    const cleanPassword = password.trim();

    try {
      const response = await api.post<{ access_token: string }>("/api/auth/login", {
        email: cleanEmail,
        password: cleanPassword,
      });

      
      const { access_token } = response.data;
      await login(access_token);
      router.push("/dashboard");
    } catch (err: any) {
      console.error("Login failed:", err);
      const detail = err.response?.data?.detail || "Une erreur est survenue lors de la connexion.";
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-screen items-center justify-center bg-slate-50 px-4 py-12 text-slate-800 overflow-hidden font-sans">
      {/* Background Mesh Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.03),transparent_40%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(37,99,235,0.03),transparent_40%)]" />

      <div className="relative w-full max-w-md z-10">
        {/* Logo & Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/10 mb-3 hover:scale-105 transition-transform duration-300">
            <TrendingUp className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">
            SmartERP AI
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-semibold tracking-wide uppercase">
            Analytics & Decision Agent
          </p>
        </div>

        {/* Card */}
        <div className="bg-white border border-slate-200/85 rounded-2xl p-8 shadow-xl">
          <h2 className="text-lg font-semibold text-slate-800 mb-6 text-center">
            Connexion à votre espace
          </h2>

          {error && (
            <div className="flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6 text-sm">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Adresse E-mail
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4.5 w-4.5" />
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="ex: admin@smarterp.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:bg-white text-slate-800 transition-all duration-200"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="password" className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Mot de passe
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:bg-white text-slate-800 transition-all duration-200"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="relative w-full flex items-center justify-center py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:from-blue-700 active:to-indigo-700 text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-md shadow-blue-500/10 disabled:opacity-50 disabled:cursor-not-allowed group overflow-hidden mt-8 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Connexion en cours...
                </>
              ) : (
                "Se connecter"
              )}
            </button>
          </form>
        </div>

        {/* Demo Credentials Alert */}
        <div className="mt-6 p-4 text-center rounded-xl bg-white border border-slate-200/80 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">
            Identifiants de démo : <span className="text-blue-600 font-semibold">admin@smarterp.ai</span> / <span className="text-blue-600 font-semibold">adminpassword</span>
          </p>
        </div>
      </div>
    </div>
  );
}
