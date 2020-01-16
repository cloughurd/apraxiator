from ..apraxiatorexception import ApraxiatorException

class StorageException(ApraxiatorException):
    def __init__(self, inner_error=None):
        self.inner_error = inner_error

    def get_message(self):
        return 'Problem Accessing Storage'

    def get_code(self):
        return 500

class ResourceNotFoundException(StorageException):
    def __init__(self, resource_id, inner_error=None):
        super(inner_error)
        self.resource_id = resource_id

    def get_message(self):
        return 'Resource {} Not Found'.format(self.resource_id)

    def get_code(self):
        return 404

class PermissionDeniedException(StorageException):
    def __init__(self, resource_id, user_id, inner_error=None):
        super(inner_error)
        self.resource_id = resource_id
        self.user_id = user_id

    def get_message(self):
        return 'Permission Denied to User {} for Resource {}'.format(self.user_id, self.resource_id)

    def get_code(self):
        return 403