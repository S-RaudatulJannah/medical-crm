import { Users, BedDouble, Activity, CheckCircle, AlertTriangle } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────

type Variant = 'primary' | 'blue' | 'amber' | 'green' | 'red'
type IconName = 'users' | 'bed' | 'activity' | 'check' | 'alert'

interface MetricCardProps {
  title: string
  value: number | string
  subtitle: string
  variant: Variant
  icon: IconName
  trend?: string
}

// ── Icon Map ──────────────────────────────────────────────────────

const ICON_MAP: Record<IconName, React.ElementType> = {
  users:    Users,
  bed:      BedDouble,
  activity: Activity,
  check:    CheckCircle,
  alert:    AlertTriangle,
}

// ── Variant Styles ────────────────────────────────────────────────

const VARIANT: Record<Variant, {
  border: string
  iconBg: string
  valueColor: string
  trendPill: string
  accentBar: string
}> = {
  primary: {
    border:     'border-[#62796A]/20',
    iconBg:     'bg-[#62796A]',
    valueColor: 'text-[#62796A]',
    trendPill:  'bg-[#62796A]/8 text-[#62796A] border-[#62796A]/20',
    accentBar:  'bg-[#62796A]',
  },
  blue: {
    border:     'border-blue-100',
    iconBg:     'bg-blue-600',
    valueColor: 'text-blue-700',
    trendPill:  'bg-blue-50 text-blue-600 border-blue-100',
    accentBar:  'bg-blue-600',
  },
  amber: {
    border:     'border-amber-100',
    iconBg:     'bg-amber-500',
    valueColor: 'text-amber-700',
    trendPill:  'bg-amber-50 text-amber-600 border-amber-100',
    accentBar:  'bg-amber-500',
  },
  green: {
    border:     'border-emerald-100',
    iconBg:     'bg-emerald-500',
    valueColor: 'text-emerald-700',
    trendPill:  'bg-emerald-50 text-emerald-600 border-emerald-100',
    accentBar:  'bg-emerald-500',
  },
  red: {
    border:     'border-red-100',
    iconBg:     'bg-red-500',
    valueColor: 'text-red-700',
    trendPill:  'bg-red-50 text-red-600 border-red-100',
    accentBar:  'bg-red-500',
  },
}

// ── Component ─────────────────────────────────────────────────────

export default function MetricCard({
  title,
  value,
  subtitle,
  variant,
  icon,
  trend,
}: MetricCardProps) {
  const s = VARIANT[variant]
  const Icon = ICON_MAP[icon]

  return (
    <div
      className={[
        'relative bg-white rounded-2xl overflow-hidden border shadow-card',
        'hover:shadow-card-md hover:-translate-y-0.5 transition-all duration-200',
        'animate-slide-up group',
        s.border,
      ].join(' ')}
    >
      {/* Top accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${s.accentBar} opacity-70`} />

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start justify-between mb-4">
          <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider leading-tight pr-3">
            {title}
          </p>
          <div
            className={[
              'w-9 h-9 rounded-xl flex items-center justify-center shrink-0',
              'group-hover:scale-110 transition-transform duration-200 shadow-sm',
              s.iconBg,
            ].join(' ')}
          >
            <Icon className="w-[18px] h-[18px] text-white" />
          </div>
        </div>

        {/* Value */}
        <p className={`text-[38px] font-extrabold leading-none tabular-nums ${s.valueColor} mb-1`}>
          {typeof value === 'number' ? value.toLocaleString('id-ID') : value}
        </p>
        <p className="text-[12px] text-gray-400 mb-4">{subtitle}</p>

        {/* Trend pill */}
        {trend && (
          <div
            className={[
              'inline-flex items-center text-[11px] font-medium',
              'px-2.5 py-1 rounded-full border',
              s.trendPill,
            ].join(' ')}
          >
            {trend}
          </div>
        )}
      </div>
    </div>
  )
}
