
document.addEventListener("DOMContentLoaded", () => {
  function counter(id, start, end, duration) {
   let obj = document.getElementById(id),
    current = start,
    range = end - start,
    increment = end > start ? 1 : -1,
    step = Math.abs(Math.floor(duration / range)),
    timer = setInterval(() => {
     current += increment;
     obj.textContent = current;
     if (current == end) {
      clearInterval(timer);
     }
    }, step);
  }
  counter("count1", 0, jsCases, 3000);
  counter("count2", 0, jsDeaths, 3000);
  counter("count3", 0, jsRecoveries, 3000);
 });

 
var options = {
    series: [{
        name: 'Active Cases',
        data: cases
      },{
          name: 'Deaths',
          data: deaths
        },{
          name: 'Recoveries',
          data: recoveries
      }],
    chart: {
      type: 'line',
      width: '100%',
      height: 300
    },
    colors: ['#F44336', '#E91E63', 'rgb(58, 219, 53)'],
    stroke: {
        curve: 'straight'
    },
    legend:{
        labels:{
            colors: '#000'
        }
    },
    yaxis: {
        labels:{
            style:{
                colors: '#000'
            }
        }
    },
    xaxis: {
      categories: dates,
      borderColor: '#00E396',
      labels: {
        style: {
          colors: '#000',
        }
    }
  }
};
  
var chart = new ApexCharts(document.querySelector("#activityChart"), options);
  
chart.render();