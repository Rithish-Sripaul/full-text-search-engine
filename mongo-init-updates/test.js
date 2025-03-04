document.addEventListener('DOMContentLoaded', function () {
  // Initialize carousels
  var myCarousel = new bootstrap.Carousel(document.querySelector('#carouselExampleIndicators'), {
      interval: 10000
  });
  var imageCarousel = new bootstrap.Carousel(document.querySelector('#slideshow_carousel'), {
      interval: 10000
  });

  const options_bar = {
    axisX: {
        showGrid: false, // Hide vertical grid lines
    },
    axisY: {
        onlyInteger: true, // Show only integers on Y-axis
    },
    low: 0,
    fullWidth: true,
    chartPadding: {
        right: 30,
    },
    lineSmooth: false,
    seriesBarDistance: 10,
    plugins: [
        Chartist.plugins.tooltip()
    ]
  };

  // CSS for sharp, thick bars
  const chartStyle = `
  .ct-bar {
    stroke-width: 25px;   /* Thicker bar width */
    stroke-linecap: square; /* Sharp edges */
  }
  `;
  const styleSheet = document.createElement("style");
  styleSheet.type = "text/css";
  styleSheet.innerText = chartStyle;
  document.head.appendChild(styleSheet);

function animateChart(chart) {
  chart.on('draw', function (data) {
      // Only animate non-zero bars
      if (data.type === 'bar') {

          // Skip drawing for zero values
          if (data.value.y === 0) {
              data.element.remove();
              return; // Exit the function early
          }

          // Animate non-zero bars with bounce effect and fade-in
          data.element.attr({
              style: 'opacity: 0;'
          });
          data.element.animate({
              y2: {
                  dur: 800,  // Faster animation
                  from: data.chartRect.height(), // Start from bottom of the chart
                  to: data.y2,                   // End at calculated position
                  easing: Chartist.Svg.Easing.easeOutBounce
              },
              opacity: {
                  dur: 800,                     // Match with y2 animation duration
                  from: 0,                      // Start invisible
                  to: 1,                        // Fade in smoothly
                  easing: Chartist.Svg.Easing.easeInQuad
              }
          });

          // Ensure bar stays visible after animation
          data.element.attr({
              style: 'opacity: 1;'
          });
      }
  });
}

  // Yearly data
  const wt_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ wt_uploads_by_year| tojson}},
  ]
  };

  const cfd_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ cfd_uploads_by_year| tojson}},
  ]
  };

  const smb_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ smb_uploads_by_year| tojson}},
  ]
  }

  const hstt_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ hstt_uploads_by_year| tojson}},
  ]
  }

  const ct_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ ct_uploads_by_year| tojson}},
  ]
  }

  const lct_data_year = {
    labels: {{ choosen_years| tojson}},
  series: [
    {{ lct_uploads_by_year| tojson}},
  ]
  }

  // Initial draw for all charts
  initializeCharts();

  // Redraw charts when the slide changes
  var carouselElement = document.querySelector('#carouselExampleIndicators');
  carouselElement.addEventListener('slid.bs.carousel', function () {
      initializeCharts();
  });
};

// WT Buttons
document.querySelector("#year-wt").addEventListener("click", function () {
  document.querySelector("#month-wt").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-wt").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-wt').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-wt', wt_data_year, options_bar);
  animateChart(chart);
});

// CFD Buttons
document.querySelector("#year-cfd").addEventListener("click", function () {
  document.querySelector("#month-cfd").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-cfd").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-cfd').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-cfd', cfd_data_year, options_bar);
  animateChart(chart);
});

// SMB Buttons
document.querySelector("#year-smb").addEventListener("click", function () {
  document.querySelector("#month-smb").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-smb").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-smb').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-smb', smb_data_year, options_bar);
  animateChart(chart);
});


// HSTT Buttons
document.querySelector("#year-hstt").addEventListener("click", function () {
  document.querySelector("#month-hstt").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-hstt").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-hstt').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-hstt', hstt_data_year, options_bar);
  animateChart(chart);
});


// CT Buttons
document.querySelector("#year-ct").addEventListener("click", function () {
  document.querySelector("#month-ct").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-ct").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-ct').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-ct', ct_data_year, options_bar);
  animateChart(chart);
});


// LCT Buttons
document.querySelector("#year-lct").addEventListener("click", function () {
  document.querySelector("#month-lct").classList = "btn btn-sm btn-outline-secondary me-2";
  document.querySelector("#year-lct").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector('.ct-chart-lct').innerHTML = '';
  var chart = new Chartist.Bar('.ct-chart-lct', lct_data_year, options_bar);
  animateChart(chart);
});


// Function to reset all buttons when the carousel changes
function resetButtons() {
  document.querySelector("#month-wt").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector("#year-wt").classList = "btn btn-sm btn-outline-secondary me-2";

  document.querySelector("#month-cfd").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector("#year-cfd").classList = "btn btn-sm btn-outline-secondary me-2";

  document.querySelector("#month-smb").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector("#year-smb").classList = "btn btn-sm btn-outline-secondary me-2";

  document.querySelector("#month-hstt").classList = "btn btn-sm btn-secondary me-2";
  document.querySelector("#year-hstt").classList = "btn btn-sm btn-outline-secondary me-2";

  document.querySelector("#month-ct").classList = "btn btn-sm btn-secondary me-2 ";
  document.querySelector("#year-ct").classList = "btn btn-sm btn-outline-secondary me-2 ";

  document.querySelector("#month-lct").classList = "btn btn-sm btn-secondary me-2 ";
  document.querySelector("#year-lct").classList = "btn btn-sm btn-outline-secondary me-2 ";
}

// Reset all the buttons when the carousel changes using the above function
var carouselElement = document.querySelector('#carouselExampleIndicators');
carouselElement.addEventListener('slid.bs.carousel', function () {
  resetButtons();
});

// Redraw charts when the slide changes
var carouselElement = document.querySelector('#carouselExampleIndicators');
carouselElement.addEventListener('slid.bs.carousel', function () {
  resetButtons();
});

// Initial draw for the active slide
});
