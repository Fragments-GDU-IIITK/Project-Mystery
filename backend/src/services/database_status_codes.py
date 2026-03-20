class ServiceStatusCodes:
    @staticmethod
    def success(data = None):
        return {
            "status" : 200,
            "data": data,
        }
    @staticmethod
    def resourceDoesNotExist():
        return {
            "status" : 404,
            "description" : "Resource Does Not Exist"
        }
    @staticmethod
    def resourceAlreadyExists():
        return {
            "status" : 100,
            "description" : "Resource already exists"
        }
    @staticmethod
    def invalidCollectionName():
        return {
            "status" : 101,
            "description" : "Invalid Collection Name"
        }
    @staticmethod
    def internalError():
        return {
            "status": 500,
            "message": "Internal database error"
        }

