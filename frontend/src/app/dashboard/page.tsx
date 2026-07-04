import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { RevenueChart } from "@/components/dashboard/RevenueChart";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          Tableau de bord
        </h1>
        <p className="mt-1 text-sm text-slate-400 font-medium">
          Indicateurs clés synchronisés en temps réel avec Odoo 17
        </p>
      </div>

      <div className="mt-6">
        <KPIGrid />
      </div>

      <div className="mt-8">
        <RevenueChart />
      </div>
    </div>
  );
}
