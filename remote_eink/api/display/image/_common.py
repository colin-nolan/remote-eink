from marshmallow import Schema, fields


class ImageMetadataSchema(Schema):
    rotation = fields.Float(data_key="rotation")
