// One-time pigment transfer from the built-in imagegen edit. Node built-ins only.
// The generated wall-v16 donor is overwritten by the preserved final wall.
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
function decode(data) {
  let pos=8, idat=[], width,height;
  if(data.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('PNG');
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
const ancestor='artifacts/line-4/wall-v16.png', target='artifacts/line-4/wall-v17.png';
const before=fs.readFileSync(ancestor), donor=fs.readFileSync(target), a=decode(before), d=decode(donor);
if(a.width!==1254||a.height!==1254||d.width!==a.width||d.height!==a.height)throw Error('dimensions');
let changed=0, bbox=[1254,1254,0,0], classes={charcoal:0,ochre:0,chalk:0};
const box=[40,805,175,925];
for(let y=box[1];y<box[3];y++)for(let x=box[0];x<box[2];x++){
  const k=(y*a.width+x)*3, r=d.pixels[k],g=d.pixels[k+1],b=d.pixels[k+2];
  const charcoal=((x-65)/20)**2+((y-834)/21)**2<1 && r<90 && g<70 && b<50;
  const ochre=((x-143)/19)**2+((y-891)/28)**2<1 && r>65&&g<110&&b<60&&r>g*2.1;
  const chalk=x>=67&&x<=140&&y>=841&&y<=893&&r>185&&g>140&&b>95&&
    r+g+b>a.pixels[k]+a.pixels[k+1]+a.pixels[k+2]+100;
  if(charcoal||ochre||chalk){
    if(!a.pixels.subarray(k,k+3).equals(d.pixels.subarray(k,k+3))){
      changed++;bbox=[Math.min(bbox[0],x),Math.min(bbox[1],y),Math.max(bbox[2],x),Math.max(bbox[3],y)];
      classes[charcoal?'charcoal':ochre?'ochre':'chalk']++;
    }
    d.pixels.copy(a.pixels,k,k,k+3);
  }
}
if(changed<500)throw Error('missing motif pigment');
fs.writeFileSync(target,encode(a));
fs.writeFileSync('line-4/mark-34-process.json',JSON.stringify({method:'Transfer generated coal, ember and chalk-path pigment only; preserve every other inherited pixel.',image_tool:'built-in image_gen',ancestor,ancestor_sha256:crypto.createHash('sha256').update(before).digest('hex'),pigment_donor_sha256:crypto.createHash('sha256').update(donor).digest('hex'),destination_box:box,changed_pixels:changed,changed_bbox_xyxy_inclusive:bbox,pigment_pixels:classes,preservation:'All pixels outside selected new pigment are identical to mark 33.'},null,2)+'\n');
console.log({width:a.width,height:a.height,changed,bbox,classes});
