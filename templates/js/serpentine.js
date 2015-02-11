/**
 * Client-side javascript utilities for Serpentine web stack
 *
 */



String.prototype.killWhitespace = function() {
    return this.replace(/\s/g, '');
};


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



// Tells us the record ID of the selected row in our data table
function getObjectID(){    
    return $("input.object_id_button:checked").attr("value");
}


function registerAction(actionMap, actionName, functionOrURL, dataValues, selectionMandatory){

    valuesDict = (dataValues === null ) ? {} : dataValues;
    actionMap[actionName] = { 'target': functionOrURL, 'data': valuesDict, 'must_select': selectionMandatory };    
}


function setFormVariableOnAction(formVarMap, actionName, formVarID, value){

    formVarMap[actionName] = {'id': formVarID, 'value': value};
}

    
// Universal logic for managing the dropdown menu/data table UI pattern.
// The actionMap parameter is a dictionary (indexed by action name) that holds 
// the data parameters for table selection logic:
// 'target': function reference or target URL (w/optional embedded variables), 
// 'data': the variables themselves, and 
// 'must_select': a boolean
// signifying whether the selected action requires a row from the table to be selected as well.
// 
function initTableSelectLogic(actionMap, formVarMap){

        /* 
        In the click handler for the go button, we index into the actionMap hashtable
        using the value of the action_selector dropdown.
        */
        $("#go_button").click(function(){
        
            action = $("#action_selector option:selected").attr("id");
            selectedObject = $("input.object_id_button:checked").attr("value"); 
        
            if(formVarMap != null){
            
                sLog("selected action is: " + action);
                
                // set form variables according to the selected user action                
                formVarData = formVarMap[action];
                if(formVarData != null){
                    targetValue = formVarData['value'];
                    if(typeof targetValue == "function"){
                        $("#" + formVarData["id"]).attr("value", targetValue());
                    }  
                    else{
                        $("#" + formVarData["id"]).attr("value", targetValue);
                    }
                }                
            }

            
            // does this action require a selection?
            if(actionMap[action]['must_select'] && selectedObject == null){
                alert("Please select an item from the grid.");     
                return false;           
            }
            else{
            
                if(typeof actionMap[action]['target'] === "function"){
                    // clients may pass a raw function reference
                    actionMap[action]['target']();
                    return false;
                }
                else if(new RegExp("([a-zA-Z\\_\\-]+\\((\\{[a-zA-Z\\_\\-]+\\}){1}\\))").test(actionMap[action]['target'])){ 
                    // We also autodetect functions;
                    // if the target is a string containing a name followed by parentheses 
                    // enclosing a set of matched curly brackets, like this:
                    //
                    // foo({var})
                    //
                    // we interpret it as a function containing a variable argument.
                
                    sLog("Registered a function with one or more embedded variables.");
                    
                    targetString = actionMap[action]['target'];
                    funcName = targetString.slice(0, targetString.indexOf("("));
                    
                    re = new RegExp("{[a-zA-Z\\_\\-]+}");
                    matches = re.exec(targetString);
                    newVar = matches[0];
                    key = newVar.slice(1, newVar.length-1).killWhitespace(); // gives us the string btwn the curly brackets
                        
                    sLog("Retrieved embedded variable: " + key);
                    
                    // the value of the var is supplied by whatever data we passed
                    // to registerAction() in the dataValues parameter, with named variables as keys
                    value = null;
                    
                    obj = actionMap[action]['data'][key]; 
                    if(obj != null){
                        if(typeof obj === "function"){                            
                            value = obj();  // if it's a function, call it                            
                        }
                        else{
                            value = obj;    // otherwise just assign
                        }
                    }
                    
                    sLog("Calling dynamic function " + funcName);                    
                    window[funcName](value);                    
                    
                    return false;
                }
                else{
                    // if the target is not a function reference, we assume it's a URL
                    
                    url = actionMap[action]['target'];
                    // find and resolve embedded variables in the URL,
                    // which are specified as an alphanumeric string between
                    // curly brackets 
                    //
                    var re = new RegExp("{[a-zA-Z]+}");
                    matches = re.exec(url);
                    
                    if(matches != null){
                    
                        sLog("Registered a URL with one or more embedded variables.");
                        
                        for (index = 0; index < matches.length; index++) {
                            newVar = matches[index];
                            key = newVar.slice(1, newVar.length-1).killWhitespace(); // gives us the string btwn the curly brackets
                            
                            sLog("Retrieved embedded variable: " + key);
                            
                            // the value of the var is supplied by whatever data we passed
                            // to registerAction() in the dataValues parameter, with named variables as keys
                            value = null;
                            
                            obj = actionMap[action]['data'][key]; 
                            if(obj === null){
                                continue;
                            }
                            else if(typeof obj === "function"){                            
                                value = obj();  // if it's a function, call it                            
                            }
                            else{
                                value = obj;    // otherwise just assign
                            }
                            
                            sLog("Embedded URL variable " + key + " has value: " + value);
                            
                            if(value != null){
                                newURL = url.replace(newVar, value);
                                actionMap[action]['target'] = newURL;
                            }
                            
                            sLog("updated target URL is " + actionMap[action]['target']);
                            sLog("asset ID in form is " + $("#asset_id").attr("value"));
                        }                    
                    }  
                    
                    $("#action_form").attr("action", actionMap[action]['target']);  
                    return true;
                }           
            }

        });
}
