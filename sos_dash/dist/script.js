//  code to generate scolling bitmap charts
//pause;

const CORR_CVS = document.getElementById('corr_graph');
const CORR_CTX = CORR_CVS.getContext('2d');
const POS_CVS = document.getElementById('pos_overlap')
const POS_CTX = POS_CVS.getContext('2d');
const NEG_CVS = document.getElementById('neg_overlap')
const NEG_CTX = NEG_CVS.getContext('2d');

//var wsURL = "ws://localhost:8888/ws"; // URL for the websocket server
//var wsURL = "ws://10.0.0.136:8888/ws"; // URL for the websocket server
var wsURL = "ws://"+self.location.hostname+":8888/ws";

const DATA = new Float32Array(400);

function fillRandData(){
  for (let i = 0; i < DATA.length; i++) {
    DATA[i] = Math.random();
  }  
}

function paintScroll(CONTEXT, colorMap, data, vector_size) {  
  // CONTEXT is the canvas contect object, colorMap is the function mapping data value to a pixel color style
  // and data is the array of floats to paint on the chart

  let canvasHeight = CONTEXT.canvas.height;
  let canvasWidth = CONTEXT.canvas.width;
  let imgData = CONTEXT.getImageData(0, 0, canvasHeight , canvasHeight-1);
  let pixelWidth = canvasWidth / vector_size;   // fractional pixel value
  
  CONTEXT.putImageData(imgData, 0, 1); // move image down one pixel
  
  for (let i = 0; i < vector_size; i++) {  // fill a row with pixel data
    CONTEXT.strokeStyle = colorMap(data[i]);   // generate new color for each pixel based on data value
    CONTEXT.beginPath();
    CONTEXT.moveTo(canvasWidth - (i * pixelWidth),0);
    CONTEXT.lineTo(canvasWidth - ((i+1) * pixelWidth),0);
    CONTEXT.stroke();  // width defaults to 1 pixel
  }  //for
}   // function


function correlationMap(sample){
  //  generate a pixel stroke color string based on the float sample value
  // 240 deg is blue, 0 deg is res
  // map from 0.0=blue to 1.0=red
  sample = 10 * sample;    // scale factor
  let hue = Math.round(240*(1.0-sample));   // hue varies from 0 to 360 degrees on the color wheel
  let lit = Math.round(10 + sample * 70);   // range from 0 to 90% lightness
  return `hsl(${hue},100%,${lit}%)`;
}

function overlapMap(sample){
  //  generate a pixel stroke color string based on the float sample value
  // 240 deg is blue, 0 deg is res
  // map from 0.0=blue to 1.0=red
  sample = 0.3 * sample;
  let hue = Math.round(240*(1.0-sample));   // hue varies from 0 to 360 degrees on the color wheel
  let lit = Math.round(10 + sample * 70);   // range from 0 to 90% lightness
  return `hsl(${hue},100%,${lit}%)`;
}


function initWebSocket(){
  websocket = new WebSocket(wsURL);
  websocket.binaryType = "arraybuffer";  // array of float32 values

  websocket.onopen = function(evt) {
    console.log("Connected to ",wsURL);
  };
         
  websocket.onmessage = function(evt) {
    var server_message = evt.data;
    let vector_size;
    let overlap_size;
//    var pre = document.createElement("p"); 
            
    const msg_view = new DataView(server_message);
    vector_size = msg_view.getUint16(0,false);       // first 2 bytes is correlatino buffer size.  big endian size in bytes

    for (let i = 0; i < vector_size/4; i++) {
      DATA[i] = msg_view.getFloat32((i*4)+2,false);
    }
    paintScroll(CORR_CTX, correlationMap, DATA, vector_size/4);
    
    overlap_size = (server_message.byteLength - vector_size - 2)/8;  // size in samples
    
    for(let i = 0; i < overlap_size; i++) {
      DATA[i] = msg_view.getFloat32((i*4) + 2 + vector_size);
    } 
    paintScroll(POS_CTX, overlapMap, DATA, overlap_size);
    
    for(let i = 0; i < overlap_size; i++) {
      DATA[i] = msg_view.getFloat32((i*4) + 2 + vector_size + overlap_size*4);
    }
    paintScroll(NEG_CTX, overlapMap, DATA, overlap_size);
    
  }// onmessage

  websocket.onclose = function(){
    console.log("Connection Closed");
    websocket.close();
  }

}//init

// Open the MQTT feed through websockets
const client = mqtt.connect('ws://10.0.0.201:8889', {
  clientId: Math.floor(Math.random() * 100000).toString(),
  username: '',
  password: '',
  qos:'2'  // no dropping or duplicating of packets
});

client.on('connect', () => {
  console.log('MQTT connected');
  client.subscribe('/SoS/log', (err) => {
    if (err) {
      console.log('MQTT Subscription Error...');
    }
  });
});

client.on('message', (topic, message) => {
  let time_stamp = message.toString().substring(0,21);
  let velocity = message.toString().substring(28,37);
  let row_array = document.getElementById("recent_data").rows;
  for (let i = row_array.length; i > 2; i--){   // top row is header..don't change
    row_array[i-1].innerHTML = row_array[i-2].innerHTML;  // shift values one row
  }
  row_array[1].cells[0].innerHTML = time_stamp;
  row_array[1].cells[1].innerHTML = velocity;
});

client.on('close',()=>{console.log('MQTT closed')});

//pause;
window.addEventListener("load", initWebSocket, false);  //add event handler







/*
for (let i = 0; i < 100; i++){
  fillRandData();
  paintScroll(CORR_CTX, correlationMap, DATA);
  paintScroll(POS_CTX, overlapMap, DATA);
  paintScroll(NEG_CTX, overlapMap, DATA);
}
*/