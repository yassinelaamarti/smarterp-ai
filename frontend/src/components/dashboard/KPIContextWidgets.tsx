import { 
  RadialBarChart, 
  RadialBar, 
  PolarAngleAxis, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie,
  Radar,
  RadarChart,
  PolarGrid,
  PolarRadiusAxis
} from 'recharts';
import { Medal, Trophy, Award, HelpCircle } from 'lucide-react';

export function RevenueGoalWidget({ data }: { data: any }) {
  if (!data) return null;
  const chartData = [{ name: 'Revenue', value: data.percentage, fill: '#3b82f6' }];
  
  return (
    <div className="h-full flex flex-col justify-center items-center p-4">
      <div className="flex items-center justify-center gap-1.5 mb-2 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Objectif Mensuel</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Affiche la progression du chiffre d'affaires par rapport à l'objectif mensuel défini dans la configuration.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="w-full h-40 relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart 
            cx="50%" 
            cy="50%" 
            innerRadius="70%" 
            outerRadius="100%" 
            barSize={15} 
            data={chartData}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar 
              background={{ fill: '#e2e8f0' }} 
              dataKey="value" 
              cornerRadius={10} 
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-black text-slate-900">{data.percentage}%</span>
        </div>
      </div>
      <div className="text-center mt-2">
        <p className="text-xs text-slate-500 font-medium">Cible : {data.target.toLocaleString('fr-FR')} MAD</p>
      </div>
    </div>
  );
}

export function PipelineFunnelWidget({ data }: { data: any[] }) {
  if (!data) return null;
  
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-4 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Entonnoir de Vente</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Répartition de la valeur financière des opportunités à chaque étape du processus commercial.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 w-full min-h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 20, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fontSize: 11, fill: '#64748b', fontWeight: 500}} width={80} />
            <Tooltip 
              cursor={{fill: 'transparent'}}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-2 rounded-lg border border-slate-100 shadow-lg">
                      <p className="text-sm font-bold text-slate-900">
                        {Number(payload[0].value).toLocaleString('fr-FR')} MAD
                      </p>
                    </div>
                  )
                }
                return null;
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function StockAlertsWidget({ data }: { data: any[] }) {
  if (!data) return null;
  
  return (
    <div className="h-full flex flex-col p-4 overflow-hidden">
      <div className="flex items-center gap-1.5 mb-4 relative group">
        <h3 className="text-sm font-bold text-red-600 uppercase tracking-wide">Top 5 Ruptures</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-red-500 transition-colors" />
        <div className="absolute top-full mt-2 left-0 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Les 5 produits dont le stock physique est le plus proche de zéro (ou en rupture totale).
          <div className="absolute bottom-full left-4 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pr-2">
        <div className="space-y-3">
          {data.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center p-3 bg-red-50 rounded-lg border border-red-100">
              <span className="text-sm font-semibold text-slate-800 truncate pr-2">{item.name}</span>
              <span className="inline-flex items-center justify-center px-2 py-1 rounded text-xs font-bold bg-red-100 text-red-700 whitespace-nowrap">
                {item.qty} restants
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function LateOrdersWidget({ data }: { data: any[] }) {
  if (!data) return null;
  
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-4 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Gravité des retards</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Analyse de l'ancienneté des commandes non livrées : mineur (&lt;3j), critique (3-7j), ou urgent (&gt;7j).
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-3">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center gap-3">
            <div className="w-24 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {item.label}
            </div>
            <div className="flex-1 h-6 bg-slate-100 rounded-full overflow-hidden relative">
              <div 
                className={`absolute top-0 left-0 h-full ${item.color} transition-all duration-1000 ease-out`}
                style={{ width: `${Math.min(100, (item.value / Math.max(1, data.reduce((acc, curr) => acc + curr.value, 0))) * 100)}%` }}
              />
            </div>
            <div className="w-8 text-sm font-bold text-slate-700">
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function NewOrdersWidget({ data }: { data: any[] }) {
  if (!data) return null;
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-2 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Catégories</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Répartition des commandes récentes selon leurs catégories de produits principales.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 w-full min-h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={2} dataKey="value">
              {data.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function AvgOrderValueWidget({ data }: { data: any[] }) {
  if (!data) return null;
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-2 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Taille des commandes</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Distribution du volume des commandes par tranches de montant pour identifier les tendances d'achat.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 w-full min-h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip cursor={{fill: 'transparent'}} />
            <Bar dataKey="orders" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function NewLeadsWidget({ data }: { data: any[] }) {
  if (!data) return null;
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-2 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Sources d'acquisition</h3>

        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Analyse de la provenance des nouveaux prospects (UTM tracking via Odoo CRM).
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 w-full min-h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" tick={{fontSize: 10}} />
            <Radar name="Leads" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function ConversionRateWidget({ data }: { data: any }) {
  if (!data) return null;
  return (
    <div className="h-full flex flex-col p-4 justify-center">
      <div className="flex items-center justify-center gap-1.5 mb-4 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Gagné vs Perdu</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Les principales raisons enregistrées par les commerciaux lors de la clôture (succès ou échec) des opportunités.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="space-y-6">
        <div>
          <div className="flex justify-between text-xs font-bold mb-1">
            <span className="text-emerald-600">Top Gagné : {data.top_win.reason}</span>
            <span className="text-slate-600">{data.top_win.percentage}%</span>
          </div>
          <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500" style={{width: `${data.top_win.percentage}%`}} />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs font-bold mb-1">
            <span className="text-red-600">Top Perdu : {data.top_loss.reason}</span>
            <span className="text-slate-600">{data.top_loss.percentage}%</span>
          </div>
          <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-red-500" style={{width: `${data.top_loss.percentage}%`}} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function StockValueWidget({ data }: { data: any }) {
  if (!data) return null;
  const total = data.fresh + data.slow + data.dead;
  return (
    <div className="h-full flex flex-col p-4 justify-center">
      <div className="flex items-center justify-center gap-1.5 mb-4 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Âge du Stock</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Répartition du capital immobilisé selon la rotation du stock : Frais (&lt;30j), Lent (30-180j), Mort (&gt;180j).
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex h-8 w-full rounded-lg overflow-hidden shadow-sm">
        <div className="bg-emerald-500 h-full flex items-center justify-center text-[10px] text-white font-bold" style={{width: `${(data.fresh/total)*100}%`}}>
          {data.fresh > total*0.15 && 'Frais'}
        </div>
        <div className="bg-amber-400 h-full flex items-center justify-center text-[10px] text-white font-bold" style={{width: `${(data.slow/total)*100}%`}}>
          {data.slow > total*0.15 && 'Lent'}
        </div>
        <div className="bg-red-500 h-full flex items-center justify-center text-[10px] text-white font-bold" style={{width: `${(data.dead/total)*100}%`}}>
          {data.dead > total*0.15 && 'Mort'}
        </div>
      </div>
      <div className="mt-4 flex justify-between text-[11px] font-semibold text-slate-500">
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"/>Frais</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400"/>Lent</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"/>Mort</div>
      </div>
    </div>
  );
}

export function UnpaidInvoicesWidget({ data }: { data: any }) {
  if (!data || !data.aging_breakdown) return null;

  const totalAmount = data.total_amount || 1;
  const categories = [
    { label: "Pas encore échues", key: "not_due", color: "bg-blue-500", textColor: "text-blue-700" },
    { label: "0-30j de retard", key: "overdue_0_30", color: "bg-amber-400", textColor: "text-amber-800" },
    { label: "30-60j de retard", key: "overdue_30_60", color: "bg-orange-500", textColor: "text-orange-800" },
    { label: "60+j de retard", key: "overdue_60_plus", color: "bg-red-600", textColor: "text-red-800" },
  ];

  const breakdownMap = new Map<string, { amount: number; count: number }>(
    data.aging_breakdown.map((item: any) => [item.key, item])
  );


  return (
    <div className="h-full flex flex-col p-4 overflow-y-auto">
      <div className="flex items-center justify-between gap-1.5 mb-3">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide">Ventilation des impayés</h3>
        <span className="text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded-md">
          {data.total_count} factures
        </span>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-3">
        {categories.map((cat) => {
          const item = breakdownMap.get(cat.key) || { amount: 0, count: 0 };
          const pct = Math.min(100, Math.round((item.amount / totalAmount) * 100));

          return (
            <div key={cat.key} className="space-y-1">
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span className={cat.textColor}>{cat.label} ({item.count} fact.)</span>
                <span>{item.amount.toLocaleString("fr-FR")} MAD</span>
              </div>
              <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${cat.color} transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ActiveCustomersWidget({ data }: { data: any[] }) {
  if (!data) return null;
  const colors = ['text-yellow-500 bg-yellow-50 border-yellow-200', 'text-slate-400 bg-slate-50 border-slate-200', 'text-amber-600 bg-amber-50 border-amber-200'];
  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-center gap-1.5 mb-3 relative group">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Top 3 VIP</h3>
        <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-blue-500 transition-colors" />
        <div className="absolute top-full mt-2 hidden group-hover:block w-48 bg-slate-800 text-white text-xs rounded p-2 z-50 text-center shadow-lg pointer-events-none">
          Les trois clients ayant généré le plus grand volume de facturation sur la période.
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
        </div>
      </div>
      <div className="flex-1 flex flex-col gap-2">
        {data.map((item, idx) => (
          <div key={idx} className={`flex items-center gap-3 p-2 rounded-lg border ${colors[idx] || 'bg-slate-50'}`}>
            <div className="flex-shrink-0">
              {idx === 0 ? <Trophy className="w-4 h-4" /> : idx === 1 ? <Medal className="w-4 h-4" /> : <Award className="w-4 h-4" />}
            </div>
            <div className="flex-1 truncate">
              <div className="text-xs font-bold truncate text-slate-800">{item.name}</div>
            </div>
            <div className="text-xs font-bold whitespace-nowrap">
              {(item.spent / 1000).toFixed(1)}k
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

