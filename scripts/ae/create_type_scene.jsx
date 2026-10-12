#target aftereffects
#include "common.jsxinc"
(function(){var failure=null;try{
    var cfg=MAD.load(),d=cfg.type_demo;if(!d||!d.text)throw Error('type_demo.text is required');
    var fps=d.fps||30,count=d.duration_frames||100,a=d.reveal_start,b=d.reveal_end,c=d.erase_start,e=d.erase_end;
    if(!(a>=0&&b>a&&c>=b&&e>c&&e<=count))throw Error('Invalid frame stages');
    var p=MAD.fresh(),comp=p.items.addComp('TYPE MECHANISM / user text',1920,1080,1,count/fps,fps),bg=comp.layers.addSolid([.96,.97,.99],'GROUND',1920,1080,1),group=p.items.addComp('TYPE GROUP / read then consume',1920,1080,1,count/fps,fps);
    var ink=group.layers.addText(d.text),doc=ink.property('ADBE Text Properties').property('ADBE Text Document'),v=doc.value;v.font=d.font||'ArialMT';v.fontSize=d.font_size||48;v.tracking=d.tracking||0;v.fillColor=[.035,.06,.09];v.applyFill=true;doc.setValue(v);
    var rect=ink.sourceRectAtTime(0,false),tr=ink.property('ADBE Transform Group');tr.property('ADBE Anchor Point').setValue([rect.left+rect.width/2,rect.top+rect.height/2]);tr.property('ADBE Position').setValue([960,540]);
    var solid=group.layers.addSolid([.035,.06,.09],'SOLID CONSUMPTION / covers text before group exit',1920,1080,1),m=solid.property('ADBE Mask Parade').addProperty('ADBE Mask Atom'),mp=m.property('ADBE Mask Shape');
    function shape(left,right){var s=new Shape();s.vertices=[[left,0],[right,0],[right,1080],[left,1080]];s.closed=true;s.inTangents=[[0,0],[0,0],[0,0],[0,0]];s.outTangents=s.inTangents;return s;}
    mp.setValueAtTime(c/fps,shape(0,0));mp.setValueAtTime(e/fps,shape(0,1920));solid.inPoint=c/fps;
    var layer=comp.layers.add(group),mask=layer.property('ADBE Mask Parade').addProperty('ADBE Mask Atom'),path=mask.property('ADBE Mask Shape');path.setValueAtTime(a/fps,shape(0,0));path.setValueAtTime(b/fps,shape(0,1920));layer.outPoint=e/fps;
    // Reveal and erase affect the entire group; text geometry never stretches.
    for(var k=1;k<=path.numKeys;k++)path.setInterpolationTypeAtKey(k,KeyframeInterpolationType.LINEAR,KeyframeInterpolationType.LINEAR);
    for(var j=1;j<=mp.numKeys;j++)mp.setInterpolationTypeAtKey(j,KeyframeInterpolationType.LINEAR,KeyframeInterpolationType.LINEAR);
    p.save(MAD.uniqueOutput('type_project'));
}catch(error){failure=error;}MAD.end(failure,{operation:'original_type_mechanism_only',rendered:false});})();

