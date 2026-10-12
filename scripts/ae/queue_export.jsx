#target aftereffects
#include "common.jsxinc"
(function(){var failure=null,selected='';try{
    var cfg=MAD.load(),exportSource=cfg.export_project||cfg.source_project,p=MAD.open(exportSource),master=MAD.comp(p);
    if(cfg.expected_width&&master.width!==cfg.expected_width)throw Error('Width mismatch');
    if(cfg.expected_height&&master.height!==cfg.expected_height)throw Error('Height mismatch');
    if(cfg.expected_fps&&Math.abs(master.frameRate-cfg.expected_fps)>.0001)throw Error('FPS mismatch');
    var output=MAD.uniqueOutput('output_video'),renderProject=MAD.uniqueOutput('render_project',MAD.file(exportSource));
    while(p.renderQueue.numItems)p.renderQueue.item(1).remove();
    var rq=p.renderQueue.items.add(master);for(var r=0;r<rq.templates.length;r++)if(/Best Settings|\u6700\u4f73\u8bbe\u7f6e/.test(rq.templates[r])){rq.applyTemplate(rq.templates[r]);break;}
    rq.timeSpanStart=0;rq.timeSpanDuration=master.duration;var om=rq.outputModule(1),best=-1;
    for(var t=0;t<om.templates.length;t++){var name=om.templates[t];if(!/H\.264/i.test(name))continue;var bit=name.match(/(\d+(?:\.\d+)?)\s*Mbps/i),score=bit?Number(bit[1]):0;if(/Match Render Settings/i.test(name))score+=1000;if(score>best){best=score;selected=name;}}
    if(!selected)throw Error('No H.264 output template available');om.applyTemplate(selected);
    var settings=om.getSettings(GetSettingsFormat.STRING),audioKey=null;for(var k in settings)if(/^(Output Audio|Audio Output)$/i.test(k))audioKey=k;
    if(!audioKey)throw Error('Audio output setting unavailable in this AE environment');om.setSetting(audioKey,'On');om.file=output;rq.render=true;
    p.save(renderProject);
}catch(e){failure=e;}MAD.end(failure,{output_template:selected,operation:'queue_only',post_export_inspection:false});})();

