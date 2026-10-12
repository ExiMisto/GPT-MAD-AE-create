#target aftereffects
#include "common.jsxinc"
(function(){var failure=null,changed=0;try{
    var cfg=MAD.load(),manifest=MAD.read(MAD.file(cfg.archive_manifest)),mapping={},p=MAD.open();
    function key(value){return value.replace(/\\/g,'/').toLowerCase();}
    for(var i=0;i<manifest.files.length;i++){var row=manifest.files[i];if(row.is_sequence)throw Error('Sequence relink is intentionally unsupported');if(/\.(psd|psb|ai|aep|aepx)$/i.test(row.original_path))throw Error('Layer/document relink is intentionally unsupported; use native layer-aware relink');mapping[(row.role||'source')+'|'+key(row.original_path)]=row.archived_path;}
    var master=MAD.comp(p);p.reduceProject([master]);
    for(var j=1;j<=p.numItems;j++){var item=p.item(j);if(!(item instanceof FootageItem))continue;var hadProxy=item.useProxy,entry;
        if(item.file){entry=mapping['source|'+key(item.file.fsName)];if(!entry)throw Error('No archive mapping: '+item.file.fsName);var replacement=new File(entry);if(!replacement.exists)throw Error('Archived file missing');var w=item.width,h=item.height,still=item.mainSource.isStill,duration=item.duration,rate=item.frameRate;item.replace(replacement);if(item.width!==w||item.height!==h||item.mainSource.isStill!==still)throw Error('Replacement changed dimensions or still interpretation');if(!still&&(Math.abs(item.duration-duration)>.0001||Math.abs(item.frameRate-rate)>.0001))throw Error('Replacement changed dynamic-source clock');changed++;}
        if(item.proxySource&&item.proxySource.file){entry=mapping['proxy|'+key(item.proxySource.file.fsName)];if(!entry)throw Error('No proxy archive mapping');var proxy=new File(entry);if(!proxy.exists)throw Error('Archived proxy missing');item.setProxy(proxy);item.useProxy=hadProxy;changed++;}
    }
    p.save(MAD.uniqueOutput('archived_project',MAD.file(cfg.source_project)));
}catch(e){failure=e;}MAD.end(failure,{relinked:changed});})();

