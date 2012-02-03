function userInit(){

	// select the first option in the action dropdown
	$('#action_selector option:first').attr('selected', true);
			
	selectedAction = $("#action_selector option:first").attr('value');
   	$("#action_form").attr("action", selectedAction);
   	$('input[name=object_id]').attr('checked', false);
   	selectionRequired = false;       	     	
}

function selectAction(event){

	selectedAction = $("#action_selector option:selected").attr('value');
	
	if($("#action_selector option:selected").attr('id') == 'insert'){  
		// user selects add 
		selectionRequired = false;							
	}
	else if($("#action_selector option:selected").attr('id') == 'update'){ 
		// user selects the update option
		selectionRequired = true;	
			
		if($("input[name=object_id]:checked").val()){
			selectedAction = $("#action_selector option:selected").attr('value') + '/' + selectedObject;			
		}	
	}
	
	$("#action_form").attr("action", selectedAction);

		return true;     					       					
}

function selectObject(event){
	selectedObject = $('input.object_id_button:checked').attr('value');    		
	selectedAction = $("#action_selector option:selected").attr('value');
   				       					        				
	if($("#action_selector option:selected").attr('id') == 'update'){
		selectedAction = $("#action_selector option:selected").attr('value') + '/' + selectedObject;	
	}
	        		        				
	$("#action_form").attr("action", selectedAction);
	
	return true;
}
            
            
// global variables
/*
selectedObject = null; 
selectedAction = null;
selectionRequired = true;

var selector = $('#action_selector');		    		

userInit();				
selector.change(function(event){				
	return selectAction(event);									       					
});

$("#submitButton").click(function(event) {  
	//alert(selectedObject);
	if(! selectedObject){
		if(selectionRequired == true){
			alert("Please select an item from the list first.");
			event.preventDefault();
		}
		else{
			return true;
		}
	}
	else{    					
		return true;
    }
}); 
*/