import json

from pydantic import UUID4, ConfigDict, field_validator
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from mealie.db.models.household.household import Household
from mealie.db.models.household.preferences import HouseholdPreferencesModel
from mealie.schema._mealie import MealieModel
from mealie.services.recipe.cooking_tools import COOKING_TOOLS


class UpdateHouseholdPreferences(MealieModel):
    private_household: bool = True
    show_announcements: bool = True

    lock_recipe_edits_from_other_households: bool = True
    first_day_of_week: int = 0

    # Recipe Defaults
    recipe_public: bool = True
    recipe_show_nutrition: bool = False
    recipe_show_assets: bool = False
    recipe_landscape_view: bool = False
    recipe_disable_comments: bool = False

    # Cooking Tools
    cooking_tools: list[str] = []

    @field_validator("cooking_tools", mode="before")
    @classmethod
    def parse_cooking_tools(cls, v):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                v = []
        if not isinstance(v, list):
            return []
        return [t for t in v if t in COOKING_TOOLS]


class CreateHouseholdPreferences(UpdateHouseholdPreferences): ...


class SaveHouseholdPreferences(UpdateHouseholdPreferences):
    household_id: UUID4


class ReadHouseholdPreferences(CreateHouseholdPreferences):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            joinedload(HouseholdPreferencesModel.household).load_only(Household.group_id),
        ]
