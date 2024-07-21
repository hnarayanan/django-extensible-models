import pytest

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from extensible_models.models import ExtensionSchema, ExtensibleModelMixin
from .models import Tenant, ExampleModel

pytestmark = pytest.mark.django_db


class TestExtensibleModel(TestCase):

    def setUp(self):
        self.tenant1 = Tenant.objects.create(name="Tenant 1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2")
        self.content_type = ContentType.objects.get_for_model(ExampleModel)

    def test_create_extension_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "extra_field": {"type": "string"},
                "number_field": {"type": "number"},
            },
            "required": ["extra_field"],
        }
        extension_schema = ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema
        )
        assert extension_schema.version == 1
        assert extension_schema.schema == schema

    def test_create_multiple_schema_versions(self):
        ExtensionSchema.objects.create(
            tenant=self.tenant1,
            content_type=self.content_type,
            schema={"type": "object", "properties": {"field1": {"type": "string"}}},
        )
        schema2 = ExtensionSchema.objects.create(
            tenant=self.tenant1,
            content_type=self.content_type,
            schema={
                "type": "object",
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "number"},
                },
            },
        )
        assert schema2.version == 2

    def test_extensible_model_creation(self):
        schema = {
            "type": "object",
            "properties": {
                "extra_field": {"type": "string"},
                "number_field": {"type": "number"},
            },
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema
        )
        model = ExampleModel.objects.create(
            name="Test Model",
            tenant=self.tenant1,
            extended_fields={"extra_field": "test value", "number_field": 42},
        )
        assert model.extended_fields["extra_field"] == "test value"
        assert model.extended_fields["number_field"] == 42

    def test_extensible_model_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "extra_field": {"type": "string"},
                "number_field": {"type": "number"},
            },
            "required": ["extra_field"],
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema
        )
        # This should work
        ExampleModel.objects.create(
            name="Valid Model",
            tenant=self.tenant1,
            extended_fields={"extra_field": "test value", "number_field": 42},
        )
        # This should raise a ValidationError
        with pytest.raises(ValidationError):
            ExampleModel.objects.create(
                name="Invalid Model",
                tenant=self.tenant1,
                extended_fields={"number_field": 42},
            )

    def test_tenant_specific_schemas(self):
        schema1 = {
            "type": "object",
            "properties": {"tenant1_field": {"type": "string"}},
        }
        schema2 = {
            "type": "object",
            "properties": {"tenant2_field": {"type": "number"}},
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema1
        )
        ExtensionSchema.objects.create(
            tenant=self.tenant2, content_type=self.content_type, schema=schema2
        )
        model1 = ExampleModel.objects.create(
            name="Tenant 1 Model",
            tenant=self.tenant1,
            extended_fields={"tenant1_field": "test"},
        )
        model2 = ExampleModel.objects.create(
            name="Tenant 2 Model",
            tenant=self.tenant2,
            extended_fields={"tenant2_field": 42},
        )
        assert "tenant1_field" in model1.extended_fields
        assert "tenant2_field" in model2.extended_fields

    def test_schema_versioning(self):
        schema_v1 = {"type": "object", "properties": {"field_v1": {"type": "string"}}}
        schema_v2 = {
            "type": "object",
            "properties": {
                "field_v1": {"type": "string"},
                "field_v2": {"type": "number"},
            },
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema_v1
        )
        model_v1 = ExampleModel.objects.create(
            name="Model V1", tenant=self.tenant1, extended_fields={"field_v1": "test"}
        )
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema_v2
        )
        model_v2 = ExampleModel.objects.create(
            name="Model V2",
            tenant=self.tenant1,
            extended_fields={"field_v1": "test", "field_v2": 42},
        )
        assert model_v1.schema_version == 1
        assert model_v2.schema_version == 2

    def test_update_to_latest_schema(self):
        schema_v1 = {"type": "object", "properties": {"field_v1": {"type": "string"}}}
        schema_v2 = {
            "type": "object",
            "properties": {
                "field_v1": {"type": "string"},
                "field_v2": {"type": "number"},
            },
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema_v1
        )
        model = ExampleModel.objects.create(
            name="Model to Update",
            tenant=self.tenant1,
            extended_fields={"field_v1": "test"},
        )
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema_v2
        )
        model.update_to_latest_schema()
        model.refresh_from_db()
        assert model.schema_version == 2
        assert "field_v2" in model.get_extension_schema()["properties"]

    @pytest.mark.parametrize(
        "field_value, expected_valid",
        [
            ("valid string", True),
            (42, False),
            (None, False),
        ],
    )
    def test_field_type_validation(self, field_value, expected_valid):
        schema = {
            "type": "object",
            "properties": {"string_field": {"type": "string"}},
            "required": ["string_field"],
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema
        )
        if expected_valid:
            ExampleModel.objects.create(
                name="Valid Model",
                tenant=self.tenant1,
                extended_fields={"string_field": field_value},
            )
        else:
            with pytest.raises(ValidationError):
                ExampleModel.objects.create(
                    name="Invalid Model",
                    tenant=self.tenant1,
                    extended_fields={"string_field": field_value},
                )

    def test_no_schema_for_tenant(self):
        # Creating a model without a schema should work
        model = ExampleModel.objects.create(
            name="No Schema Model", tenant=self.tenant1, extended_fields={}
        )
        assert model.extended_fields == {}

    def test_multiple_content_types(self):
        # Assuming you have another model that uses ExtensibleModelMixin
        other_content_type = ContentType.objects.get_for_model(OtherModel)
        schema1 = {
            "type": "object",
            "properties": {"example_field": {"type": "string"}},
        }
        schema2 = {"type": "object", "properties": {"other_field": {"type": "number"}}}
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=self.content_type, schema=schema1
        )
        ExtensionSchema.objects.create(
            tenant=self.tenant1, content_type=other_content_type, schema=schema2
        )
        example_model = ExampleModel.objects.create(
            name="Example Model",
            tenant=self.tenant1,
            extended_fields={"example_field": "test"},
        )
        other_model = OtherModel.objects.create(
            name="Other Model", tenant=self.tenant1, extended_fields={"other_field": 42}
        )
        assert "example_field" in example_model.extended_fields
        assert "other_field" in other_model.extended_fields

    def test_schema_inheritance(self):
        parent_schema = {
            "type": "object",
            "properties": {"parent_field": {"type": "string"}},
        }
        child_schema = {
            "type": "object",
            "properties": {
                "parent_field": {"type": "string"},
                "child_field": {"type": "number"},
            },
        }
        ExtensionSchema.objects.create(
            tenant=self.tenant1,
            content_type=ContentType.objects.get_for_model(ParentModel),
            schema=parent_schema,
        )
        ExtensionSchema.objects.create(
            tenant=self.tenant1,
            content_type=ContentType.objects.get_for_model(ChildModel),
            schema=child_schema,
        )
        child_model = ChildModel.objects.create(
            name="Child Model",
            tenant=self.tenant1,
            extended_fields={"parent_field": "test", "child_field": 42},
        )
        assert "parent_field" in child_model.extended_fields
        assert "child_field" in child_model.extended_fields
