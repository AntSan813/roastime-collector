document.addEventListener("DOMContentLoaded", function () {
  // Access roastData
  var data = roastData

  const timeData = roastData["Time List"]
  const beanTempData = roastData["Bean Temp"]
  const beanRorData = roastData["Bean RoR"]
  const ibtsTempData = roastData["IBTS Temp"]
  const ibtsRorData = roastData["IBTS RoR"]

  // Prepare data series for control metrics as categories
  var controlCategories = ["Power", "Fan", "Drum Speed"]
  var controlData = [data.Power, data.Fan, data.Drum]
  var controlSeries = []

  controlData.forEach(function (controlArray, controlIndex) {
    var seriesData = []
    for (var i = 0; i < controlArray.length - 1; i++) {
      var startTime = timeData[i]
      var endTime = timeData[i + 1]
      var value = controlArray[i]

      seriesData.push({
        x: startTime,
        x2: endTime,
        y: controlIndex, // Position on y-axis for the control metric
        color: getControlColor(controlCategories[controlIndex], value),
      })
    }
    controlSeries.push({
      name: controlCategories[controlIndex],
      data: seriesData,
    })
  })

  // Function to get color based on control value
  function getControlColor(metricName, value) {
    var colors = {
      Power: "rgba(255, 0, 0, " + value / 20 + ")", // Adjust max value as needed
      Fan: "rgba(0, 255, 0, " + value / 20 + ")",
      "Drum Speed": "rgba(0, 0, 255, " + value / 20 + ")",
    }
    return colors[metricName]
  }

  // Initialize the chart
  Highcharts.chart("roast-chart", {
    chart: {
      height: 600,
      marginBottom: 150,
      events: {
        fullscreenOpen: function () {
          this.update({
            title: {
              style: {
                fontSize: "30px",
              },
            },
            subtitle: {
              style: {
                color: "red",
              },
            },
          })
        },
        fullscreenClose: function () {
          this.update({
            title: {
              style: {
                fontSize: "18px",
              },
            },
          })
        },
      },
    },
    title: {
      text: "Roast Profile",
    },
    xAxis: {
      title: {
        text: "Time (s)",
      },
      type: "linear",
    },
    yAxis: [
      {
        title: {
          text: "Temperature (°C)",
        },
        height: "60%",
        lineWidth: 2,
        min: 0,
        max: 500,
      },
      {
        title: {
          text: "RoR Temperature (°C)",
        },
        opposite: true,
        min: 0,
        max: 50,
        height: "60%",
        lineWidth: 2,
      },
      {
        title: {
          text: "Control Metrics",
        },
        top: "65%",
        height: "35%",
        offset: 0,
        lineWidth: 2,
        categories: controlCategories,
        reversed: true,
      },
    ],
    tooltip: {
      shared: true,
    },
    legend: {
      align: "center",
      verticalAlign: "bottom",
      layout: "horizontal",
    },
    series: [
      {
        name: "Bean Temperature",
        data: beanTempData,
        type: "line",
        color: "#8B4513",
        yAxis: 0,
      },
      {
        name: "Drum Temperature",
        data: ibtsTempData,
        type: "line",
        color: "#FFA500",
        yAxis: 0,
      },
      {
        name: "Bean Rate of Rise",
        data: beanRorData,
        type: "line",
        color: "#0000FF",
        yAxis: 1,
        dashStyle: "ShortDash",
      },
      {
        name: "IBTS Rate of Rise",
        data: ibtsRorData,
        type: "line",
        color: "#00FF00",
        yAxis: 1,
        dashStyle: "ShortDash",
      },
    ].concat(
      controlSeries.map(function (series, index) {
        return {
          name: series.name,
          data: series.data,
          type: "xrange",
          yAxis: 2,
          dataLabels: {
            enabled: false,
          },
          showInLegend: false,
        }
      })
    ),
  })
})
