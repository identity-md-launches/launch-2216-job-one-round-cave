// Preserve every ancestral pixel except pigment from the generated new motif.
// Node built-ins only; reads/writes only the explicitly named workspace images.
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
function decode(data) {
  let pos=8, idat=[], width,height;
  while(pos<data.length){let n=data.readUInt32BE(pos), kind=data.toString('ascii',pos+4,pos+8), p=data.subarray(pos+8,pos+8+n);
    if(kind==='IHDR'){width=p.readUInt32BE(0);height=p.readUInt32BE(4);if(p[8]!==8||p[9]!==2||p[12]!==0)throw Error('RGB8 noninterlaced required');}
    if(kind==='IDAT')idat.push(p);pos+=n+12;}
  let raw=zlib.inflateSync(Buffer.concat(idat)), stride=width*3, pixels=Buffer.alloc(width*height*3);
  if(raw.length!==(stride+1)*height)throw Error('scanline size');
  for(let y=0;y<height;y++){let mode=raw[y*(stride+1)];for(let x=0;x<stride;x++){
    let k=y*stride+x,a=x>=3?pixels[k-3]:0,b=y?pixels[k-stride]:0,c=y&&x>=3?pixels[k-stride-3]:0,p=0;
    if(mode===1)p=a;else if(mode===2)p=b;else if(mode===3)p=Math.floor((a+b)/2);else if(mode===4){let v=a+b-c, da=Math.abs(v-a),db=Math.abs(v-b),dc=Math.abs(v-c);p=da<=db&&da<=dc?a:db<=dc?b:c;}else if(mode!==0)throw Error('filter');
    pixels[k]=(raw[y*(stride+1)+1+x]+p)&255;}}
  return {width,height,pixels};
}
function crc(data){let c=0xffffffff;for(let b of data){c^=b;for(let j=0;j<8;j++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
function chunk(name,data){let kind=Buffer.from(name),out=Buffer.alloc(data.length+12);out.writeUInt32BE(data.length,0);kind.copy(out,4);data.copy(out,8);out.writeUInt32BE(crc(Buffer.concat([kind,data])),data.length+8);return out;}
function encode(img){let header=Buffer.alloc(13);header.writeUInt32BE(img.width,0);header.writeUInt32BE(img.height,4);header[8]=8;header[9]=2;
 let stride=img.width*3,raw=Buffer.alloc((stride+1)*img.height);for(let y=0;y<img.height;y++)img.pixels.copy(raw,y*(stride+1)+1,y*stride,(y+1)*stride);
 return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}

const ancestor='artifacts/gathering/wall-v16.png', target='artifacts/gathering/wall-v17.png';
const before=fs.readFileSync(ancestor), donor=fs.readFileSync(target), a=decode(before), d=decode(donor);
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const box=[560,120,680,200], crop=[405,255,1125,730];
const original=Buffer.from(a.pixels);
if(a.width!==1254||a.height!==1254)throw Error('Ancestor dimensions');
if(d.width===a.width&&d.height===a.height)throw Error('Refusing to repaint completed wall');
for(let y=box[1];y<box[3];y++)for(let x=box[0];x<box[2];x++){
 const sx=Math.floor(crop[0]+(x-box[0])*(crop[2]-crop[0])/(box[2]-box[0]));
 const sy=Math.floor(crop[1]+(y-box[1])*(crop[3]-crop[1])/(box[3]-box[1]));
 const j=(sy*d.width+sx)*3,k=(y*a.width+x)*3;
 const r=d.pixels[j],g=d.pixels[j+1],b=d.pixels[j+2];
 if(r<45||r<g||g<b)continue;
 const alpha=Math.min(.76,(r-35)/220);
 for(let c=0;c<3;c++)a.pixels[k+c]=Math.round(a.pixels[k+c]*(1-alpha)+d.pixels[j+c]*alpha);
}
let changed=0;for(let k=0;k<a.pixels.length;k+=3)if(!original.subarray(k,k+3).equals(a.pixels.subarray(k,k+3)))changed++;
if(changed<100)throw Error('Missing new pigment');
fs.writeFileSync(target,encode(a));
fs.writeFileSync('gathering/mark-process17.json',JSON.stringify({method:'Generated isolated pigment motif, transferred only nonblack mineral pigment to bare upper-center rock; no background regeneration.',image_tool:'mcp__image__generate_image',prompt:'Two rough chalk curves shelter yellow and red ochre pebbles linked by a broken charcoal thread; porous worn mineral pigment on black; no writing, hands or symbols.',ancestor,ancestor_sha256:hash(before),generated_donor_sha256:hash(donor),donor_dimensions:[d.width,d.height],donor_crop:crop,destination_box:box,changed_pixels:changed,preservation:'All decoded pixels outside the small pigment transfer are identical to Gathering 16.'},null,2)+'\n');
console.log({width:a.width,height:a.height,changed});
