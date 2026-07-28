import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Validator } from '../src/validator.js';
import { Player } from '../src/player.js';
import { SpacedRetrievalEngine } from '../src/spaced.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define directories for temp files
const tempDir = path.join(__dirname, 'temp');
if (!fs.existsSync(tempDir)) {
  fs.mkdirSync(tempDir);
}

// 1. Create temporary mock configuration and levels files for testing
const germanProfilePath = path.join(tempDir, 'german_profile.json');
const germanLevelsPath = path.join(tempDir, 'german_levels.json');
const germanExamPath = path.join(tempDir, 'german_exam.json');

const hindiProfilePath = path.join(tempDir, 'hindi_profile.json');

// Write profile configurations
fs.writeFileSync(germanProfilePath, JSON.stringify({
  "language": "german",
  "permitted_genders": ["masculine", "feminine", "neuter", "common"],
  "active_phonetic_systems": [],
  "script_traits": {
    "is_abugida": false,
    "has_matra": false,
    "has_sound_family": false
  }
}, null, 2));

fs.writeFileSync(hindiProfilePath, JSON.stringify({
  "language": "hindi",
  "permitted_genders": ["masculine", "feminine"],
  "active_phonetic_systems": ["abugida"],
  "script_traits": {
    "is_abugida": true,
    "has_matra": true,
    "has_sound_family": true
  }
}, null, 2));

// Write German Levels JSON (No 'matra' or 'sound_family' for non-Abugida, uses neuter/common genders, exactly 3 items per level)
const mockGermanLevels = {
  "module": 1,
  "module_name_en": "German Basics",
  "levels": [
    {
      "level": 1,
      "title_en": "Nouns and Genders",
      "is_micro_dialogue_level": false,
      "items": [
        {
          "id": "DE-L01-I1",
          "type": "word",
          "target": "Buch",
          "read_as": "buuch",
          "gloss_en": "book",
          "gender": "neuter",
          "difficulty": 1,
          "tags": ["noun"],
          "cards": {
            "learn": {
              "title_en": "das Buch",
              "explanation_en": "German neuter noun for book."
            },
            "practice": {
              "format": "multiple_choice",
              "prompt_en": "What gender is Buch?",
              "options": ["masculine", "feminine", "neuter"],
              "answer_index": 2
            },
            "game": {
              "format": "sorting",
              "engine": "sorting",
              "categories": ["neuter", "common"],
              "items": [
                { "text": "Buch", "category": "neuter" },
                { "text": "Mensch", "category": "common" }
              ]
            }
          }
        },
        {
          "id": "DE-L01-I2",
          "type": "word",
          "target": "Mensch",
          "read_as": "mensch",
          "gloss_en": "human",
          "gender": "common",
          "difficulty": 2,
          "tags": ["noun"],
          "cards": {
            "learn": {
              "title_en": "der Mensch",
              "explanation_en": "Common/masculine noun for human."
            },
            "practice": {
              "format": "multiple_choice",
              "prompt_en": "What gender is Mensch?",
              "options": ["masculine", "feminine", "neuter", "common"],
              "answer_index": 3
            },
            "game": {
              "format": "sorting",
              "engine": "sorting",
              "categories": ["neuter", "common"],
              "items": [
                { "text": "Buch", "category": "neuter" },
                { "text": "Mensch", "category": "common" }
              ]
            }
          }
        },
        {
          "id": "DE-L01-I3",
          "type": "word",
          "target": "Haus",
          "read_as": "haos",
          "gloss_en": "house",
          "gender": "neuter",
          "difficulty": 1,
          "tags": ["noun"],
          "cards": {
            "learn": {
              "title_en": "das Haus",
              "explanation_en": "Neuter noun for house."
            },
            "practice": {
              "format": "multiple_choice",
              "prompt_en": "What gender is Haus?",
              "options": ["masculine", "feminine", "neuter"],
              "answer_index": 2
            },
            "game": {
              "format": "sorting",
              "engine": "sorting",
              "categories": ["neuter", "common"],
              "items": [
                { "text": "Buch", "category": "neuter" },
                { "text": "Mensch", "category": "common" }
              ]
            }
          }
        }
      ],
      "summary": {
        "recap_en": "Learned some basic German nouns and genders.",
        "key_forms": ["Buch", "Mensch", "Haus"],
        "next_up_en": "German adjectives next."
      }
    }
  ]
};
fs.writeFileSync(germanLevelsPath, JSON.stringify(mockGermanLevels, null, 2));

// Write German Custom Exam JSON
const mockGermanExam = {
  "module": 1,
  "kind": "custom_exam",
  "questions": [
    {
      "id": "DE-EXAM-Q1",
      "source_item_ids": ["DE-L01-I1"],
      "type": "recognition",
      "prompt_en": "What does Buch mean?",
      "options": ["book", "house", "human"],
      "answer_index": 0,
      "explanation_en": "Buch is book."
    },
    {
      "id": "DE-EXAM-Q2",
      "source_item_ids": ["DE-L01-I2"],
      "type": "recognition",
      "prompt_en": "What does Mensch mean?",
      "options": ["book", "house", "human"],
      "answer_index": 2,
      "explanation_en": "Mensch is human."
    }
  ]
};
fs.writeFileSync(germanExamPath, JSON.stringify(mockGermanExam, null, 2));


// --- TEST CASES ---
console.log("🚀 Starting Tests for Declarative Language Profiles & Parametric Game Engines...\n");

function runTest(testName, testFn) {
  try {
    testFn();
    console.log(`✅ Passed: ${testName}`);
  } catch (err) {
    console.error(`❌ Failed: ${testName}`);
    console.error(err);
    process.exit(1);
  }
}

// 1. German levels gender verification ("neuter" & "common")
runTest("German level validation using 'neuter' and 'common' genders", () => {
  const validator = new Validator(germanProfilePath);
  const registerErrors = validator.registerLevels(germanLevelsPath);
  assert.strictEqual(registerErrors.length, 0, "Registering levels should have 0 errors");

  const valErrors = validator.validateLevelFile(germanLevelsPath);
  assert.strictEqual(valErrors.length, 0, "Validating levels should have 0 errors (gender types should be successfully accepted)");
});

// 2. successful omit of matra or sound_family on non-Abugida script
runTest("Non-Abugida levels should omit 'matra' or 'sound_family' without error", () => {
  const validator = new Validator(germanProfilePath);
  validator.registerLevels(germanLevelsPath);
  const valErrors = validator.validateLevelFile(germanLevelsPath);
  // Checking that omitted fields are perfectly allowed for non-abugidas
  assert.ok(valErrors.every(err => !err.message.includes("matra") && !err.message.includes("sound_family")));
});

// 3. Referential integrity rule verification
runTest("Referential integrity checks for valid custom module exams", () => {
  const validator = new Validator(germanProfilePath);
  validator.registerLevels(germanLevelsPath);
  const valErrors = validator.validateMockFile(germanExamPath);
  assert.strictEqual(valErrors.length, 0, "No referential integrity errors expected when all ids exist");
});

runTest("Referential integrity checks should flag broken/non-existent item IDs", () => {
  const validator = new Validator(germanProfilePath);
  validator.registerLevels(germanLevelsPath);

  // Write a broken exam referencing a non-existent item id 'DE-L01-I99'
  const brokenExamPath = path.join(tempDir, 'broken_exam.json');
  fs.writeFileSync(brokenExamPath, JSON.stringify({
    "module": 1,
    "questions": [
      {
        "id": "DE-EXAM-Q1",
        "source_item_ids": ["DE-L01-I99"], // Broken reference!
        "type": "recognition",
        "prompt_en": "What is going on?",
        "options": ["nothing", "something"],
        "answer_index": 0,
        "explanation_en": "..."
      }
    ]
  }));

  const valErrors = validator.validateMockFile(brokenExamPath);
  assert.ok(valErrors.length > 0, "Should detect referential integrity failure");
  assert.ok(valErrors[0].message.includes("Referential Integrity violation"), "Error message should mention referential integrity");
});

// 4. Runtime player sorting game instantiation and rendering
runTest("Runtime player instantiates and renders sorting game without crashing", () => {
  const validator = new Validator(germanProfilePath);
  validator.registerLevels(germanLevelsPath);
  const item = validator.itemMap.get("DE-L01-I1").data;

  // Instantiate Player using German book card game configuration
  const player = new Player(item.cards.game);
  const state = player.instantiate();

  assert.strictEqual(state.engine, 'sorting');
  assert.deepStrictEqual(state.categories, ['neuter', 'common']);
  assert.strictEqual(state.items.length, 2);

  const renderOutput = player.render();
  assert.strictEqual(renderOutput.engine, 'sorting');
  assert.ok(renderOutput.html.includes('sorting-game'));
  assert.ok(renderOutput.html.includes('Buch'));
  assert.ok(renderOutput.html.includes('Mensch'));

  // Test submitting sort action
  const isCorrect = player.submitSortAction(state.items[0].id, 'neuter');
  assert.strictEqual(isCorrect, true, "Buch should be classified as neuter");
});

// 5. Run checks on all Hindi files to ensure complete integrity of existing curriculum
runTest("Integrity run over full Hindi dataset module 1 levels, checkpoint, mock, and spine", () => {
  const hindiProfile = path.join(__dirname, '..', 'profiles', 'hindi.json');
  const validator = new Validator(hindiProfile);

  const module1Levels = path.join(__dirname, '..', 'hindi dataset', 'module01_levels01-05.json');
  const module1CP = path.join(__dirname, '..', 'hindi dataset', 'module01_checkpoint1.json');
  const module1Mock = path.join(__dirname, '..', 'hindi dataset', 'module01_mock.json');

  const regErrors = validator.registerLevels(module1Levels);
  assert.strictEqual(regErrors.length, 0, "Should register Hindi Module 1 levels without error");

  const valErrors = validator.validateLevelFile(module1Levels);
  assert.strictEqual(valErrors.length, 0, "Should validate Hindi Module 1 levels without error");

  const cpErrors = validator.validateCheckpointFile(module1CP);
  assert.strictEqual(cpErrors.length, 0, "Should satisfy Hindi Checkpoint 1 referential integrity");

  const mockErrors = validator.validateMockFile(module1Mock);
  assert.strictEqual(mockErrors.length, 0, "Should satisfy Hindi Mock Exam 1 referential integrity");
});

// 6. Spaced retrieval dynamic scheduling based on custom tag anchors
runTest("Spaced retrieval schedules dynamically based on custom tag anchors", () => {
  const engine = new SpacedRetrievalEngine();
  
  const itemNoAnchors = { id: "SR-1", tags: ["noun", "regular"] };
  const itemWithMultiplier = { id: "SR-2", tags: ["noun", "anchor:multiplier:1.5", "anchor:ease:3.0"] };
  const itemWithFixedInterval = { id: "SR-3", tags: ["noun", "anchor:interval:10"] };

  // Verify parser
  const anchors1 = engine.parseAnchors(itemNoAnchors);
  assert.deepStrictEqual(anchors1, {}, "Should parse no anchors for clean tags");

  const anchors2 = engine.parseAnchors(itemWithMultiplier);
  assert.strictEqual(anchors2.multiplier, 1.5, "Should correctly parse multiplier anchor");
  assert.strictEqual(anchors2.ease, 3.0, "Should correctly parse ease anchor");

  const anchors3 = engine.parseAnchors(itemWithFixedInterval);
  assert.strictEqual(anchors3.interval, 10, "Should correctly parse fixed interval anchor");

  // Verify scheduling
  const state = { repetitions: 2, interval: 6, easeFactor: 2.5 };
  
  // No anchors
  const nextNoAnchors = engine.scheduleNextReview(itemNoAnchors, state, 5);
  // normal SM-2: interval = Math.round(6 * 2.5) = 15
  assert.strictEqual(nextNoAnchors.interval, 15, "Standard interval should be 15 days");

  // Multiplier anchor (1.5)
  const nextWithMultiplier = engine.scheduleNextReview(itemWithMultiplier, state, 5);
  // interval = Math.round(Math.round(6 * 2.5) * 1.5) = Math.round(15 * 1.5) = 23
  assert.strictEqual(nextWithMultiplier.interval, 23, "Multiplier should scale the interval to 23");
  assert.strictEqual(nextWithMultiplier.easeFactor, 3.0, "Ease should be overridden by anchor value");

  // Fixed interval anchor (10)
  const nextWithFixed = engine.scheduleNextReview(itemWithFixedInterval, state, 5);
  assert.strictEqual(nextWithFixed.interval, 10, "Fixed interval override should be enforced as exactly 10 days");
});

// 7. Player runtime parameter mapping from gameplay tags
runTest("Player maps parsed tag parameters to gameplay properties at runtime", () => {
  const customConfig = {
    engine: "sorting",
    question_en: "Practice sorting",
    tags: ["gameplay:difficulty:hard", "gameplay:timer:45", "gameplay:theme:sepia", "gameplay:options_count:1"],
    categories: ["neuter", "common"],
    items: [
      { text: "Buch", category: "neuter" },
      { text: "Mensch", category: "common" }
    ]
  };

  const player = new Player(customConfig);
  const state = player.instantiate();

  assert.strictEqual(state.difficulty, "hard", "Difficulty property should be mapped to 'hard'");
  assert.strictEqual(state.timer, 45, "Timer property should be mapped to 45");
  assert.strictEqual(state.theme, "sepia", "Theme property should be mapped to 'sepia'");
  assert.strictEqual(state.items.length, 1, "Options count tag should slice items array to length 1");

  const renderOutput = player.render();
  assert.ok(renderOutput.html.includes("theme-sepia"), "HTML markup should contain theme-sepia class");
  assert.ok(renderOutput.html.includes("game-timer"), "HTML markup should contain timer overlay");
});

// 8. Expansion language bypass in Validator
runTest("Validator bypasses Hindi pronunciation, spelling, and gender checks on expansion tags", () => {
  // Use a Hindi validator profile
  const validator = new Validator(hindiProfilePath);

  // Define custom German level within a Hindi registry, carrying expansion and gender/script override tags
  const hybridLevelsPath = path.join(tempDir, "hybrid_levels.json");
  const mockCards = {
    "learn": {
      "title_en": "Learn item",
      "explanation_en": "Learn item description"
    },
    "practice": {
      "format": "multiple_choice",
      "prompt_en": "What is this?",
      "options": ["Option A", "Option B"],
      "answer_index": 0
    },
    "game": {
      "format": "multiple_choice",
      "prompt_en": "Play game?",
      "options": ["Yes", "No"],
      "answer_index": 0
    }
  };

  fs.writeFileSync(hybridLevelsPath, JSON.stringify({
    "module": 1,
    "module_name_en": "Hindi with German localization block",
    "levels": [
      {
        "level": 100,
        "title_en": "Hybrid block",
        "is_micro_dialogue_level": false,
        "items": [
          {
            "id": "HYBRID-I1",
            "type": "word",
            "target": "Buch", // Spelling is non-Devanagari! But bypassed!
            "gender": "neuter", // Gender is neuter! But allowed!
            "tags": ["lang:german", "gender:neuter", "script:roman", "anchor:interval:30"],
            "cards": mockCards
          },
          {
            "id": "HYBRID-I2",
            "type": "word",
            "target": "Mensch",
            "gender": "common",
            "tags": ["lang:german", "gender:common", "script:roman"],
            "cards": mockCards
          },
          {
            "id": "HYBRID-I3",
            "type": "word",
            "target": "Haus",
            "gender": "neuter",
            "tags": ["lang:german", "gender:neuter", "script:roman"],
            "cards": mockCards
          }
        ],
        "summary": {
          "recap_en": "Bypass recap.",
          "key_forms": ["Buch", "Mensch", "Haus"],
          "next_up_en": "Next up."
        }
      }
    ]
  }, null, 2));

  // Register levels
  const regErrors = validator.registerLevels(hybridLevelsPath);
  assert.strictEqual(regErrors.length, 0, "Should register levels without error");

  // Validate Level File
  const valErrors = validator.validateLevelFile(hybridLevelsPath);
  assert.strictEqual(valErrors.length, 0, "Validator should successfully bypass spelling, read_as, and permitted genders on the expansion level!");
});

console.log("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉");
