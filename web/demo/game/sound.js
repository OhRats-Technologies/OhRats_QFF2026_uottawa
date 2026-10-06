// Sound is opt-in and created locally after a user gesture.
export class Sound {
  enabled=false;
  enable(value) {
    this.enabled=value;
    if(value){this.context??=new AudioContext();this.context.resume();}
  }
  tone(freq,duration=.12,delay=0,type='sine',gain=.07) {
    if(!this.enabled)return;
    const ctx=this.context,o=ctx.createOscillator(),v=ctx.createGain(),t=ctx.currentTime+delay;
    o.type=type;o.frequency.setValueAtTime(freq,t);v.gain.setValueAtTime(.001,t);
    v.gain.exponentialRampToValueAtTime(gain,t+.015);
    v.gain.exponentialRampToValueAtTime(.001,t+duration);
    o.connect(v);v.connect(ctx.destination);o.start(t);o.stop(t+duration);
  }
  play(kind) {
    if(kind==='collect'){this.tone(660);this.tone(990,.16,.055);}
    if(kind==='hit')this.tone(85,.25,0,'triangle',.1);
    if(kind==='project')[220,440,660,880].forEach((f,i)=>this.tone(f,.22,i*.045));
    if(kind==='won')[523,659,784,1046].forEach((f,i)=>this.tone(f,.25,i*.12));
    if(kind==='lost'){this.tone(220,.2);this.tone(110,.35,.2);}
  }
}
