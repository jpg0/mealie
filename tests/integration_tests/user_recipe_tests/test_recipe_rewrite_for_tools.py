import pytest
from fastapi.testclient import TestClient

from mealie.schema.group.ai_providers import AIProviderCreate, AIProviderSettingsUpdate
from mealie.schema.openai.recipe import OpenAIRecipe, OpenAIRecipeIngredient, OpenAIRecipeInstruction
from mealie.services.openai import OpenAIService
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@pytest.fixture()
def seed_recipe(api_client: TestClient, unique_user: TestUser) -> str:
    """Create a recipe in the DB and return its slug."""
    payload = {"name": f"Original Recipe {random_string(5)}"}
    response = api_client.post(api_routes.recipes, json=payload, headers=unique_user.token)
    assert response.status_code == 201
    slug = response.json()

    # Add some content so the rewrite has something to work with
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()
    recipe["recipeIngredient"] = [
        {"note": "2 cups flour"},
        {"note": "1 cup water"},
        {"note": "1 tsp salt"},
    ]
    recipe["recipeInstructions"] = [
        {"text": "Mix flour and salt together."},
        {"text": "Add water and knead into a dough."},
    ]
    api_client.put(api_routes.recipes_slug(slug), json=recipe, headers=unique_user.token)
    return slug


@pytest.fixture(autouse=True)
def setup_ai_provider(unique_user: TestUser):
    """Create a real DB AI provider so the endpoint doesn't reject the request."""
    provider = unique_user.repos.group_ai_providers.create(
        AIProviderCreate(name=random_string(), model="gpt-4o", api_key="test-key")
    )
    unique_user.repos.group_ai_provider_settings.update(
        unique_user.repos.group_id,
        AIProviderSettingsUpdate(
            default_provider_id=provider.id,
            audio_provider_id=None,
            image_provider_id=None,
        ),
    )


from mealie.schema.openai.recipe import OpenAIRecipe, OpenAIRecipeIngredient, OpenAIRecipeInstruction, OpenAIRecipeRewriteResponse

def _mock_openai_recipe() -> OpenAIRecipeRewriteResponse:
    """Return a mock OpenAI response that looks like a rewritten recipe."""
    recipe = OpenAIRecipe(
        name="Rewritten Recipe",
        description="A recipe rewritten for Thermomix",
        recipe_yield="4 servings",
        total_time="30 minutes",
        ingredients=[
            OpenAIRecipeIngredient(title=None, text="2 cups flour"),
            OpenAIRecipeIngredient(title=None, text="3/4 cup water (reduced for pressure cooking)"),
            OpenAIRecipeIngredient(title=None, text="1 tsp salt"),
        ],
        instructions=[
            OpenAIRecipeInstruction(title=None, text="Add flour, water, and salt to the Thermomix bowl."),
            OpenAIRecipeInstruction(title=None, text="Knead for 2 minutes on Dough setting."),
        ],
        notes=[],
    )
    return OpenAIRecipeRewriteResponse(
        is_improved=True,
        reason=None,
        recipe=recipe,
    )


class TestRewriteForToolsTests:
    def test_rewrite_creates_new_recipe(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """The rewrite endpoint should create a new recipe and return it."""
        async def mock_get_response(self, prompt, message, *args, **kwargs):
            return _mock_openai_recipe()

        monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix"]},
            headers=unique_user.token,
        )
        assert response.status_code == 201

        new_recipe = response.json()
        assert new_recipe["name"].endswith("(Thermomix)")
        assert len(new_recipe["recipeIngredient"]) == 3
        assert len(new_recipe["recipeInstructions"]) == 2

    def test_rewrite_preserves_original(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """The original recipe should not be modified."""
        original = api_client.get(
            api_routes.recipes_slug(seed_recipe), headers=unique_user.token
        ).json()

        async def mock_get_response(self, prompt, message, *args, **kwargs):
            return _mock_openai_recipe()

        monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

        api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix"]},
            headers=unique_user.token,
        )

        after = api_client.get(
            api_routes.recipes_slug(seed_recipe), headers=unique_user.token
        ).json()
        assert after["name"] == original["name"]
        assert len(after["recipeIngredient"]) == len(original["recipeIngredient"])

    def test_rewrite_custom_name(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """When a custom name is provided, it should be used."""
        async def mock_get_response(self, prompt, message, *args, **kwargs):
            return _mock_openai_recipe()

        monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

        custom_name = f"My Custom Rewrite {random_string(5)}"
        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix"], "name": custom_name},
            headers=unique_user.token,
        )
        assert response.status_code == 201
        assert response.json()["name"] == custom_name

    def test_rewrite_multiple_tools_name(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """When multiple tools are specified, the name should include all of them."""
        async def mock_get_response(self, prompt, message, *args, **kwargs):
            return _mock_openai_recipe()

        monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix", "pressure_cooker"]},
            headers=unique_user.token,
        )
        assert response.status_code == 201
        name = response.json()["name"]
        assert "Thermomix" in name
        assert "Pressure Cooker" in name

    def test_rewrite_no_tools_returns_400(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        seed_recipe: str,
    ):
        """Requesting a rewrite with no tools should return 400."""
        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": []},
            headers=unique_user.token,
        )
        assert response.status_code == 400

    def test_rewrite_ai_disabled_returns_400(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        seed_recipe: str,
    ):
        """When AI is not configured, the endpoint should return 400."""
        unique_user.repos.group_ai_provider_settings.update(
            unique_user.repos.group_id,
            AIProviderSettingsUpdate(
                default_provider_id=None,
                audio_provider_id=None,
                image_provider_id=None,
            ),
        )

        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix"]},
            headers=unique_user.token,
        )
        assert response.status_code == 400

    def test_rewrite_invalid_tool_returns_error(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """An invalid tool ID should result in an error."""
        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["nonexistent_tool"]},
            headers=unique_user.token,
        )
        assert response.status_code == 500


class TestCookingToolsListTests:
    def test_get_cooking_tools(
        self,
        api_client: TestClient,
        unique_user: TestUser,
    ):
        """The cooking tools endpoint should return the available tools."""
        response = api_client.get(
            api_routes.recipes_cooking_tools,
            headers=unique_user.token,
        )
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) >= 2
        tool_ids = [t["id"] for t in tools]
        assert "thermomix" in tool_ids
        assert "pressure_cooker" in tool_ids

    def test_rewrite_fails_if_not_improved(
        self,
        api_client: TestClient,
        unique_user: TestUser,
        monkeypatch: pytest.MonkeyPatch,
        seed_recipe: str,
    ):
        """When the AI determines the tools do not improve the recipe, the endpoint should return 400."""
        async def mock_get_response(self, prompt, message, *args, **kwargs):
            return OpenAIRecipeRewriteResponse(
                is_improved=False,
                reason="The Thermomix does not improve grilling a steak.",
                recipe=None,
            )
    
        monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)
    
        response = api_client.post(
            api_routes.recipes_slug_rewrite_for_tools(seed_recipe),
            json={"tools": ["thermomix"]},
            headers=unique_user.token,
        )
        assert response.status_code == 400
        assert "does not improve grilling a steak" in response.json()["detail"]["message"]

class TestHouseholdCookingToolsPreferenceTests:
    def test_set_and_get_cooking_tools(
        self,
        api_client: TestClient,
        unique_user: TestUser,
    ):
        """Setting cooking tools in household preferences should persist."""
        # Get current preferences
        response = api_client.get("/api/households/preferences", headers=unique_user.token)
        assert response.status_code == 200
        prefs = response.json()

        # Update with cooking tools
        prefs["cookingTools"] = ["thermomix", "pressure_cooker"]
        response = api_client.put("/api/households/preferences", json=prefs, headers=unique_user.token)
        assert response.status_code == 200
        updated = response.json()
        assert set(updated["cookingTools"]) == {"thermomix", "pressure_cooker"}

        # Read back
        response = api_client.get("/api/households/preferences", headers=unique_user.token)
        assert response.status_code == 200
        assert set(response.json()["cookingTools"]) == {"thermomix", "pressure_cooker"}

    def test_invalid_tool_id_filtered(
        self,
        api_client: TestClient,
        unique_user: TestUser,
    ):
        """Invalid tool IDs should be filtered out by the validator."""
        response = api_client.get("/api/households/preferences", headers=unique_user.token)
        prefs = response.json()

        prefs["cookingTools"] = ["thermomix", "invalid_tool", "pressure_cooker"]
        response = api_client.put("/api/households/preferences", json=prefs, headers=unique_user.token)
        assert response.status_code == 200
        updated = response.json()
        assert "invalid_tool" not in updated["cookingTools"]
        assert "thermomix" in updated["cookingTools"]
