import { seasonColor, seasonLabel, type Season } from "@/lib/seasons"

export function SeasonLegend() {
  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
      {(Object.keys(seasonLabel) as Season[]).map((season) => (
        <div key={season} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="size-2 rounded-full" style={{ backgroundColor: seasonColor[season] }} aria-hidden />
          {seasonLabel[season]}
        </div>
      ))}
    </div>
  )
}
