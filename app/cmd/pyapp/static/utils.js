function secondsToTime (s) {
  seconds = parseInt(s);
  var hours   = Math.floor(seconds / 3600);
  var minutes = Math.floor((seconds - (hours * 3600)) / 60);
  var seconds = seconds - (hours * 3600) - (minutes * 60);
  var time = "";

  if (hours != 0) {
    time = hours+":";
  }
  if (minutes != 0 || time !== "") {
    minutes = (minutes < 10 && time !== "") ? "0"+minutes : String(minutes);
    time += minutes;
  }

  if (time === "") {
    time = seconds+"s";
  }
  else {
    if ( seconds > 0 )
    {
      time += ":";
      time += (seconds < 10) ? "0"+seconds : String(seconds);
    }
    else if ( hours == 0 )
    {
      time += " mins";
    }
  }

  return time;
}

function secondsToMinutes(s) {
  seconds = parseInt(s);
  var hours   = Math.floor(seconds / 3600);
  var minutes = Math.floor((seconds - (hours * 3600)) / 60);
  var seconds = seconds - (hours * 3600) - (minutes * 60);
  var time = "";

  if (hours != 0) {
    time = hours+"h";
  }
  if (minutes != 0 || time !== "") {
    minutes = (minutes < 10 && time !== "") ? "0"+minutes : String(minutes);
    time += " " + minutes + "m";
  }

  if (time === "") {
    time = seconds+"s";
  }

  return time;
}

function setSelectedValue(selectObj, valueToSet, valueType = false) {
    for (var i = 0; i < selectObj.options.length; i++) {
      if (valueType == true) {
        if (selectObj.options[i].value == valueToSet) {
            selectObj.options[i].selected = true;
            return;
        }
      } else {
        // alert(valueToSet + " --- " + selectObj.options[i].text);
        if (selectObj.options[i].text == valueToSet) {
            selectObj.options[i].selected = true;
            return;
        }
      }
    }
}

function getSelectedValue(selectObj, valueType = false) {
  for (var i = 0; i < selectObj.options.length; i++) {
    if ( selectObj.options[i].selected == true )
    {
      if ( valueType )
      {
        return selectObj.options[i].value;
      }
      return selectObj.options[i].text
    }
  }
}

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function convertdf(data_json) {
  const jblob = JSON.parse(data_json);
  var columns = [];
  var fields = jblob['schema']['fields'];

  for ( var j = 0; j < fields.length; j++) 
  {
    if ( fields[j].name != 'index' ) { columns = columns.concat(fields[j].name); }
  }

  var data = jblob['data'];
  data.columns = columns;

  return data;
}

function convertSimpleJSON(data_json) {

  var data = new Array();

  var mapResults = new Map();
  var mapColumns = new Map();

  for ( var j = 0; j < data_json.length; j++) 
  {
    var date_f = data_json[j][0];
    var amount_f = data_json[j][1];

    if ( amount_f != 0 )
    {
      var lookup = mapResults.get(date_f);

      if ( lookup == null )
      {
        lookup = new Map();
      }

      lookup.set("total", Math.round(amount_f));
      lookup.set("group", date_f);
      mapResults.set(date_f, lookup);
      mapColumns.set("total", "");
    }
  }

  for (const [key, values] of mapResults) {
    const obj = Object.fromEntries(values);

    // Ensure a complete object..
    for (const [key, values] of mapColumns) {
      if ( obj[key] == null ) { obj[key] = 0; }
    }

    data.push(obj)
  }

  var columns = new Array();

  columns.push("group");

  for (const [key, values] of mapColumns) {
    columns.push(key)
  }

  data.columns = columns;

  return data;
}

function convertGroupJSON(data_json) {

  var data = new Array();

  var mapResults = new Map();
  var mapColumns = new Map();

  for ( var j = 0; j < data_json.length; j++) 
  {
    var group_f = data_json[j][0];
    var date_f = data_json[j][1];
    var amount_f = data_json[j][2];

    if ( amount_f != 0 )
    {
      var lookup = mapResults.get(date_f);

      if ( lookup == null )
      {
        lookup = new Map();
      }

      lookup.set(group_f, Math.abs(amount_f));
      lookup.set("group", date_f);
      mapResults.set(date_f, lookup);
      mapColumns.set(group_f, "");
    }
  }

  for (const [key, values] of mapResults) {
    const obj = Object.fromEntries(values);

    // Ensure a complete object..
    for (const [key, values] of mapColumns) {
      if ( obj[key] == null ) { obj[key] = 0; }
    }

    data.push(obj)
  }

  var columns = new Array();

  columns.push("group");

  for (const [key, values] of mapColumns) {
    columns.push(key)
  }

  data.columns = columns;

  return data;
}

function rgbToHex(r, g, b) {
  var s = "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  return s.substring(0,7);
}

var GColor = function(r,g,b) {
  r = (typeof r === 'undefined')?0:r;
  g = (typeof g === 'undefined')?0:g;
  b = (typeof b === 'undefined')?0:b;
  return {r:r, g:g, b:b};
};

function djb2(str){
  var hash = 5381;
  for (var i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i); /* hash * 33 + c */
  }
  return hash;
}

function hashStringToColor(str) {
  var hash = djb2(str);
  var r = (hash & 0xFF0000) >> 16;
  var g = (hash & 0x00FF00) >> 8;
  var b = hash & 0x0000FF;
  return "#" + ("0" + r.toString(16)).substr(-2) + ("0" + g.toString(16)).substr(-2) + ("0" + b.toString(16)).substr(-2);
}

var createColorRange = function(c1, c2, element_count) {
  var colorList = [], tmpColor;

  for (var i=0; i<element_count; i++) {
      tmpColor = new GColor();
      tmpColor.r = c1.r + ((i*(c2.r-c1.r))/element_count);
      tmpColor.g = c1.g + ((i*(c2.g-c1.g))/element_count);
      tmpColor.b = c1.b + ((i*(c2.b-c1.b))/element_count);
      //colorList.push(tmpColor);
      colorList.push(rgbToHex(tmpColor.r, tmpColor.g, tmpColor.b));
  }
  return colorList;
};

var createColorRangeSmooth = function(c1, c2, element_count) {
  var colorList = [], tmpColor;

  for (var i=0; i<element_count; i++) {
      tmpColor = new GColor();
      tmpColor.r = c1.r + ((i*(c2.r-c1.r))/element_count);
      tmpColor.g = c1.g + ((i*(c2.g-c1.g))/element_count);
      tmpColor.b = c1.b + ((i*(c2.b-c1.b))/element_count);
      //colorList.push(tmpColor);
      colorList.push(rgbToHex(tmpColor.r, tmpColor.g, tmpColor.b));
  }
  return colorList;
};

/**
 * Interpolate colors in HSL space for smoother perceptual transitions.
 * Returns an array of hex color strings.
 */
var createColorRangeSmoothHSL = function(c1, c2, element_count) {
  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s;
    const l = (max + min) / 2;
    if (max === min) {
      h = s = 0;
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = ((g - b) / d) + (g < b ? 6 : 0); break;
        case g: h = ((b - r) / d) + 2; break;
        default: h = ((r - g) / d) + 4; break;
      }
      h = h * 60;
    }
    return { h: h, s: s, l: l };
  }

  function hslToRgb(h, s, l) {
    h = ((h % 360) + 360) % 360;
    s = Math.max(0, Math.min(1, s));
    l = Math.max(0, Math.min(1, l));
    if (s === 0) {
      const v = Math.round(l * 255);
      return { r: v, g: v, b: v };
    }
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    const hk = h / 360;
    const t = (n) => {
      let tc = hk + n;
      if (tc < 0) tc += 1;
      if (tc > 1) tc -= 1;
      if (tc < 1/6) return p + (q - p) * 6 * tc;
      if (tc < 1/2) return q;
      if (tc < 2/3) return p + (q - p) * (2/3 - tc) * 6;
      return p;
    };
    return {
      r: Math.round(t(1/3) * 255),
      g: Math.round(t(0)   * 255),
      b: Math.round(t(-1/3)* 255)
    };
  }

  if (!element_count || element_count <= 0) return [];

  // convert input to rgb numbers (assume c1/c2 have r,g,b properties)
  const a = { r: Math.round(c1.r), g: Math.round(c1.g), b: Math.round(c1.b) };
  const b = { r: Math.round(c2.r), g: Math.round(c2.g), b: Math.round(c2.b) };

  const hslA = rgbToHsl(a.r, a.g, a.b);
  const hslB = rgbToHsl(b.r, b.g, b.b);

  const colors = [];
  for (let i = 0; i < element_count; i++) {
    const t = element_count === 1 ? 0 : i / (element_count - 1);

    // interpolate hue on shortest arc
    let dh = hslB.h - hslA.h;
    if (Math.abs(dh) > 180) {
      dh -= Math.sign(dh) * 360;
    }
    const h = hslA.h + dh * t;
    const s = hslA.s + (hslB.s - hslA.s) * t;
    const l = hslA.l + (hslB.l - hslA.l) * t;

    const rgb = hslToRgb(h, s, l);
    colors.push(rgbToHex(rgb.r, rgb.g, rgb.b));
  }
  return colors;
};

function timestamp(str) {
  return Number(moment(str, "YYYY-MM-DD").format("x"));
}

function toFormat(v) {
  return moment(v).format("MMM Do YY");
}

/**
* returns an array with moving average of the input array
* @param array - the input array
* @param count - the number of elements to include in the moving average calculation
* @param qualifier - an optional function that will be called on each 
*  value to determine whether it should be used
*/
function movingAvg(array, count, qualifier){

  // calculate average for subarray
  var avg = function(array, qualifier){

          var sum = 0, count = 0, val;
          for (var i in array){
              if ( isNaN(array[i]) )
              {
                  continue;
              }
              val = parseFloat(array[i]);
              if (!qualifier || qualifier(val)){
                  sum += val;
                  count++;
              }
          }

          return sum / count;
      };

  var result = [], val;

  // pad beginning of result with null values
  for (var i=0; i < count-1; i++)
      result.push(null);

  // calculate average for each subarray and add to result
  for (var i=0, len=array.length - count; i <= len; i++){

      val = avg(array.slice(i, i + count), qualifier);
      if (isNaN(val))
          result.push(null);
      else
          result.push(val.toFixed(2));
  }

  return result;
}

function roundNumber(num, scale) {
  if(!("" + num).includes("e")) {
    return +(Math.round(num + "e+" + scale)  + "e-" + scale);
  } else {
    var arr = ("" + num).split("e");
    var sig = ""
    if(+arr[1] + scale > 0) {
      sig = "+";
    }
    return +(Math.round(+arr[0] + "e" + sig + (+arr[1] + scale)) + "e-" + scale);
  }
}

// Ratios

function calcAverage(val1, val2) {
  if ( parseFloat(val2) == 0 ) {
    return ""
  }
  return roundNumber(parseFloat(val1) / parseFloat(val2), 2);
}

function createCookie(name, value, days) {

    var expires;

    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toGMTString();
    } else {
        expires = "";
    }
    document.cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value) + expires + "; path=/";
}

function readCookie(name) {
    var nameEQ = encodeURIComponent(name) + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) === ' ')
            c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0)
            return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
    return null;
}

function eraseCookie(name) {

	var found = false;

	var nameEQ = encodeURIComponent(name) + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) === ' ')
            c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0)
		{
			found = true;
			break;
		}
	}

	if ( found ) {
    	createCookie(name, "", -1);
	}
}

function hashCode(str) {
    return str.split('').reduce((prevHash, currVal) =>
      (((prevHash << 5) - prevHash) + currVal.charCodeAt(0))|0, 0);
}

function hashStringToColor2(str) {
  // persistent assignment maps to avoid returning same color for different strings
  if (!hashStringToColor2._assigned) {
    hashStringToColor2._assigned = Object.create(null);
    hashStringToColor2._used = new Set();
  }

  const assigned = hashStringToColor2._assigned;
  const used = hashStringToColor2._used;

  if (assigned[str]) return assigned[str];

  // Prefer D3 palettes when available
  const palette = (typeof d3 !== 'undefined' && (d3.schemeTableau10 || d3.schemeCategory10)) ?
    (d3.schemeTableau10 || d3.schemeCategory10) :
    null;

  const baseHash = Math.abs(hashCode(String(str)));

  if (Array.isArray(palette) && palette.length) {
    const len = palette.length;
    // start at hash-derived index, then probe for unused slot
    const start = baseHash % len;
    for (let i = 0; i < len; i++) {
      const idx = (start + i) % len;
      const c = palette[idx];
      if (!used.has(c)) {
        used.add(c);
        assigned[str] = c;
        return c;
      }
    }
    // all palette colors used -> fall back to HSL generation below
  }

  // generate deterministic HSL and probe different hues until unused
  const saturation = 60;
  const lightness = 50;
  const step = 35; // hue step to try different distinct hues
  let hue = baseHash % 360;
  for (let i = 0; i < 360 / step; i++) {
    const tryHue = (hue + i * step) % 360;
    const c = `hsl(${tryHue}, ${saturation}%, ${lightness}%)`;
    if (!used.has(c)) {
      used.add(c);
      assigned[str] = c;
      return c;
    }
  }

  // last resort: return hash-derived hex (may duplicate, but extremely unlikely here)
  const fallbackHue = hue;
  const fallback = `hsl(${fallbackHue}, ${saturation}%, ${lightness}%)`;
  used.add(fallback);
  assigned[str] = fallback;
  return fallback;
}

function hashStringToColor3(str, opts = { usePalette: true, palette: null }) {
  // deterministic hash -> hue
  const h = ((hashCode(String(str)) % 360) + 360) % 360;
  const saturation = (typeof opts.saturation === 'number') ? opts.saturation : 60; // %
  const lightness  = (typeof opts.lightness === 'number') ? opts.lightness : 50;  // %

  // Prefer using a d3 categorical palette if available and requested
  if (opts.usePalette && typeof d3 !== 'undefined') {
    const palette = opts.palette || d3.schemeTableau10 || d3.schemeCategory10;
    if (Array.isArray(palette) && palette.length) {
      return palette[Math.abs(hashCode(String(str))) % palette.length];
    }
  }

  // Return an HSL string (works in CSS and d3)
  return `hsl(${h}, ${saturation}%, ${lightness}%)`;
}