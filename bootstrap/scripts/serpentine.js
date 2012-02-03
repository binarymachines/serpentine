

// use a less common namespace than just 'log'
function sLog(msg){
    // attempt to send a message to the console
    try{
        console.log(msg);
    }
    // fail gracefully if it does not exist
    catch(e){}
}


function limitText(limitField, limitCounter, limitNum) {

    var charsLeft = 0;
	if ($(limitField).attr("value").length > limitNum) {
		$(limitField).attr("value", $(limitField).attr("value").substring(0, limitNum));
		
	} 
	else {
	   charsLeft = limitNum - $(limitField).attr("value").length;
		//$(limitCounter).attr("value", limitNum - $(limitField).attr("value").length);
	}
	
	//sLog(charsLeft + " characters left.");
}


function renderHTML(appName, frameID, targetDivID, dataParams){

        $.ajaxSetup({
            cache: false
        });
        
        if(dataParams != null){
            dataParams["pseudoParam"] = new Date().getTime();
        }
        
        for(key in dataParams){
            sLog("Value of request param " + key + ": " + dataParams[key]);
        }
    
        $.ajax({
            type: "GET",
            url: "/" + appName + "/frame/" + frameID, 
            data: dataParams,
            success: function(data){  
                divSelector = "#" + targetDivID;                     
                $(divSelector).html(data);
                
            }
        }); 
}


function renderControl(appName, controlID, targetDivID, callbackFunc, dataParams){

        $.ajaxSetup({
            cache: false
        });
    
        if(dataParams != null){            
            dataParams["pseudoParam"] = new Date().getTime();    
            for(key in dataParams){
               sLog("Value of request param " + key + ": " + dataParams[key]);
            }        
        }
            
        $.ajax({
            type: "GET",
            url: "/" + appName + "/responder/" + controlID, 
            data: dataParams,
            success: function(data){  
                divSelector = "#" + targetDivID;                     
                $(divSelector).html(data);  
                if(callbackFunc != null){
                    callbackFunc(data);            
                }                
            }
        }); 
}



function renderRadioGroup(appName, controlID, targetDivID, dataParams){

        $.ajaxSetup({
            cache: false
        });
    
        $.ajax({
            type: "GET",
            url: "/" + appName + "/control/radiogroup/" + controlID, 
            data: dataParams,
            success: function(data){  
                divSelector = "#" + targetDivID;                     
                $(divSelector).html(data);
                // TODO: return JSON status code & alert on error 
            }
        }); 
}