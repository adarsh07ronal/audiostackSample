sox -n -r 44100 -c 1 -b 16 streams/call_16.wav  synth 6 sine 220  //low pitch

sox -n -r 44100 -c 1 -b 16 streams/nav_16.wav   synth 5 sine 1000 //high pitch 

sox -n -r 44100 -c 1 -b 16 streams/music_16.wav synth 10 sine 440 // medium pitch