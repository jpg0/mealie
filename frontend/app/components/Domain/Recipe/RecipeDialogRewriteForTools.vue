<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('recipe.rewrite-for-tools')"
    color="primary"
    :icon="$globals.icons.blender"
    can-submit
    :submit-text="$t('recipe.rewrite-for-tools-submit')"
    :submit-disabled="!selectedTools.length || loading"
    :loading="loading"
    :keep-open="true"
    @submit="handleRewrite()"
  >
    <v-card-text>
      <p class="text-subtitle-2 mb-4">
        {{ $t('recipe.rewrite-for-tools-description') }}
      </p>

      <!-- Tool Selection -->
      <div class="mb-4">
        <p class="text-subtitle-1 font-weight-medium mb-2">
          {{ $t('recipe.rewrite-for-tools-select-tools') }}
        </p>
        <v-checkbox
          v-for="tool in availableTools"
          :key="tool.id"
          :model-value="selectedTools.includes(tool.id)"
          :label="tool.name"
          hide-details
          density="compact"
          color="primary"
          @update:model-value="toggleTool(tool.id, $event)"
        />
      </div>

      <!-- Loading State -->
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        class="mt-4"
      />

      <!-- Error Message -->
      <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
        {{ error }}
      </v-alert>
    </v-card-text>
  </BaseDialog>
</template>

<script setup lang="ts">
import type { Recipe } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";

interface CookingTool {
  id: string;
  name: string;
}

const props = defineProps<{
  recipe: Recipe;
}>();

const emit = defineEmits<{
  rewritten: [slug: string];
}>();

const dialog = defineModel<boolean>({ required: true });

const api = useUserApi();
const i18n = useI18n();
const auth = useMealieAuth();
const { $globals } = useNuxtApp();

const router = useRouter();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || auth.user.value?.groupSlug || "");

// State
const availableTools = ref<CookingTool[]>([]);
const selectedTools = ref<string[]>([]);
const loading = ref(false);
const error = ref("");

// Load available cooking tools on mount
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
  if (enabled) {
    if (!selectedTools.value.includes(toolId)) {
      selectedTools.value = [...selectedTools.value, toolId];
    }
  }
  else {
    selectedTools.value = selectedTools.value.filter(t => t !== toolId);
  }
}

async function handleRewrite() {
  if (!selectedTools.value.length) {
    error.value = i18n.t("recipe.rewrite-for-tools-no-tools") as string;
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const { data: response } = await api.recipes.rewriteForTools(
      props.recipe.slug,
      {
        tools: selectedTools.value,
      },
    );

    if (response && response.slug) {
      alert.success(i18n.t("recipe.rewrite-for-tools-success") as string);
      emit("rewritten", response.slug);
      dialog.value = false;

      // Navigate to the new recipe
      router.push(`/g/${groupSlug.value}/r/${response.slug}`);
    }
    else {
      error.value = i18n.t("recipe.rewrite-for-tools-error") as string;
    }
  }
  catch (err: any) {
    console.error("Rewrite failed:", err);

    // Check for AI disabled error
    if (err?.response?.status === 400) {
      const data = err.response.data;
      if (data?.detail === "ai_disabled") {
        error.value = i18n.t("recipe.rewrite-for-tools-ai-disabled") as string;
      }
      else if (data?.detail?.message) {
        error.value = data.detail.message;
      }
      else {
        error.value = i18n.t("recipe.rewrite-for-tools-error") as string;
      }
    }
    else {
      error.value = i18n.t("recipe.rewrite-for-tools-error") as string;
    }
  }
  finally {
    loading.value = false;
  }
}

// Reset state when dialog closes
watch(dialog, (newVal) => {
  if (!newVal) {
    selectedTools.value = [];
    error.value = "";
  }
});
</script>
