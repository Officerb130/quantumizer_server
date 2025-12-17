

function makeChart(workout, ftp_input) {

  d3.json("api/workout", {
    method:"POST",
    body: "{ \"id\": \"" + workout + "\" }",
    headers: {
      "Content-type": "application/json; charset=UTF-8",
      "Authorization" : "Bearer " + getCookie("access-token")
    }
  }).then( function(data_json) {

    var timeLabels = [];
    var powerDataFTP = [];
    var powerData = data_json['power'];
    var ftp = data_json['ftp'];
    var dt = new Date();

    for (var i = 0; i < powerData.length; i++) 
    { 
      powerDataFTP.push(ftp);
      timeLabels.push(dt);
      dt = new Date(dt.getTime() + 1000);
    }

    var minDate = timeLabels.reduce(function (a, b) { return a < b ? a : b; }); 
    var maxDate = timeLabels.reduce(function (a, b) { return a > b ? a : b; });

    var pmcChart = new Chart($("#" + workout + "-chart"), {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                data: powerData,
                label: "Power",
                borderColor: "#8e5ea2",
                backgroundColor: "#8e5ea2",
                fill: false,
                yAxisID: "y-axis-1",
                xAxisID: "x-axis-1",
                type: 'line',
                pointHitRadius: 10,
                order: 2
            },
            {
                data: powerDataFTP,
                label: "FTP",
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgb(75, 192, 192)',
                fill: false,
                yAxisID: "y-axis-1",
                xAxisID: "x-axis-1",
                type: 'line',
                borderWidth: 1,
                pointHitRadius: 0,
                pointRadius: 0,
                spanGaps: false,
                order: 1
            }
            ]
        },
        options: {
            animation: false,
            title: {
                display: false,
            },
            legend: {
                display: false,
                labels: {
                    fontColor: 'white'
                }
            },
            datasets: {
              line: {
                  pointRadius: 0 // disable for all `'line'` datasets
              }
            },
            elements: {
                point: {
                    radius: 0
                }
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                      display: true,
                      labelString: 'Power'
                    },
                    type: "linear",
                    position: "left",
                    id: "y-axis-1",
                    ticks: {
                        beginAtZero: false,
                        fontColor: 'white'
                    }
                }],
                xAxes: [{
                    id: "x-axis-1",
                    type: 'time',
                    time: {
                      tooltipFormat: 'hh:mm:ss'
                    },
                    ticks: {
                      callback: function(value, index, ticks) {
                          var x = moment(value, 'hh:mm:ss').format("HH:mm");
                          // alert(x)
                          return x.replace("12:", "00:");
                          // alert(value);
                          // return moment(value).format("HH:mm");
                          //return timestamp(value);
                          //return '$' + value;
                      },
                      maxRotation: 0,
                      // major: {
                      //   enabled: true
                      // },
                      display : false,
                        // source: 'auto',
                        min: minDate,
                        max: maxDate,
                        fontColor: 'white',
                    },
                    // time: {
                    //   unit: 'hour'
                    // },
                    // barPercentage: 0.4
                }]
            },
            tooltips: {
                enabled: true,
                mode: 'index',
                position: 'nearest',
                filter: function (tooltipItem, data) {
                    if (tooltipItem.datasetIndex == 1) {
                      return false;
                    }
                    return true;
                    // var label = data.labels[tooltipItem.index];
                    // console.log(tooltipItem, data, label);
                },
              callbacks: {
                  footer: function(tooltipItems, data) {

                    var data = data.datasets[0].data;
                    var index = tooltipItems[0].index;

                    var secondsBefore = 0, secondsAfter = 0;

                    for (var i = index-1; i > -1; i--) 
                    { 
                      if ( data[i] != data[index] )
                      {
                        break
                      }
                      secondsBefore++;
                    }

                    for (var i = index+1; i < data.length; i++) 
                    { 
                      if ( data[i] != data[index] )
                      {
                        break
                      }
                      secondsAfter++;
                    }

                    var totalSeconds = secondsAfter + secondsBefore + 1;

                    //console.log(tooltipItems[0].index);
                    //console.log(tooltipItems[0].index);
                    //console.log(data);
                    //console.log(totalSeconds);
                   // console.log(data[0].data[tooltipItems[0].index]);
                    
                    // let sum = 0;
                  
                    // tooltipItems.forEach(function(tooltipItem) {
                    //   alert(tooltipItem.parsed.y);
                    //   sum += tooltipItem.parsed.y;
                    // });
                  
                    return "Interval = " + secondsToTime(totalSeconds);
                  },
                  title: function(value) {
                            //alert(JSON.stringify(value));
                            var x = value[0]['xLabel'];
                            return x.replace("12:", "00:");
                        },
                  // label: function(value) {
                  //           alert(JSON.stringify(value));
                  //           return "Power: " + value['yLabel'];
                  //       },
                  // labelColor: function(context) {
                  //             return {
                  //                 borderColor: 'rgb(0, 0, 255)',
                  //                 backgroundColor: 'rgb(255, 222, 0)',
                  //                 borderWidth: 2,
                  //                 borderDash: [2, 2],
                  //                 borderRadius: 2,
                  //             };
                  //         },
                    // labelTextColor: function(context) {
                    //           return '#543453';
                    //       },
                }
              }
            },
            // plugins: {
            //   autocolors: true,
            //   annotation: {
            //     annotations: {
            //       line1: {
            //         type: 'line',
            //         yMin: {{ ftp }},
            //         yMax: {{ ftp }},
            //         borderColor: 'rgb(255, 99, 132)',
            //         borderWidth: 2
            //       }
            //     }
            //   }
            // }
    });
  });
}
 