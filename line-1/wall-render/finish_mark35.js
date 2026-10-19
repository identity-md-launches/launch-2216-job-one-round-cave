'use strict';
// One-shot generated-pigment transfer. No network, accounts or environment access.
const fs=require('node:fs'),crypto=require('node:crypto');
const {decodePNG,encodePNG,preview}=require('./finish_wall.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const source='artifacts/line-1/wall-v16.png',destination='artifacts/line-1/wall-v17.png';
if(fs.existsSync('dist/line-1/35.json')) throw Error('already finished; refusing to repaint');
const raw=fs.readFileSync(source),ancestor=decodePNG(source),donorRaw=fs.readFileSync(destination),donor=decodePNG(destination);
if(JSON.parse(fs.readFileSync('dist/line-1/34.json')).image!=='https://api.imd.fun/artifacts/'+hash(raw)) throw Error('ancestor pin mismatch');
if(!raw.equals(fs.readFileSync('artifacts/line-1/wall.png'))) throw Error('current wall differs from ancestor');
if(ancestor.width!==1254||ancestor.height!==1254||ancestor.channels!==3||donor.width!==1254||donor.height!==1254) throw Error('unexpected dimensions');
const out={...ancestor,pixels:Buffer.from(ancestor.pixels)};
const bounds=[525,525,645,610],crop=[200,310,1050,900],scale=.14;
for(let y=0;y<Math.ceil((crop[3]-crop[1])*scale);y++) for(let x=0;x<Math.ceil((crop[2]-crop[0])*scale);x++) {
 const sx=Math.floor(crop[0]+x/scale),sy=Math.floor(crop[1]+y/scale),at=(sy*donor.width+sx)*donor.channels;
 const r=donor.pixels[at],g=donor.pixels[at+1],b=donor.pixels[at+2];
 if(r<90||r<g||g<b) continue;
 let color;
 if(g>100&&r-g<65&&b>65) color=[208,187,149];
 else if(r>g*1.25) color=[157,65,31];
 else continue;
 const alpha=.48+.28*r/255,px=bounds[0]+x,py=bounds[1]+y;
 if(px>=bounds[2]||py>=bounds[3]) throw Error('outside patch');
 const dest=(py*out.width+px)*3;
 for(let c=0;c<3;c++) out.pixels[dest+c]=Math.round(out.pixels[dest+c]*(1-alpha)+color[c]*alpha);
}
let changed=0;
for(let y=0;y<out.height;y++) for(let x=0;x<out.width;x++) {
 const i=(y*out.width+x)*3;
 if(!out.pixels.subarray(i,i+3).equals(ancestor.pixels.subarray(i,i+3))) {
  changed++;
  if(x<bounds[0]||x>=bounds[2]||y<bounds[1]||y>=bounds[3]) throw Error('ancestor changed outside patch');
 }
}
if(changed<500) throw Error('mark missing');
const png=encodePNG(out),jpg=preview(out),digest=hash(png);
if(jpg.length>100000) throw Error('preview exceeds 100 KB');
const record={name:'The Bounded Pebble',image:'https://api.imd.fun/artifacts/'+digest,attributes:[
 {trait_type:'Cave',value:'Roots'},{trait_type:'Wall',value:'Line 1'},{trait_type:'Number',value:35},
 {trait_type:'Left behind',value:'Paired Bounds'},
 {trait_type:'Meaning',value:'A pebble between chalk curves holds room for what a measurement cannot yet tell.'},
 {trait_type:'One thing',value:'Reproducible benchmark evidence'}]};
fs.writeFileSync(destination,png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/35.jpg',jpg);
fs.writeFileSync('dist/line-1/35.json',JSON.stringify(record,null,2)+'\n');
const review={wall:destination,width:out.width,height:out.height,format:'PNG RGB8',bytes:png.length,sha256:digest,
 preview:{path:'dist/line-1/35.jpg',width:512,height:512,format:'JPEG',bytes:jpg.length},
 ancestor:source,ancestor_sha256:hash(raw),generated_pigment_sha256:hash(donorRaw),bounds,crop,scale,changed_pixels:changed,
 all_pixels_outside_bounds_identical:true,
 process:'Installed image generator supplied isolated chalk and ochre pigment. Only pigment transferred to bare rock; donor overwritten by full wall. Existing PNG/JPEG helpers reused.',
 visual_review:{status:'pending inspection',unmet_visual_requirements:[]},
 preview_location:'The explicit required numbered JPEG beside its record is the sole new picture outside artifacts.'};
fs.writeFileSync('line-1/wall-review-35.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify(review));
