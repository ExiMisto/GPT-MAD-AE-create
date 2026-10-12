#target aftereffects
#include "common.jsxinc"
(function(){var failure=null,result={};try{
    var cfg=MAD.load(),p=MAD.open(),master=MAD.comp(p),seen={},seenSources={},assets=[],fonts={},manual=[],comps=0;
    function source(item,role,sourceObject){if(!sourceObject||!sourceObject.file)return;var f=sourceObject.file,path=f.fsName,id=role+'|'+path;if(seenSources[id])return;seenSources[id]=true;var sequence=!sourceObject.isStill&&/\.(png|jpe?g|tiff?|bmp|exr|dpx)$/i.test(path),layered=/\.(psd|psb|ai|aep|aepx)$/i.test(path);assets.push({path:path,role:role,item_id:item.id,item_name:item.name,exists:f.exists,is_sequence:sequence,requires_manual_relink:layered});if(sequence)manual.push('Image sequence needs whole-frame collection: '+path);if(layered)manual.push('Layer/document interpretation needs manual native relink: '+path);}
    function scanProps(group,label){for(var k=1;k<=group.numProperties;k++){var q=group.property(k);if(q.propertyType===PropertyType.PROPERTY){if(q.canSetExpression&&q.expressionEnabled&&/(?:footage\s*\(|File\s*\(|\$\.|eval\s*\()/i.test(q.expression))manual.push('Expression may reference external data: '+label+'/'+q.name);}else scanProps(q,label+'/'+q.name);}}
    function visit(c){if(seen[c.id])return;seen[c.id]=true;comps++;for(var j=1;j<=c.numLayers;j++){var l=c.layer(j);if(l instanceof TextLayer){try{fonts[l.property('ADBE Text Properties').property('ADBE Text Document').value.font]=true;}catch(e){manual.push('Text font could not be read: '+c.name+'/'+l.name);}}scanProps(l,c.name+'/'+l.name);if(l.source instanceof CompItem)visit(l.source);else if(l.source instanceof FootageItem){source(l.source,'source',l.source.mainSource);source(l.source,'proxy',l.source.proxySource);}}}
    visit(master);var fontNames=[];for(var name in fonts)if(fonts.hasOwnProperty(name))fontNames.push(name);
    result={schema:1,source_project:MAD.file(cfg.source_project).fsName,master_comp:master.name,include_disabled_layers:true,comps:comps,assets:assets,fonts:fontNames,manual_review:manual,limitations:['Fonts and effect plug-ins are not copied by footage traversal.','Expressions may create hidden dependencies.','Image sequences require manual whole-sequence handling.']};
    var report=MAD.uniqueOutput('audit_report');MAD.write(report,result);
}catch(e){failure=e;}MAD.end(failure,{assets:result.assets?result.assets.length:0});})();

