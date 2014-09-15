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