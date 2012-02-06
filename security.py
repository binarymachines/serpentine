


class ObjectType:
    FRAME = 'frame'
    METHOD = 'method'
    TAG = 'tag'



class SecurityManager:
    def __init__(self):
        self.restrictionMap = {}
        

    def restrictObjectAccess(self, objectType, validationFunction, redirectFrameID, **kwargs):        
        if objectType == ObjectType.METHOD:
            controllerID = kwargs.get('controller_id')
            methodName = kwargs.get('method_name')

            if controllerID is None:
                raise SecurityConfigException('Attempted to restrict access to a method without specifying controller_id.')

            if methodName is None:
                raise SecurityConfigException('Attempted to restrict access to a method without specifying method_name.')
            
            self.restrictionMap[(objectType, controllerID, methodName)] = { 'validate_function': validationFunction, 'redirect': redirectFrameID }

        if objectType == ObjectType.FRAME:
            frameID = kwargs.get('frame_id')
            
            if frameID is None:
                raise SecurityConfigException('Attempted to restrict access to a frame without specifying frame_id.')

            self.restrictionMap[frameID] = { 'validate_function': validationFunction, 'redirect': redirectFrameID }
        

   


class SecurityContext:
      def __init__(self, userID, roleID)
        self.userID = userID
        self.roleID = roleID
