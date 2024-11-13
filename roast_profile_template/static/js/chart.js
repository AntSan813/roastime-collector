const getControlColor = (metricName, value) => {
  var colors = {
    Fan: "rgba(70, 130, 180, 0.8)",
    Power: "rgba(255, 165, 0, 0.8)",
    "Drum Speed": "rgba(60, 179, 113, 0.8)",
  }
  return colors[metricName]
}

// Smooth RoR data using a simple moving average
const smoothData = (dataArray, windowSize) => {
  var smoothed = []
  for (var i = 0; i < dataArray.length; i++) {
    var start = Math.max(0, i - windowSize + 1)
    var sum = 0
    for (var j = start; j <= i; j++) {
      sum += dataArray[j]
    }
    smoothed.push(sum / (i - start + 1))
  }
  return smoothed
}

const chart = {
  height: 600,
  marginBottom: 150,
  marginLeft: 50,
  events: {
    fullscreenOpen: () => {
      this.update({
        title: {
          style: {
            fontSize: "30px",
          },
        },
      })
    },
    fullscreenClose: () => {
      this.update({
        title: {
          style: {
            fontSize: "18px",
          },
        },
      })
    },
  },
}

title = {
  text: null,
  style: {
    fontSize: "16px",
  },
}

const yAxis = [
  {
    title: {
      text: "Temperature (°C)",
    },
    height: "60%",
    lineWidth: 2,
    min: 0,
    max: 250,
    labels: {
      style: {
        fontSize: "10px",
      },
    },
  },
  {
    title: {
      text: "RoR (°C/min)",
    },
    opposite: true,
    min: 0,
    max: 50,
    height: "60%",
    lineWidth: 2,
    labels: {
      style: {
        fontSize: "10px",
      },
    },
  },
  {
    title: {
      text: "Control Settings",
    },
    min: 0,
    max: 10,
    opposite: true,
    top: "65%",
    height: "35%",
    offset: 0,
    lineWidth: 2,
    labels: {
      style: {
        fontSize: "10px",
      },
    },
  },
  {
    title: {
      text: null,
    },
    min: 0,
    max: 10,
    top: "65%",
    height: "35%",
    offset: 0,
    lineWidth: 2,
    labels: {
      style: {
        fontSize: "10px",
      },
    },
  },
]

const legend = {
  align: "center",
  verticalAlign: "bottom",
  layout: "horizontal",
}

const credits = {
  enabled: false,
}

const generateXAxis = data => {
  return {
    plotBands: [
      {
        from: data["roastStartIndex"] * data["sampleRate"],
        to: data["indexYellowingStart"] * data["sampleRate"],
        color: "rgba(255, 255, 204, 0.2)",
        label: {
          text: "Drying Phase",
          style: { fontSize: "10px" },
        },
      },
      {
        from: data["indexYellowingStart"] * data["sampleRate"],
        to: data["indexFirstCrackStart"] * data["sampleRate"],
        color: "rgba(255, 204, 153, 0.2)",
        label: {
          text: "Maillard Phase",
          style: { fontSize: "10px" },
        },
      },
      {
        from: data["indexFirstCrackStart"] * data["sampleRate"],
        to: data["roastEndIndex"] * data["sampleRate"],
        color: "rgba(255, 153, 153, 0.2)",
        label: {
          text: "Development Phase",
          style: { fontSize: "10px" },
        },
      },
    ],
    title: {
      text: "Time (s)",
    },
    type: "linear",
  }
}

const generateTooltip = data => {
  const getControlValueAtIndex = (ctrlType, idx) => {
    var actions = data.actions.actionTimeList.filter(
      a => a.ctrlType === ctrlType
    )
    var lastValue = actions[0] ? actions[0].value : 0
    for (var i = 0; i < actions.length; i++) {
      if (idx >= actions[i].index) {
        lastValue = actions[i].value
      } else {
        break
      }
    }
    return lastValue
  }
  return {
    shared: true,
    formatter: () => {
      var s = "<b>Time: " + this.x + " s</b>"
      this.points.forEach(point => {
        if (point.series.name.includes("Setting")) return
        s += "<br/>" + point.series.name + ": " + point.y.toFixed(2) + "°C"
      })
      // Include control settings
      var idx = Math.floor(this.x / data["sampleRate"])
      var power = getControlValueAtIndex(0, idx)
      var fan = getControlValueAtIndex(1, idx)
      var drum = getControlValueAtIndex(2, idx)
      s +=
        "<br/><b>Power:</b> " +
        power +
        ", <b>Fan:</b> " +
        fan +
        ", <b>Drum Speed:</b> " +
        drum
      return s
    },
  }
}

const generateAnnotations = data => {
  var annotationLabels = []

  const addAnnotation = (indexKey, label) => {
    if (data[indexKey]) {
      var index = data[indexKey]
      var time = index * data["sampleRate"]
      var temp = data["beanTemperature"]

      annotationLabels.push({
        point: {
          xAxis: 0,
          yAxis: 0,
          x: time,
          y: temp,
        },
        text: label,
        backgroundColor: "rgba(255,255,255,0.7)",
        borderColor: "#414141",
        borderRadius: 3,
        borderWidth: 1,
        style: {
          fontSize: "10px",
        },
      })
    }
  }

  addAnnotation("indexFirstCrackStart", "First Crack")
  addAnnotation("indexSecondCrackStart", "Second Crack")
  addAnnotation("indexYellowingStart", "Yellowing")
  addAnnotation("roastEndIndex", "Roast End")

  return [
    {
      draggable: "",
      labels: annotationLabels,
    },
  ]
}

const generateSeries = data => {
  var data = roastData
  if (!data) return null

  var roastStartIndex = data["roastStartIndex"] + 1

  const beanTempData = data["beanTemperature"]
  const beanRorData = data["beanDerivative"]
  const ibtsTempData = data["drumTemperature"]
  const ibtsRorData = data["ibtsDerivative"]

  const getControlLineData = ctrlType => {
    var actions = data.actions.actionTimeList.filter(
      a => a.ctrlType === ctrlType
    )
    var lineData = []
    var lastValue = actions[0] ? actions[0].value : 0

    for (var i = 0; i < beanTempData.length; i++) {
      var time = i * data["sampleRate"]
      if (actions[0] && i >= actions[0].index) {
        lastValue = actions.shift().value
      }
      lineData.push([time, lastValue])
    }
    return lineData
  }

  return [
    {
      name: "Bean Temperature",
      data: beanTempData.map((temp, idx) => [idx * data["sampleRate"], temp]),
      type: "line",
      color: "rgb(71,178,255)",
      yAxis: 0,
    },
    {
      name: "Drum Temperature",
      data: ibtsTempData.map((temp, idx) => [idx * data["sampleRate"], temp]),
      type: "line",
      color: "rgb(185,129,227)",
      yAxis: 0,
    },
    {
      name: "Bean Rate of Rise",
      data: smoothData(beanRorData, 5).map((ror, idx) => [
        idx * data["sampleRate"],
        ror,
      ]),
      type: "line",
      color: "rgb(80,79,195)",
      yAxis: 1,
    },
    {
      name: "IBTS Rate of Rise",
      data: smoothData(ibtsRorData, 5).map((ror, idx) => [
        idx * data["sampleRate"],
        ror,
      ]),
      type: "line",
      color: "rgb(223,213,196)",
      yAxis: 1,
    },
    {
      name: "Power Setting",
      data: getControlLineData(0),
      step: "left",
      type: "line",
      color: "rgba(255, 165, 0, 0.8)",
      yAxis: 2,
    },
    {
      name: "Fan Setting",
      data: getControlLineData(1),
      step: "left",
      type: "line",
      color: "rgba(70, 130, 180, 0.8)",
      yAxis: 2,
    },
    {
      name: "Drum Speed Setting",
      data: getControlLineData(2),
      step: "left",
      type: "line",
      color: "rgba(60, 179, 113, 0.8)",
      yAxis: 2,
    },
  ]
}

document.addEventListener("DOMContentLoaded", () => {
  var data = roastData
  if (!data) return null
  Highcharts.chart("roast-chart", {
    chart,
    title,
    xAxis: generateXAxis(data),
    yAxis,
    legend,
    credits,
    series: generateSeries(data),
    tooltip: generateTooltip(data),
    annotations: generateAnnotations(data),
  })
})
