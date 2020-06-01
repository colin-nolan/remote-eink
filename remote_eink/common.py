# class DisplayControllerNotFoundError(ValueError):
#     """
#     Required display controller not found.
#     """
#     def __init__(self, identifier: str = None):
#         super().__init__("" if identifier is None else f"Display controller with ID not found: {identifier}")
#         self.identifier = identifier
