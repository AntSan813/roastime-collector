/* =====================================================================
   ROAST RECORD — roast curve (Highcharts), themed to match the page.
   ===================================================================== */

const COLORS = {
  ink: "#241813",
  muted: "#6d5c4e",
  faint: "#9c8a78",
  line: "#ece2d0",
  axis: "#e3d6bf",
  beanTemp: "#c0492a", // ember
  drumTemp: "#8c6239", // toffee
  beanRor: "#c98a2e", // amber
  drumRor: "#b0a083", // taupe
  power: "#d6a23f", // gold
  fan: "#5b7da6", // slate
  drum: "#6f8f5e", // sage
}

const FONT_SANS = '"Hanken Grotesk", system-ui, sans-serif'
const FONT_MONO = '"IBM Plex Mono", monospace'

// Smooth RoR data using a simple trailing moving average
const smoothData = (dataArray, windowSize) => {
  const smoothed = []
  for (let i = 0; i < dataArray.length; i++) {
    const start = Math.max(0, i - windowSize + 1)
    let sum = 0
    for (let j = start; j <= i; j++) sum += dataArray[j]
    smoothed.push(sum / (i - start + 1))
  }
  return smoothed
}

const monoLabels = { style: { fontSize: "10px", fontFamily: FONT_MONO, color: COLORS.muted } }

const chart = {
  backgroundColor: "transparent",
  height: 600,
  marginBottom: 150,
  marginLeft: 56,
  marginRight: 56,
  spacingTop: 16,
  style: { fontFamily: FONT_SANS },
}

const title = { text: null }

const yAxis = [
  {
    title: { text: "Temperature (°C)", style: { color: COLORS.muted, fontFamily: FONT_MONO, fontSize: "11px" } },
    height: "60%",
    min: 0,
    max: 250,
    gridLineColor: COLORS.line,
    lineWidth: 1,
    lineColor: COLORS.axis,
    labels: monoLabels,
  },
  {
    title: { text: "RoR (°C/min)", style: { color: COLORS.muted, fontFamily: FONT_MONO, fontSize: "11px" } },
    opposite: true,
    min: 0,
    max: 50,
    height: "60%",
    gridLineWidth: 0,
    lineWidth: 1,
    lineColor: COLORS.axis,
    labels: monoLabels,
  },
  {
    title: { text: "Controls", style: { color: COLORS.muted, fontFamily: FONT_MONO, fontSize: "11px" } },
    min: 0,
    max: 10,
    opposite: true,
    top: "65%",
    height: "35%",
    offset: 0,
    gridLineColor: COLORS.line,
    lineWidth: 1,
    lineColor: COLORS.axis,
    labels: monoLabels,
  },
  {
    title: { text: null },
    min: 0,
    max: 10,
    top: "65%",
    height: "35%",
    offset: 0,
    gridLineWidth: 0,
    lineWidth: 0,
    labels: { enabled: false },
  },
]

const legend = {
  align: "center",
  verticalAlign: "bottom",
  layout: "horizontal",
  itemStyle: { fontFamily: FONT_SANS, fontWeight: "500", color: COLORS.ink, fontSize: "12px" },
  itemHoverStyle: { color: COLORS.beanTemp },
  symbolRadius: 2,
}

const credits = { enabled: false }

const exporting = {
  buttons: { contextButton: { symbolStroke: COLORS.muted, theme: { fill: "transparent" } } },
}

const generateXAxis = data => ({
  plotBands: [
    {
      from: data["roastStartIndex"] * data["sampleRate"],
      to: data["indexYellowingStart"] * data["sampleRate"],
      color: "rgba(231,204,134,.28)",
      label: { text: "Drying", style: { fontSize: "10px", fontFamily: FONT_MONO, color: COLORS.muted, letterSpacing: "1px" } },
    },
    {
      from: data["indexYellowingStart"] * data["sampleRate"],
      to: data["indexFirstCrackStart"] * data["sampleRate"],
      color: "rgba(214,162,63,.22)",
      label: { text: "Maillard", style: { fontSize: "10px", fontFamily: FONT_MONO, color: COLORS.muted, letterSpacing: "1px" } },
    },
    {
      from: data["indexFirstCrackStart"] * data["sampleRate"],
      to: data["roastEndIndex"] * data["sampleRate"],
      color: "rgba(192,73,42,.16)",
      label: { text: "Development", style: { fontSize: "10px", fontFamily: FONT_MONO, color: COLORS.muted, letterSpacing: "1px" } },
    },
  ],
  title: { text: "Time (s)", style: { color: COLORS.muted, fontFamily: FONT_MONO, fontSize: "11px" } },
  lineColor: COLORS.axis,
  tickColor: COLORS.axis,
  gridLineColor: COLORS.line,
  labels: monoLabels,
  type: "linear",
})

const generateTooltip = data => {
  const getControlValueAtIndex = (ctrlType, idx) => {
    const actions = data.actions.actionTimeList.filter(a => a.ctrlType === ctrlType)
    let lastValue = actions[0] ? actions[0].value : 0
    for (let i = 0; i < actions.length; i++) {
      if (idx >= actions[i].index) lastValue = actions[i].value
      else break
    }
    return lastValue
  }
  return {
    shared: true,
    useHTML: true,
    backgroundColor: "#3a221a",
    borderColor: COLORS.beanTemp,
    borderRadius: 8,
    style: { color: "#f3e7d4", fontFamily: FONT_SANS, fontSize: "12px" },
    // NOTE: must be a regular function — Highcharts binds `this` to the
    // tooltip context. An arrow function (the previous bug) loses `this`.
    formatter: function () {
      let s = '<b style="font-family:' + FONT_MONO + '">' + this.x + " s</b>"
      this.points.forEach(point => {
        if (point.series.name.includes("Setting")) return
        s += "<br/>" + point.series.name + ": " + point.y.toFixed(1) + " °C"
      })
      const idx = Math.floor(this.x / data["sampleRate"])
      s +=
        '<br/><span style="color:#d6a23f">Power ' + getControlValueAtIndex(0, idx) + "</span>" +
        '  <span style="color:#9bbce0">Fan ' + getControlValueAtIndex(1, idx) + "</span>" +
        '  <span style="color:#a9c79a">Drum ' + getControlValueAtIndex(2, idx) + "</span>"
      return s
    },
  }
}

const generateAnnotations = data => {
  const annotationLabels = []
  const addAnnotation = (indexKey, label) => {
    if (data[indexKey]) {
      const time = data[indexKey] * data["sampleRate"]
      annotationLabels.push({
        point: { xAxis: 0, yAxis: 0, x: time, y: data["beanTemperature"][data[indexKey]] || 0 },
        text: label,
        backgroundColor: "rgba(251,246,236,.94)",
        borderColor: COLORS.ink,
        borderRadius: 4,
        borderWidth: 1,
        style: { fontSize: "10px", fontFamily: FONT_MONO, color: COLORS.ink },
      })
    }
  }
  addAnnotation("indexYellowingStart", "Yellowing")
  addAnnotation("indexFirstCrackStart", "First Crack")
  addAnnotation("indexSecondCrackStart", "Second Crack")
  addAnnotation("roastEndIndex", "Roast End")
  return [{ draggable: "", labelOptions: { allowOverlap: false }, labels: annotationLabels }]
}

const generateSeries = data => {
  const beanTempData = data["beanTemperature"]
  const beanRorData = data["beanDerivative"]
  const ibtsTempData = data["drumTemperature"]
  const ibtsRorData = data["ibtsDerivative"]
  const t = idx => idx * data["sampleRate"]

  const getControlLineData = ctrlType => {
    const actions = data.actions.actionTimeList.filter(a => a.ctrlType === ctrlType)
    const lineData = []
    let lastValue = actions[0] ? actions[0].value : 0
    for (let i = 0; i < beanTempData.length; i++) {
      if (actions[0] && i >= actions[0].index) lastValue = actions.shift().value
      lineData.push([t(i), lastValue])
    }
    return lineData
  }

  return [
    { name: "Bean Temperature", data: beanTempData.map((v, i) => [t(i), v]), type: "line", color: COLORS.beanTemp, lineWidth: 3, yAxis: 0, marker: { enabled: false } },
    { name: "Drum Temperature", data: ibtsTempData.map((v, i) => [t(i), v]), type: "line", color: COLORS.drumTemp, lineWidth: 3, yAxis: 0, marker: { enabled: false } },
    { name: "Bean Rate of Rise", data: smoothData(beanRorData, 5).map((v, i) => [t(i), v]), type: "line", color: COLORS.beanRor, lineWidth: 1.5, dashStyle: "ShortDash", yAxis: 1, marker: { enabled: false } },
    { name: "Drum Rate of Rise", data: smoothData(ibtsRorData, 5).map((v, i) => [t(i), v]), type: "line", color: COLORS.drumRor, lineWidth: 1.5, dashStyle: "ShortDash", yAxis: 1, marker: { enabled: false } },
    { name: "Power Setting", data: getControlLineData(0), step: "left", type: "line", color: COLORS.power, lineWidth: 2, yAxis: 2, marker: { enabled: false } },
    { name: "Fan Setting", data: getControlLineData(1), step: "left", type: "line", color: COLORS.fan, lineWidth: 2, yAxis: 2, marker: { enabled: false } },
    { name: "Drum Speed Setting", data: getControlLineData(2), step: "left", type: "line", color: COLORS.drum, lineWidth: 2, yAxis: 2, marker: { enabled: false } },
  ]
}

const responsive = {
  rules: [
    {
      condition: { maxWidth: 560 },
      chartOptions: {
        chart: { height: 540, marginLeft: 40, marginRight: 12 },
        legend: { itemStyle: { fontSize: "10px" } },
      },
    },
  ],
}

document.addEventListener("DOMContentLoaded", () => {
  const data = typeof roastData !== "undefined" ? roastData : null
  if (!data) return
  Highcharts.chart("roast-chart", {
    chart,
    title,
    xAxis: generateXAxis(data),
    yAxis,
    legend,
    credits,
    exporting,
    responsive,
    plotOptions: { series: { animation: { duration: 900 }, states: { hover: { lineWidthPlus: 1 } } } },
    series: generateSeries(data),
    tooltip: generateTooltip(data),
    annotations: generateAnnotations(data),
  })
})
