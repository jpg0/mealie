<!-- eslint-disable vue/no-v-html -->
<template>
  <div class="recipe-card">
    <v-btn
      class="no-print"
      icon
      color="primary"
      style="position: fixed; top: 16px; right: 16px; z-index: 10;"
      @click="() => $globals.window.print()"
    >
      <v-icon>{{ $globals.icons.printer }}</v-icon>
    </v-btn>

    <div class="image-ingredients-panel">
      <div v-if="recipeImageUrl" class="hero-image-container">
        <img
          :src="recipeImageUrl"
          class="hero-image"
          alt="Recipe Image"
        >
        <div class="image-fade" />
      </div>
      <div ref="ingredientsContainer" class="ingredients-overlay">
        <div ref="ingredientsContent">
          <div class="section-title ingredients-title">
            {{ $t("recipe.ingredients") }}
          </div>
          <div
            v-for="(ingredientSection, sectionIndex) in ingredientSections"
            :key="`ingredient-section-${sectionIndex}`"
          >
            <h3 v-if="ingredientSection.sectionName" class="section-title">
              {{ ingredientSection.sectionName }}
            </h3>
            <ul class="ingredient-list">
              <li
                v-for="(ingredient, ingredientIndex) in ingredientSection.ingredients"
                :key="`ingredient-${ingredientIndex}`"
                class="ingredient-item"
              >
                <span v-html="parseText(ingredient)" />
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="right-panel">
      <div class="recipe-header-bar">
        <div class="header-top">
          <h1 class="recipe-title">{{ recipe.name }}</h1>
          <div class="metadata-items">
            <div v-if="recipeYield" class="metadata-item" v-html="recipeYield" />
            <div v-if="recipe.prepTime" class="metadata-item">
              Prep: {{ recipe.prepTime }}
            </div>
            <div v-if="recipe.performTime" class="metadata-item">
              Cook: {{ recipe.performTime }}
            </div>
            <div v-if="recipe.totalTime" class="metadata-item">
              Total: {{ recipe.totalTime }}
            </div>
          </div>
        </div>
        <p v-if="recipe.description" class="recipe-description">
          {{ recipe.description }}
        </p>
      </div>

      <div ref="instructionsContainer" class="instructions-body">
        <div ref="instructionsContent">
          <div v-if="instructionSections.length > 0" class="section-title">
            {{ $t("recipe.instructions") }}
          </div>
          <div
            v-for="(instructionSection, sectionIndex) in instructionSections"
            :key="`instruction-section-${sectionIndex}`"
          >
            <div
              v-for="(step, stepIndex) in instructionSection.instructions"
              :key="`instruction-${stepIndex}`"
              class="instruction-step"
            >
              <span class="step-number">{{ stepIndex + instructionSection.stepOffset + 1 }}</span>
              <div class="step-content">
                <h4 v-if="step.title" class="instruction-title">{{ step.title }}</h4>
                <SafeMarkdown :source="step.text" />
              </div>
            </div>
          </div>

          <div v-if="hasNotes" class="notes-section">
            <div v-for="(note, index) in recipe.notes" :key="index">
              <h4 class="section-title">{{ note.title }}</h4>
              <SafeMarkdown :source="note.text" />
            </div>
          </div>

          <div v-if="recipe.orgURL" class="source-footer">
            Source: <a :href="recipe.orgURL" target="_blank" rel="noopener noreferrer">{{ recipe.orgURL }}</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import DOMPurify from "dompurify";
import { useStaticRoutes } from "~/composables/api";
import type { Recipe, RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import { useIngredientTextParser } from "~/composables/recipes";
import { useScaledAmount } from "~/composables/recipes/use-scaled-amount";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  scale?: number;
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1,
});

const { $globals } = useNuxtApp();
const i18n = useI18n();
const { recipeImage } = useStaticRoutes();

const ingredientsContainer = ref<HTMLElement | null>(null);
const ingredientsContent = ref<HTMLElement | null>(null);
const instructionsContainer = ref<HTMLElement | null>(null);
const instructionsContent = ref<HTMLElement | null>(null);

function scaleToFit(container: HTMLElement, content: HTMLElement, maxScale = 1.8) {
  content.style.zoom = "";

  nextTick(() => {
    requestAnimationFrame(() => {
      const containerH = container.clientHeight;
      if (containerH <= 0) return;

      let lo = 0.3;
      let hi = maxScale;

      for (let i = 0; i < 15; i++) {
        const mid = (lo + hi) / 2;
        content.style.zoom = String(mid);

        const overflows = container.scrollHeight > container.clientHeight + 1;
        if (overflows) {
          hi = mid;
        }
        else {
          lo = mid;
        }
      }

      content.style.zoom = String(lo);
      container.dataset.scale = String(lo.toFixed(3));
    });
  });
}

watch(
  () => props.recipe,
  () => {
    nextTick(() => {
      requestAnimationFrame(() => {
        if (ingredientsContainer.value && ingredientsContent.value) {
          scaleToFit(ingredientsContainer.value, ingredientsContent.value);
        }
        if (instructionsContainer.value && instructionsContent.value) {
          scaleToFit(instructionsContainer.value, instructionsContent.value);
        }
      });
    });
  },
  { immediate: true },
);

const hasNotes = computed(() => props.recipe.notes && props.recipe.notes.length > 0);

const recipeImageUrl = computed(() => {
  return recipeImage(props.recipe.id, props.recipe.image);
});

type IngredientSection = {
  sectionName: string;
  ingredients: RecipeIngredient[];
};

type InstructionSection = {
  sectionName: string;
  stepOffset: number;
  instructions: RecipeStep[];
};

const ingredientSections = computed<IngredientSection[]>(() => {
  if (!props.recipe.recipeIngredient) {
    return [];
  }
  const sections: IngredientSection[] = [];
  const addIngredientsToSections = (ingredients: RecipeIngredient[], sections: IngredientSection[], title: string | null) => {
    let section: IngredientSection | undefined;
    if (title) {
      section = sections.find(sec => sec.sectionName === title);
      if (!section) {
        section = { sectionName: title, ingredients: [] };
        sections.push(section);
      }
    }

    ingredients.forEach((ingredient) => {
      if (ingredient.referencedRecipe?.recipeIngredient?.length) {
        addIngredientsToSections(
          ingredient.referencedRecipe.recipeIngredient,
          sections,
          "",
        );
      }
      else {
        const sectionName = title || ingredient.title || "";
        if (sectionName) {
          let sec = sections.find(sec => sec.sectionName === sectionName);
          if (!sec) {
            sec = { sectionName, ingredients: [] };
            sections.push(sec);
          }
          ingredient.title = sectionName;
          sec.ingredients.push(ingredient);
        }
        else {
          if (sections.length === 0) {
            sections.push({
              sectionName: "",
              ingredients: [ingredient],
            });
          }
          else {
            sections[sections.length - 1].ingredients.push(ingredient);
          }
        }
      }
    });
  };

  addIngredientsToSections(props.recipe.recipeIngredient, sections, null);
  return sections;
});

const instructionSections = computed<InstructionSection[]>(() => {
  if (!props.recipe.recipeInstructions) {
    return [];
  }

  return props.recipe.recipeInstructions.reduce((sections, step) => {
    const offset = (() => {
      if (sections.length === 0) {
        return 0;
      }

      const lastOffset = sections[sections.length - 1].stepOffset;
      const lastNumSteps = sections[sections.length - 1].instructions.length;
      return lastOffset + lastNumSteps;
    })();

    if (step.title) {
      sections.push({
        sectionName: step.title,
        stepOffset: offset,
        instructions: [step],
      });

      return sections;
    }

    if (sections.length === 0) {
      sections.push({
        sectionName: "",
        stepOffset: offset,
        instructions: [step],
      });

      return sections;
    }

    sections[sections.length - 1].instructions.push(step);
    return sections;
  }, [] as InstructionSection[]);
});

const { parseIngredientText } = useIngredientTextParser();

function parseText(ingredient: RecipeIngredient) {
  return parseIngredientText(ingredient, props.scale);
}

const yieldDisplay = computed(() => {
  const { scaledAmountDisplay } = useScaledAmount(props.recipe.recipeServings, props.scale);
  return scaledAmountDisplay ? i18n.t("recipe.serves-amount", { amount: scaledAmountDisplay }) as string : "";
});

const recipeYield = computed(() => {
  const { scaledAmountDisplay } = useScaledAmount(props.recipe.recipeYieldQuantity, props.scale);
  if (scaledAmountDisplay && yieldDisplay.value) {
    return DOMPurify.sanitize(`${yieldDisplay.value}; ${scaledAmountDisplay}`);
  }
  else {
    return DOMPurify.sanitize(yieldDisplay.value || scaledAmountDisplay || "");
  }
});
</script>

<style scoped>
.recipe-card {
  --card-accent: #00897B;
  width: 297mm;
  height: 210mm;
  margin: 0 auto;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #333;
  background: white;
  display: grid;
  grid-template-columns: 240px 1fr;
  overflow: hidden;
  box-sizing: border-box;
}

.image-ingredients-panel {
  position: relative;
  overflow: hidden;
}

.hero-image-container {
  position: absolute;
  inset: 0;
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-fade {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.78);
}

.ingredients-overlay {
  position: relative;
  z-index: 1;
  padding: 12px 14px;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}

.ingredients-title {
  font-size: 14px;
  margin-bottom: 6px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.recipe-header-bar {
  padding: 8px 16px 6px;
  border-bottom: 3px solid var(--card-accent);
  flex-shrink: 0;
}

.header-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.recipe-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recipe-description {
  font-size: 11px;
  color: #666;
  margin: 2px 0 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.metadata-items {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.metadata-item {
  font-size: 11px;
  font-weight: 600;
  color: var(--card-accent);
  white-space: nowrap;
}

.instructions-body {
  flex: 1;
  padding: 8px 16px;
  overflow: hidden;
}

.section-title {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 3px;
  color: var(--card-accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ingredient-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ingredient-item {
  padding: 1.5px 0;
  font-size: 10.5px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  line-height: 1.3;
}

.instruction-step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 4px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: var(--card-accent);
  color: white;
  font-weight: 700;
  font-size: 9px;
  margin-right: 5px;
  flex-shrink: 0;
  margin-top: 1px;
}

.instruction-title {
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 1px;
}

.step-content {
  flex: 1;
  font-size: 10.5px;
  line-height: 1.3;
}

.notes-section {
  border-top: 1px solid #e0e0e0;
  padding-top: 4px;
  margin-top: 4px;
}

.notes-section h4 {
  color: var(--card-accent);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 3px;
}

.source-footer {
  font-size: 9px;
  color: #999;
  border-top: 1px solid #e0e0e0;
  padding-top: 3px;
  margin-top: 4px;
}

</style>

<style>
@media print {
  .no-print {
    display: none !important;
  }

  body, html {
    margin: 0 !important;
    padding: 0 !important;
  }

  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  @page {
    size: A4 landscape;
    margin: 0;
  }
}
</style>
