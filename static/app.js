//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");

//var refreshButton = document.getElementById("refreshButton");

window.AudioContext = window.AudioContext || window.webkitAudioContext;

var audioContext = new AudioContext();
var audioInput = null,
    realAudioInput = null,
    inputPoint = null,
    audioRecorder = null;
var rafID = null;
var analyserContext = null;
var canvasWidth, canvasHeight;
var recIndex = 0;


//add events to those 2 buttons

recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);
//refreshButton.addEventListener("click", refresh);
//Button.addEventListener("click",getInferResult);


function convertToMono( input ) {
    var splitter = audioContext.createChannelSplitter(2);
    var merger = audioContext.createChannelMerger(2);

    input.connect( splitter );
    splitter.connect( merger, 0, 0 );
    splitter.connect( merger, 0, 1 );
    return merger;
}


function updateAnalysers(time) {
    if (!analyserContext) {
        var canvas = document.getElementById("analyser");
        canvasWidth = canvas.width;
        canvasHeight = canvas.height;
        analyserContext = canvas.getContext('2d');
    }

    // analyzer draw code here
    {
        var SPACING = 3;
        var BAR_WIDTH = 1;
        var numBars = Math.round(canvasWidth / SPACING);
        var freqByteData = new Uint8Array(analyserNode.frequencyBinCount);

        analyserNode.getByteFrequencyData(freqByteData);

        analyserContext.clearRect(0, 0, canvasWidth, canvasHeight);
        analyserContext.fillStyle = '#F6D565';
        analyserContext.lineCap = 'round';
        var multiplier = analyserNode.frequencyBinCount / numBars;

        // Draw rectangle for each frequency bin.
        for (var i = 0; i < numBars; ++i) {
            var magnitude = 0;
            var offset = Math.floor( i * multiplier );
            // gotta sum/average the block, or we miss narrow-bandwidth spikes
            for (var j = 0; j< multiplier; j++)
                magnitude += freqByteData[offset + j];
            magnitude = magnitude / multiplier;
            var magnitude2 = freqByteData[i * multiplier];
            analyserContext.fillStyle = "hsl( " + Math.round((i*360)/numBars) + ", 100%, 50%)";
            analyserContext.fillRect(i * SPACING, canvasHeight, BAR_WIDTH, -magnitude);
        }
    }

    rafID = window.requestAnimationFrame( updateAnalysers );
}


function gotStream(stream) {
    inputPoint = audioContext.createGain();

    // Create an AudioNode from the stream.
    realAudioInput = audioContext.createMediaStreamSource(stream);
    console.log(inputPoint);
    console.log(stream);
    audioInput = realAudioInput;
    audioInput.connect(inputPoint);

    audioInput = convertToMono( inputPoint );

    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 2048;
    inputPoint.connect( analyserNode );

    audioRecorder = new Recorder( inputPoint );

    zeroGain = audioContext.createGain();
    zeroGain.gain.value = 0.0;
    inputPoint.connect( zeroGain );
    zeroGain.connect( audioContext.destination );
    updateAnalysers();
}



function startRecording() {
	console.log("recordButton clicked");
	recIndex++
	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    
    var constraints = { audio: true, video:false }

 	/*
    	Disable the record button until we get a success or fail from getUserMedia() 
	*/

	recordButton.disabled = true;
	stopButton.disabled = false;
	//pauseButton.disabled = false

	/*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/


	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device

		*/
		audioContext = new AudioContext();

		//update the format

		/*  assign to gumStream for later use  */
		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

        inputPoint = audioContext.createGain();

        // Create an AudioNode from the stream.
        realAudioInput = audioContext.createMediaStreamSource(stream);
        console.log(inputPoint);
        console.log(stream);
        audioInput = realAudioInput;
        audioInput.connect(inputPoint);

        audioInput = convertToMono( inputPoint );

        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 2048;
        inputPoint.connect( analyserNode );

        audioRecorder = new Recorder( inputPoint );

        zeroGain = audioContext.createGain();
        zeroGain.gain.value = 0.0;
        inputPoint.connect( zeroGain );
        zeroGain.connect( audioContext.destination );
        updateAnalysers();

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1})

		//start the recording process
		rec.record()

        //两秒钟后自动停止
        setTimeout(stopRecording,2500)

		console.log("Recording started");




	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
    	recordButton.disabled = false;
    	stopButton.disabled = true;
    	//pauseButton.disabled = true
	});
}

function pauseRecording(){
	console.log("pauseButton clicked rec.recording=",rec.recording );
	if (rec.recording){
		//pause
		rec.stop();
		pauseButton.innerHTML="Resume";
	}else{
		//resume
		rec.record()
		pauseButton.innerHTML="Pause";

	}
}

function stopRecording() {
	console.log("stopButton clicked");

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	//pauseButton.disabled = true;

	//reset button just in case the recording is stopped while paused
	//pauseButton.innerHTML="Pause";
	
	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();
	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(recognition);
}


function recognition(blob) {
	alreadyRecording = true
	var url = URL.createObjectURL(blob);
	var au = document.createElement('audio');
	var li = document.createElement('li');
	var link = document.createElement('a');
    recordButton.disabled = true
	//name of .wav file to use during upload and download (without extendion)

	var filename = 'audio.wav'

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	//save to disk link
	//link.href = url;
	//link.download = filename+".wav"; //download forces the browser to donwload the file using the  filename
	//link.innerHTML = "保存到本地";

	//add the new audio element to li
	li.appendChild(au);
	
	//add the filename to the li
	//li.appendChild(document.createTextNode(filename+".wav "))

	//add the save to disk link to li
	li.appendChild(link);
	
	//upload link
	var upload = document.createElement('recobutton');
	var result = document.getElementById('result');
	var refresh = document.createElement('refreshbutton');
	refresh.href = "#";
	refresh.innerHTML = "重置"
	//var upload = document.getElementById("button");
	upload.href="#";
	upload.innerHTML = "    识别    ";
	upload.addEventListener("click", function(event){

		  var xhr=new XMLHttpRequest();

		  //li.appendChild(result)
          xhr.onload = function(){
                if(this.readyState===4 &&this.status===200){
                    result.innerHTML = "识别结果: "+this.responseText;
               }else{
                    result.innerHTML ="";
               }
          };
		  var fd=new FormData();
		  fd.append("file",blob, filename);
		  xhr.open("POST","/save-record",true);
		  xhr.send(fd);
	});

	refresh.addEventListener("click",function(event){
	    recordButton.disabled = false
	    result.innerHTML ="识别结果: ";
        li.removeChild(upload);
	    li.removeChild(au);
	    li.removeChild(refresh);
	    //li.removeChild(document.TextNode(filename+".wav "))
	})

	//document.body.appendChild(upload)
	li.appendChild(document.createTextNode (" "))
	li.appendChild(upload)//add the upload link to li
	li.appendChild(document.createTextNode (" "))
	li.appendChild(refresh)
	//add the li element to the ol
	recordingsList.appendChild(li);
}
