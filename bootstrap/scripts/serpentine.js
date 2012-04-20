

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
	   if(limitCounter != null){
		  $(limitCounter).attr("value", charsLeft);
		}
	}
}


function getResponse(appName, responderID, callbackFunction, dataParams, dataResolvers){

        $.ajaxSetup({
            cache: false
        });
        
        var dataParams = (dataParams === null) ? {} : dataParams;
        
        
            dataParams["pseudoParam"] = new Date().getTime();
            
            // The dataResolvers param is a hashtable where <key> is a variable name
            // embedded in one or more of the dataParams values, and <value>
            // is either an explicit value or a function which will resolve (supply)
            // the variable's data.
            
            // For example, you might call getResponse and pass { object_id: "{id}"} as the dataParams.
            // Then dataResolver might read { id: 5 } to select a specific value, or "#xxx" where xxx is 
            // a DOM object ID, or a direct reference to a javascript function which will retrieve 
            // the desired value.
            
            
            if(dataResolvers != null){
                
                // find the embedded variables in dataParams
                // -- formatted as {variable} 
                for(var key in dataParams){
                    var re = new RegExp("{[a-zA-Z]*}");
                    matches = re.exec(dataParams[key]);
                
                    if(matches != null){
                    
                        for (index = 0; index < matches.length; index++) {
                            newVar = matches[index];
                            resolverKey = newVar.slice(1, newVar.length-1) // gives us the string btwn the curly brackets
                            
                            value = dataResolvers[resolverKey];
                            if(value === null){
                                continue;
                            }                            
                            else if(typeof value === "function"){
                                resolvedData = dataResolvers[resolverKey]();
                            }
                            else{
                                resolvedData = dataResolvers[resolverKey];
                            }
                            newParam = dataParams[key].replace(newVar, resolvedData);
                            dataParams[key] = newParam;
                        }
                    }
                }
            }
        
        
        
        for(key in dataParams){
            sLog("Value of request param " + key + ": " + dataParams[key] + "\n");
        }
    
    
        $.ajax({
            type: "GET",
            url: "/" + appName + "/responder/" + responderID, 
            data: dataParams,
            success: function(data){  
                callbackFunction(data);               
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
            url: "/" + appName + "/uicontrol/" + controlID, 
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


