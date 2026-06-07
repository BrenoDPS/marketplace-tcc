import pytest
from pydantic import TypeAdapter, ValidationError

from src.schemas.sdui import (
    ApiCallAction,
    CheckoutSummaryBlock,
    HeroBannerBlock,
    HeroBannerProps,
    ImpactBannerBlock,
    NavigateAction,
    NavigatePayload,
    OpenModalAction,
    OpenModalPayload,
    ProductCardBlock,
    ProductCardProps,
    ScreenResponse,
    SustainabilityProps,
    UIAction,
    UIComponent,
)

ui_adapter = TypeAdapter(UIComponent)
action_adapter = TypeAdapter(UIAction)


class TestUIComponentDiscriminator:
    def test_hero_banner_from_dict(self) -> None:
        data = {
            "type": "hero_banner",
            "version": 1,
            "props": {"title": "T", "image_url": "img.png"},
            "actions": [],
        }
        component = ui_adapter.validate_python(data)
        assert isinstance(component, HeroBannerBlock)
        assert component.props.title == "T"
        assert component.version == 1

    def test_product_card_from_dict(self) -> None:
        data = {
            "type": "product_card",
            "version": 1,
            "props": {
                "product_id": "p1",
                "price": 19.9,
                "badge": {"label": "Local", "impact_level": "green"},
            },
            "actions": [],
        }
        component = ui_adapter.validate_python(data)
        assert isinstance(component, ProductCardBlock)
        assert component.props.product_id == "p1"
        assert component.props.badge is not None
        assert component.props.badge.impact_level == "green"

    def test_invalid_component_type_raises(self) -> None:
        data = {"type": "unknown_widget", "version": 1, "props": {}, "actions": []}
        with pytest.raises(ValidationError):
            ui_adapter.validate_python(data)

    def test_checkout_summary_from_dict(self) -> None:
        data = {
            "type": "checkout_summary",
            "version": 1,
            "props": {
                "product_id": "p1",
                "title": "Informatica Acessorios",
                "quantity": 2,
                "unit_price": 10.0,
                "subtotal": 20.0,
                "freight": 5.0,
                "total": 25.0,
            },
            "actions": [],
        }
        component = ui_adapter.validate_python(data)
        assert isinstance(component, CheckoutSummaryBlock)
        assert component.props.quantity == 2
        assert component.props.total == 25.0

    def test_impact_banner_from_dict(self) -> None:
        data = {
            "type": "impact_banner",
            "version": 1,
            "props": {
                "distance_km": 27.0,
                "co2_kg": 0.01,
                "badge": {"label": "Entrega local (~27 km)", "impact_level": "green"},
                "message": "Entrega local com menor impacto.",
            },
            "actions": [],
        }
        component = ui_adapter.validate_python(data)
        assert isinstance(component, ImpactBannerBlock)
        assert component.props.badge is not None
        assert component.props.co2_kg == 0.01

    def test_impact_banner_allows_null_distance_and_badge(self) -> None:
        data = {
            "type": "impact_banner",
            "version": 1,
            "props": {"message": "Sem estimativa de distancia."},
            "actions": [],
        }
        component = ui_adapter.validate_python(data)
        assert isinstance(component, ImpactBannerBlock)
        assert component.props.distance_km is None
        assert component.props.badge is None


class TestUIActionDiscriminator:
    def test_navigate_action(self) -> None:
        data = {"type": "navigate", "payload": {"path": "/home"}}
        action = action_adapter.validate_python(data)
        assert isinstance(action, NavigateAction)
        assert action.payload.path == "/home"
        assert action.payload.replace is False

    def test_api_call_action(self) -> None:
        data = {
            "type": "api_call",
            "payload": {"method": "POST", "path": "/checkout"},
        }
        action = action_adapter.validate_python(data)
        assert isinstance(action, ApiCallAction)
        assert action.payload.method == "POST"

    def test_open_modal_action(self) -> None:
        data = {
            "type": "open_modal",
            "payload": {"modal_id": "m1", "title": "Detalhes"},
        }
        action = action_adapter.validate_python(data)
        assert isinstance(action, OpenModalAction)
        assert action.payload.modal_id == "m1"

    def test_invalid_action_type_raises(self) -> None:
        data = {"type": "unknown_action", "payload": {}}
        with pytest.raises(ValidationError):
            action_adapter.validate_python(data)

    def test_invalid_api_method_raises(self) -> None:
        data = {"type": "api_call", "payload": {"method": "INVALID", "path": "/x"}}
        with pytest.raises(ValidationError):
            action_adapter.validate_python(data)


class TestScreenResponse:
    def test_default_schema_version_is_one(self) -> None:
        response = ScreenResponse(screen_id="home", context="default", components=[])
        assert response.schema_version == 1

    def test_serialization_round_trip(self) -> None:
        response = ScreenResponse(
            screen_id="home",
            context="electronics_expert",
            components=[
                HeroBannerBlock(
                    props=HeroBannerProps(title="T", image_url="img.png"),
                    actions=[NavigateAction(payload=NavigatePayload(path="/x"))],
                ),
                ProductCardBlock(
                    props=ProductCardProps(
                        product_id="p1",
                        price=10.0,
                        badge=SustainabilityProps(label="Local"),
                    ),
                    actions=[OpenModalAction(payload=OpenModalPayload(modal_id="m1"))],
                ),
            ],
        )
        json_str = response.model_dump_json()
        restored = ScreenResponse.model_validate_json(json_str)

        assert restored.schema_version == 1
        assert len(restored.components) == 2
        assert isinstance(restored.components[0], HeroBannerBlock)
        assert isinstance(restored.components[1], ProductCardBlock)
        assert isinstance(restored.components[0].actions[0], NavigateAction)
        assert isinstance(restored.components[1].actions[0], OpenModalAction)
        assert restored.components[1].props.badge is not None
        assert restored.components[1].props.badge.impact_level == "green"

    def test_json_envelope_fields(self) -> None:
        response = ScreenResponse(
            screen_id="home",
            context="ctx",
            components=[
                HeroBannerBlock(
                    props=HeroBannerProps(title="T", image_url="img"),
                ),
            ],
        )
        data = response.model_dump()
        assert data["schema_version"] == 1
        block = data["components"][0]
        assert block["type"] == "hero_banner"
        assert block["version"] == 1
        assert "props" in block
        assert block["actions"] == []
