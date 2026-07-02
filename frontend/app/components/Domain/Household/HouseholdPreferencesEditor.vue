<template>
  <div v-if="preferences">
    <BaseCardSectionTitle :title="$t('household.household-preferences')" />
    <div class="mb-6">
      <v-checkbox v-model="local.privateHousehold" hide-details density="compact" :label="$t('household.private-household')" color="primary" />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("household.private-household-description") }}
        </p>
        <DocLink class="mt-2" link="/documentation/getting-started/faq/#how-do-private-groups-and-recipes-work" />
      </div>
    </div>
    <div class="mb-6">
      <v-checkbox v-model="local.lockRecipeEditsFromOtherHouseholds" hide-details density="compact" :label="$t('household.lock-recipe-edits-from-other-households')" color="primary" />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("household.lock-recipe-edits-from-other-households-description") }}
        </p>
      </div>
    </div>
    <div class="mb-6">
      <v-checkbox
        v-model="local.showAnnouncements"
        hide-details
        density="compact"
        color="primary"
        :label="$t('announcements.show-announcements-from-mealie')"
      />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("announcements.show-announcements-setting-description") }}
        </p>
      </div>
    </div>
    <v-select
      v-model="local.firstDayOfWeek"
      :prepend-icon="$globals.icons.calendarWeekBegin"
      :items="allDays"
      item-title="name"
      item-value="value"
      :label="$t('settings.first-day-of-week')"
      variant="underlined"
      flat
    />

    <BaseCardSectionTitle class="mt-5" :title="$t('household.household-recipe-preferences')">
      {{ $t("household.default-recipe-preferences-description") }}
    </BaseCardSectionTitle>
    <div class="preference-container">
      <div v-for="p in recipePreferences" :key="p.key">
        <v-checkbox v-model="local[p.key]" hide-details density="compact" :label="p.label" color="primary" />
        <p class="ml-8 text-subtitle-2 my-0 py-0">
          {{ p.description }}
        </p>
      </div>
    </div>

    <!-- Cooking Tools Section -->
    <BaseCardSectionTitle class="mt-5" :title="$t('household.cooking-tools')">
      {{ $t('household.cooking-tools-description') }}
    </BaseCardSectionTitle>
    <div class="preference-container">
      <div v-for="tool in availableTools" :key="tool.id">
        <v-checkbox
          :model-value="local.cookingTools?.includes(tool.id)"
          hide-details
          density="compact"
          color="primary"
          :label="tool.name"
          @update:model-value="toggleTool(tool.id, $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ReadHouseholdPreferences } from "~/lib/api/types/household";
import { useUserApi } from "~/composables/api";

const preferences = defineModel<ReadHouseholdPreferences>({ required: true });
const local = reactive({ ...preferences.value });
watch(local, (newVal) => { preferences.value = { ...newVal }; });

const i18n = useI18n();
const api = useUserApi();

// Load available cooking tools
const availableTools = ref<Array<{ id: string; name: string }>>([]);

onMounted(async () => {
  try {
    const { data } = await api.recipes.getCookingTools();
    if (data) {
      availableTools.value = data;
    }
  }
  catch (err) {
    console.error("Failed to load cooking tools:", err);
  }
});

function toggleTool(toolId: string, enabled: boolean | null) {
  if (!local.cookingTools) {
    local.cookingTools = [];
  }
  if (enabled) {
    if (!local.cookingTools.includes(toolId)) {
      local.cookingTools = [...local.cookingTools, toolId];
    }
  }
  else {
    local.cookingTools = local.cookingTools.filter((t: string) => t !== toolId);
  }
}

type Preference = {
  key: keyof ReadHouseholdPreferences;
  label: string;
  description: string;
};

const recipePreferences: Preference[] = [
  {
    key: "recipePublic",
    label: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes"),
    description: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes-description"),
  },
  {
    key: "recipeShowNutrition",
    label: i18n.t("group.show-nutrition-information"),
    description: i18n.t("group.show-nutrition-information-description"),
  },
  {
    key: "recipeShowAssets",
    label: i18n.t("group.show-recipe-assets"),
    description: i18n.t("group.show-recipe-assets-description"),
  },
  {
    key: "recipeLandscapeView",
    label: i18n.t("group.default-to-landscape-view"),
    description: i18n.t("group.default-to-landscape-view-description"),
  },
  {
    key: "recipeDisableComments",
    label: i18n.t("group.disable-users-from-commenting-on-recipes"),
    description: i18n.t("group.disable-users-from-commenting-on-recipes-description"),
  },
];

const allDays = [
  {
    name: i18n.t("general.sunday"),
    value: 0,
  },
  {
    name: i18n.t("general.monday"),
    value: 1,
  },
  {
    name: i18n.t("general.tuesday"),
    value: 2,
  },
  {
    name: i18n.t("general.wednesday"),
    value: 3,
  },
  {
    name: i18n.t("general.thursday"),
    value: 4,
  },
  {
    name: i18n.t("general.friday"),
    value: 5,
  },
  {
    name: i18n.t("general.saturday"),
    value: 6,
  },
];
</script>

<style lang="css">
.preference-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 600px;
}
</style>
