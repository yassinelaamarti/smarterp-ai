import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { RevenueChart } from "@/components/dashboard/RevenueChart";

export default function DashboardPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900">
        Tableau de bord
      </h1>
      <p className="mt-1 text-sm text-gray-500">
        Vue d&apos;ensemble des indicateurs clés — Odoo 17
      </p>

      <div className="mt-8">
        <KPIGrid />
      </div>

      <div className="mt-6">
        <RevenueChart />
      </div>
    </main>
  );
}
