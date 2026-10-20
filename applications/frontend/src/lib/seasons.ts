export type Season = "verao" | "outono" | "inverno" | "primavera"

export const seasonLabel: Record<Season, string> = {
  verao: "Verão",
  outono: "Outono",
  inverno: "Inverno",
  primavera: "Primavera",
}

export const seasonColor: Record<Season, string> = {
  verao: "#f59e0b",
  outono: "#ea580c",
  inverno: "#3b82f6",
  primavera: "#22c55e",
}

export function getSeason(date: Date): Season {
  const monthDay = (date.getMonth() + 1) * 100 + date.getDate()

  if (monthDay >= 1221 || monthDay <= 320) return "verao"
  if (monthDay <= 620) return "outono"
  if (monthDay <= 922) return "inverno"
  return "primavera"
}

export interface SeasonBlock {
  season: Season
  x1: string
  x2: string
}

export function toSeasonBlocks(rows: { season: Season; label: string }[]): SeasonBlock[] {
  const blocks: SeasonBlock[] = []
  for (const row of rows) {
    const last = blocks[blocks.length - 1]
    if (last && last.season === row.season) {
      last.x2 = row.label
    } else {
      blocks.push({ season: row.season, x1: row.label, x2: row.label })
    }
  }
  return blocks
}
