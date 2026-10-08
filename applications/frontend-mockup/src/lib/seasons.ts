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

/** Estação do ano no hemisfério sul, a partir da data (independe do ano). */
export function getSeason(date: Date): Season {
  const monthDay = (date.getMonth() + 1) * 100 + date.getDate()

  if (monthDay >= 1221 || monthDay <= 320) return "verao"
  if (monthDay <= 620) return "outono"
  if (monthDay <= 922) return "inverno"
  return "primavera"
}
