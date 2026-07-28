import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Validator } from '../src/validator.js';
import { Player } from '../src/player.js';

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

// 6. Unified Registry and Script Boundary validation tests
runTest("Rejects validation requests for unregistered languages in JS", () => {
  const validator = new Validator();
  assert.throws(() => {
    validator.getProfileForLanguage("unsupported_language");
  }, /not explicitly registered/);
});

runTest("Enforces script boundaries and fails closed on invalid characters in JS", () => {
  const validator = new Validator("es");
  
  const invalidSpanishLevels = path.join(tempDir, 'invalid_spanish_levels.json');
  fs.writeFileSync(invalidSpanishLevels, JSON.stringify({
    "module": 1,
    "module_name_es": "Spanish",
    "levels": [
      {
        "level": 1,
        "items": [
          {
            "id": "ES-L01-I1",
            "type": "vocabulary",
            "target": "hola తె", // Telugu char, invalid in Spanish!
            "cards": { "learn": {}, "practice": {}, "game": {} }
          },
          { "id": "ES-L01-I2", "cards": { "learn": {}, "practice": {}, "game": {} } },
          { "id": "ES-L01-I3", "cards": { "learn": {}, "practice": {}, "game": {} } }
        ],
        "summary": { "recap_en": "Recap", "key_forms": [], "next_up_en": "Next" }
      }
    ]
  }, null, 2));

  const valErrors = validator.validateLevelFile(invalidSpanishLevels);
  assert.ok(valErrors.length > 0, "Should have validation errors due to script boundary violation");
  assert.ok(valErrors[0].message.includes("Script boundary violation"), "Error message should mention script boundary violation");
});

console.log("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉");
