
// Tells us the record ID of the selected row in our data table
function getObjectID(){    
    return $("input.object_id_button:checked").attr("value");
}


function registerAction(actionMap, actionName, actionURL, dataValues, selectionMandatory){

    valuesDict = (dataValues === null ) ? {} : dataValues;
    actionMap[actionName] = { 'url': actionURL, 'data': valuesDict, 'must_select': selectionMandatory };    
}

    
// Universal logic for managing the dropdown menu/data table UI pattern.
// The actionMap parameter is a dictionary (indexed by action name) that holds 
// the data parameters for table selection logic:
// 'url': target URL (w/optional embedded variables), 
// 'data': the variables themselves, and 
// 'must_select': a boolean
// signifying whether the selected action requires a row from the table to be selected as well.
// 
function initTableSelectLogic(actionMap){

        /* 
        In the click handler for the go button, we index into the actionMap hashtable
        using the value of the action_selector dropdown.
        */
        $("#go_button").click(function(){

            action = $("#action_selector option:selected").attr("id");
            selectedObject = $("input.object_id_button:checked").attr("value"); 
            
            // does this action require a selection?
            if(actionMap[action]['must_select'] && selectedObject == null){
                alert("Please select an item from the grid.");     
                return false;           
            }
            else{
                url = actionMap[action]['url'];
                // find and resolve embedded variables in the URL,
                // which are specified as an alphanumeric string between
                // curly brackets 
                //
                var re = new RegExp("{[a-zA-Z]*}");
                matches = re.exec(url);
                
                if(matches != null){
                    
                    for (index = 0; index < matches.length; index++) {
                        newVar = matches[index];
                        key = newVar.slice(1, newVar.length-1) // gives us the string btwn the curly brackets
                        
                        sLog("retrieved embedded variable " + key);
                        // the value of the var is supplied by whatever data we passed
                        // to registerAction in a dictionary, with named variables as keys
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
                        
                        if(value != null){
                            newURL = actionMap[action]['url'].replace(newVar, value);
                            actionMap[action]['url'] = newURL;
                        }
                    }
                }
                
            }
            //alert(actionMap[action]['url']);
            $("#action_form").attr("action", actionMap[action]['url']);
            
            return true;
        });
}
