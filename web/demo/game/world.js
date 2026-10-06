import * as T from 'three';
import {random} from './rules.js';

const glow=(color)=>new T.MeshStandardMaterial({color,emissive:color,emissiveIntensity:1.5,roughness:.35,metalness:.35});
export class World {
  constructor(canvas,reduced=false,matrix=null) {
    this.reduced=reduced;this.objects=new Map();this.bursts=[];
    this.renderer=new T.WebGLRenderer({canvas,antialias:true,alpha:false});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));
    this.renderer.outputColorSpace=T.SRGBColorSpace;this.renderer.toneMapping=T.ACESFilmicToneMapping;
    this.scene=new T.Scene();this.scene.background=new T.Color('#07161e');
    this.scene.fog=new T.FogExp2('#07161e',.019);
    this.camera=new T.PerspectiveCamera(58,1,.1,170);this.camera.position.set(0,5,17);this.camera.lookAt(0,1,-22);
    this.scene.add(new T.HemisphereLight('#b2f6e5','#12333b',2.5));
    const sun=new T.DirectionalLight('#f6cc9e',2);sun.position.set(-12,18,-5);this.scene.add(sun);
    this.point=new T.PointLight('#77ffdb',25,22);this.scene.add(this.point);
    this.forest();this.floor();this.drone();this.tracks();this.pipeline(matrix);
    this.packetGeometry=new T.IcosahedronGeometry(.55,1);this.noiseGeometry=new T.OctahedronGeometry(1.05);
    this.packetMaterial=glow('#75edc5');this.noiseMaterial=glow('#ff8256');
    this.packetRing=new T.TorusGeometry(.95,.04,6,40);this.noiseEdges=new T.EdgesGeometry(new T.BoxGeometry(2.5,2.5,2.5));
    this.edgeMaterial=new T.LineBasicMaterial({color:'#ffb379'});
    this.resize();window.addEventListener('resize',()=>this.resize());
  }
  resize(){
    this.renderer.setSize(innerWidth,innerHeight,false);this.camera.aspect=innerWidth/innerHeight;
    this.camera.fov=this.camera.aspect<1?2*Math.atan(Math.tan(58*Math.PI/360)/this.camera.aspect)*180/Math.PI:58;
    this.camera.updateProjectionMatrix();
  }
  floor() {
    const g=new T.PlaneGeometry(240,220,70,60);g.rotateX(-Math.PI/2);
    const a=g.attributes.position;
    for(let i=0;i<a.count;i++){
      const x=a.getX(i),z=a.getZ(i);
      a.setY(i,Math.abs(x)<8?-.15:Math.sin(x*.12+z*.15)*1.8+Math.cos(z*.07)*.8-.5);
    }
    g.computeVertexNormals();
    const m=new T.Mesh(g,new T.MeshStandardMaterial({color:'#123f40',roughness:1,flatShading:true}));
    m.position.z=-75;this.scene.add(m);
    const grid=new T.GridHelper(180,70,'#386d70','#1b3a47');grid.position.set(0,0,-60);this.scene.add(grid);this.grid=grid;
  }
  forest() {
    const rng=random(141),g=new T.ConeGeometry(1,4,5),mat=new T.MeshStandardMaterial({color:'#276d62',flatShading:true});
    this.trees=new T.InstancedMesh(g,mat,480);const dummy=new T.Object3D();this.treePositions=[];this.treeDummy=dummy;
    for(let i=0;i<480;i++){
      const x=(i%2?1:-1)*(9+rng()*65),z=-rng()*170,scale=.6+rng()*2.1;
      dummy.position.set(x,scale*1.6,z);dummy.scale.set(scale,scale,scale);dummy.rotation.y=rng()*Math.PI;
      dummy.updateMatrix();this.trees.setMatrixAt(i,dummy.matrix);
      this.treePositions.push({x,y:scale*1.6,z,scale,rotation:dummy.rotation.y});
      this.trees.setColorAt(i,new T.Color().setHSL(.42+rng()*.12,.3,.1+rng()*.13));
    }
    this.scene.add(this.trees);
  }
  drone() {
    this.player=new T.Group();
    const body=new T.Mesh(new T.OctahedronGeometry(.7),new T.MeshStandardMaterial({color:'#d7e9e1',metalness:.7,roughness:.2}));
    body.scale.set(1,.35,1.3);this.player.add(body);
    this.orbits=[];
    for(let i=0;i<4;i++){
      const ring=new T.Mesh(new T.TorusGeometry(.9,.025,6,64),glow('#6de0c1'));
      ring.rotation.x=Math.PI/2+i*.2;ring.rotation.y=i*Math.PI/4;this.player.add(ring);this.orbits.push(ring);
    }
    this.player.position.set(0,.9,5);this.scene.add(this.player);
    this.pulse=new T.Mesh(new T.TorusGeometry(1,.045,6,96),glow('#ceeac4'));
    this.pulse.rotation.x=Math.PI/2;this.pulse.visible=false;this.scene.add(this.pulse);
  }
  tracks() {
    this.beacons=[];
    for(const x of [-6.3,6.3])for(let z=-100;z<12;z+=8){
      const m=new T.Mesh(new T.BoxGeometry(.06,.08,2.4),glow('#336d8f'));
      m.position.set(x,.04,z);this.scene.add(m);this.beacons.push(m);
    }
    const gate=new T.Group();
    for(const x of [-7,7]){
      const p=new T.Mesh(new T.BoxGeometry(.12,7,.12),glow('#487f8d'));p.position.set(x,3,-55);gate.add(p);
    }
    const beam=new T.Mesh(new T.BoxGeometry(14,.12,.12),glow('#487f8d'));beam.position.set(0,6.5,-55);gate.add(beam);this.scene.add(gate);
  }
  pipeline(matrix) {
    // Phase hoops are illustrative; wall colours reuse one saved four-qubit matrix.
    this.phaseGate=new T.Group();
    for(let i=0;i<4;i++){
      const ring=new T.Mesh(new T.TorusGeometry(1.2,.035,8,64),glow('#7dc9da'));
      ring.position.set(-4.5+i*3,4.7,-32);ring.rotation.y=i*.4;this.phaseGate.add(ring);
    }
    this.phaseGate.visible=false;this.scene.add(this.phaseGate);
    this.matrixWalls=new T.Group();
    if(matrix)for(const side of [-1,1]){
      const tiles=new T.InstancedMesh(new T.BoxGeometry(.205,.205,.035),new T.MeshStandardMaterial({color:'#64bda4',emissive:'#2c6d67',emissiveIntensity:.6}),961);
      const d=new T.Object3D();
      matrix.forEach((row,i)=>row.forEach((v,j)=>{
        d.position.set((j-15)*.22,(15-i)*.22,0);d.updateMatrix();tiles.setMatrixAt(i*31+j,d.matrix);
        tiles.setColorAt(i*31+j,new T.Color().setHSL(.43,.3,.1+v*.65));
      }));
      tiles.position.set(side*8.5,4,-31);tiles.rotation.y=side*-.45;this.matrixWalls.add(tiles);
    }
    this.matrixWalls.visible=false;this.scene.add(this.matrixWalls);
  }
  entity(e) {
    const group=new T.Group(),packet=e.kind==='packet';
    const mesh=new T.Mesh(packet?this.packetGeometry:this.noiseGeometry,packet?this.packetMaterial:this.noiseMaterial);
    group.add(mesh);
    if(packet){const ring=new T.Mesh(this.packetRing,this.packetMaterial);ring.rotation.x=Math.PI/2;group.add(ring);}
    else group.add(new T.LineSegments(this.noiseEdges,this.edgeMaterial));
    this.scene.add(group);this.objects.set(e.id,group);return group;
  }
  burst(x,z,kind) {
    const count=this.reduced?8:24,g=new T.BufferGeometry(),positions=new Float32Array(count*3),vel=[];
    for(let i=0;i<count;i++){
      positions.set([x,.9,z],i*3);vel.push(new T.Vector3((Math.random()-.5)*9,Math.random()*6,(Math.random()-.5)*9));
    }
    g.setAttribute('position',new T.BufferAttribute(positions,3));
    const material=new T.PointsMaterial({color:kind==='hit'?'#ff976c':'#beffdf',size:.13,transparent:true});
    const mesh=new T.Points(g,material);this.scene.add(mesh);this.bursts.push({mesh,vel,life:1});
  }
  reset(){for(const o of this.objects.values())this.scene.remove(o);this.objects.clear();}
  update(run,dt,clock) {
    const moving=run?.status==='playing',time=run?.time??clock*.1;
    const speed=moving?(19+time*.07)*(run.mode==='practice'?.75:1):0;
    this.player.position.x=run?.x??Math.sin(clock*.4)*.4;
    this.player.position.y=.95+(this.reduced?0:Math.sin(clock*3)*.06);
    this.player.rotation.z=run?(run.x-run.target)*.07:0;
    this.player.visible=!run||run.invulnerable===0||Math.floor(clock*12)%2===0;
    this.point.position.copy(this.player.position);
    this.orbits.forEach((r,i)=>r.rotation.z=(this.reduced?0:clock*.7)+i*.6);
    this.phaseGate.visible=!!run&&run.stage>=1;this.matrixWalls.visible=!!run&&run.stage===2;
    this.phaseGate.children.forEach((ring,i)=>ring.rotation.z=this.reduced?i*.5:clock*.3+i*.6);
    this.camera.position.x+=(this.player.position.x*.22-this.camera.position.x)*dt*3;
    if(moving){
      this.treePositions.forEach((p,i)=>{
        p.z+=speed*dt;if(p.z>20)p.z-=180;
        const d=this.treeDummy;d.position.set(p.x,p.y,p.z);d.scale.setScalar(p.scale);d.rotation.y=p.rotation;d.updateMatrix();this.trees.setMatrixAt(i,d.matrix);
      });this.trees.instanceMatrix.needsUpdate=true;
    }
    if(moving)for(const b of this.beacons){b.position.z+=speed*dt;if(b.position.z>12)b.position.z-=112;}
    for(const e of run?.entities??[]){
      const o=this.objects.get(e.id)??this.entity(e);o.position.set(e.x,e.kind==='packet'?1.1:1.2,e.z);
      o.rotation.y=clock*(e.kind==='packet'?1:2);o.rotation.z=clock*.5;
    }
    const ids=new Set(run?.entities.map(e=>e.id)??[]);
    for(const [id,o] of this.objects)if(!ids.has(id)){this.scene.remove(o);this.objects.delete(id);}
    for(const b of this.bursts){
      b.life-=dt;const a=b.mesh.geometry.attributes.position;
      b.vel.forEach((v,i)=>{a.setXYZ(i,a.getX(i)+v.x*dt,a.getY(i)+v.y*dt,a.getZ(i)+v.z*dt);v.y-=5*dt;});
      a.needsUpdate=true;b.mesh.material.opacity=Math.max(0,b.life);
    }
    this.bursts=this.bursts.filter(b=>{if(b.life>0)return true;this.scene.remove(b.mesh);b.mesh.geometry.dispose();b.mesh.material.dispose();return false;});
    const age=run?run.time-run.pulseAt:10;
    this.pulse.visible=age<.9;this.pulse.position.set(this.player.position.x,.1,5);this.pulse.scale.setScalar(1+age*35);this.pulse.material.emissiveIntensity=3;
    this.renderer.render(this.scene,this.camera);
  }
}
