import fs from 'fs';
import path from 'path';

export class Validator {
  constructor(profilePathOrLang) {
    this.itemMap = new Map(); // Maps item ID to item data and source file
    this.levelMap = new Map(); // Maps level number to level data and source file
    this.profile = null;
    this.registry = null;

    if (profilePathOrLang) {
      if (typeof profilePathOrLang === 'string') {
        if (profilePathOrLang.endsWith('registry.json')) {
          this.registry = this.loadJSON(profilePathOrLang);
        } else {
          try {
            if (fs.existsSync(profilePathOrLang)) {
              const loaded = this.loadJSON(profilePathOrLang);
              if (loaded.languages) {
                this.registry = loaded;
              } else {
                this.profile = loaded;
              }
            } else {
              const registryPath = '/app/profiles/registry.json';
              this.registry = this.loadJSON(registryPath);
              this.profile = this.getProfileForLanguage(profilePathOrLang);
            }
          } catch (e) {
            try {
              const registryPath = '/app/profiles/registry.json';
              this.registry = this.loadJSON(registryPath);
              this.profile = this.getProfileForLanguage(profilePathOrLang);
            } catch (innerErr) {
              throw new Error(`Failed to initialize Validator: ${profilePathOrLang}. Error: ${e.message}`);
            }
          }
        }
      } else if (typeof profilePathOrLang === 'object') {
        this.profile = profilePathOrLang;
      }
    } else {
      const registryPath = '/app/profiles/registry.json';
      this.registry = this.loadJSON(registryPath);
    }
  }

  loadJSON(filePath) {
    try {
      const data = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(data);
    } catch (e) {
      throw new Error(`Failed to load or parse JSON from ${filePath}: ${e.message}`);
    }
  }

  getProfileForLanguage(langCode) {
    if (!this.registry) {
      const registryPath = '/app/profiles/registry.json';
      this.registry = this.loadJSON(registryPath);
    }
    const cleanCode = langCode.toLowerCase();
    let entry = this.registry.languages[cleanCode];
    if (!entry) {
      entry = Object.values(this.registry.languages).find(l => l.language.toLowerCase() === cleanCode);
    }
    if (!entry) {
      throw new Error(`Language '${langCode}' is not explicitly registered in the unified registry.`);
    }

    const fallbackProfile = {
      language: entry.language || cleanCode,
      iso_code: entry.iso_code || cleanCode,
      permitted_genders: entry.permitted_genders || [],
      active_phonetic_systems: entry.active_phonetic_systems || [],
      script_traits: {
        is_abugida: entry.script_traits?.is_abugida ?? false,
        has_matra: entry.script_traits?.has_matra ?? false,
        has_sound_family: entry.script_traits?.has_sound_family ?? false,
        has_tones: entry.script_traits?.has_tones ?? false,
        has_word_masks: entry.script_traits?.has_word_masks ?? false,
        ...(entry.script_traits || {})
      },
      script_boundaries: entry.script_boundaries || { ranges: [] }
    };
    return fallbackProfile;
  }

  detectLanguage(data) {
    if (!this.registry) {
      const registryPath = '/app/profiles/registry.json';
      this.registry = this.loadJSON(registryPath);
    }

    const strData = JSON.stringify(data);
    for (const [langCode, langObj] of Object.entries(this.registry.languages)) {
      if (data[`module_name_${langCode}`] !== undefined || strData.includes(`title_${langCode}`)) {
        return langCode;
      }
    }

    const charCounts = {};
    for (const langCode of Object.keys(this.registry.languages)) {
      charCounts[langCode] = 0;
    }

    const scanStrings = (val) => {
      if (typeof val === 'string') {
        for (const [langCode, langObj] of Object.entries(this.registry.languages)) {
          const ranges = langObj.script_boundaries?.ranges || [];
          for (const [start, end] of ranges) {
            const startCode = start.codePointAt(0);
            const endCode = end.codePointAt(0);
            for (let i = 0; i < val.length; i++) {
              const code = val.codePointAt(i);
              if (code >= startCode && code <= endCode) {
                const char = String.fromCodePoint(code);
                if (startCode > 0x7F || /^\p{L}$/u.test(char)) {
                  charCounts[langCode]++;
                }
              }
            }
          }
        }
      } else if (Array.isArray(val)) {
        for (const item of val) {
          scanStrings(item);
        }
      } else if (val && typeof val === 'object') {
        for (const value of Object.values(val)) {
          scanStrings(value);
        }
      }
    };

    scanStrings(data);

    const nonLatinLanguages = {};
    const latinLanguages = {};
    for (const [langCode, langObj] of Object.entries(this.registry.languages)) {
      const ranges = langObj.script_boundaries?.ranges || [];
      const hasNonLatinRange = ranges.some(([start, end]) => start.codePointAt(0) > 0x2FF);
      const count = charCounts[langCode] || 0;
      if (hasNonLatinRange) {
        nonLatinLanguages[langCode] = count;
      } else {
        latinLanguages[langCode] = count;
      }
    }

    const hasNonLatinMatch = Object.values(nonLatinLanguages).some(count => count > 0);
    const activeCandidates = hasNonLatinMatch ? nonLatinLanguages : latinLanguages;

    let bestLang = null;
    let maxCount = 0;
    for (const [langCode, count] of Object.entries(activeCandidates)) {
      if (count > maxCount) {
        maxCount = count;
        bestLang = langCode;
      }
    }

    return bestLang;
  }

  validateScriptBoundaries(text, langCode) {
    const profile = this.getProfileForLanguage(langCode);
    const ranges = profile.script_boundaries?.ranges || [];
    if (ranges.length === 0) return;

    for (let i = 0; i < text.length; i++) {
      const code = text.codePointAt(i);
      let allowed = false;
      for (const [start, end] of ranges) {
        const startCode = start.codePointAt(0);
        const endCode = end.codePointAt(0);
        if (code >= startCode && code <= endCode) {
          allowed = true;
          break;
        }
      }

      if (!allowed) {
        const char = String.fromPoint ? String.fromPoint(code) : String.fromCodePoint(code);
        const isLetter = /^\p{L}$/u.test(char);
        if (isLetter) {
          throw new Error(`Script boundary violation: character '${char}' (U+${code.toString(16).toUpperCase()}) in target '${text}' is outside the permitted script boundaries for language '${langCode}'.`);
        }
      }
    }
  }

  // Pre-loads levels so referential integrity can be verified across all files in the module
  registerLevels(levelsFilePath) {
    const data = this.loadJSON(levelsFilePath);
    const levels = data.levels || [];
    const errors = [];

    // Basic levels array check
    if (!Array.isArray(levels)) {
      errors.push({
        file: levelsFilePath,
        message: "The 'levels' field must be an array."
      });
      return errors;
    }

    for (const lvl of levels) {
      const lvlNum = lvl.level;
      if (typeof lvlNum !== 'number') {
        errors.push({
          file: levelsFilePath,
          message: `Level number must be a number, got: ${typeof lvlNum}`
        });
        continue;
      }

      if (this.levelMap.has(lvlNum)) {
        errors.push({
          file: levelsFilePath,
          message: `Duplicate level number found: ${lvlNum}`
        });
      }
      this.levelMap.set(lvlNum, { data: lvl, file: levelsFilePath });

      const items = lvl.items || [];
      if (!Array.isArray(items)) {
        errors.push({
          file: levelsFilePath,
          level: lvlNum,
          message: `The 'items' field in level ${lvlNum} must be an array.`
        });
        continue;
      }

      // Rigid Lesson Counting Limit: exactly three items per level
      if (items.length !== 3) {
        errors.push({
          file: levelsFilePath,
          level: lvlNum,
          message: `Rigid lesson count limit violated in level ${lvlNum}: expected exactly 3 items, found ${items.length}`
        });
      }

      // Check for summary recap
      if (!lvl.summary) {
        errors.push({
          file: levelsFilePath,
          level: lvlNum,
          message: `Level ${lvlNum} is missing a summary recap.`
        });
      } else {
        const sum = lvl.summary;
        if (typeof sum.recap_en !== 'string' || !Array.isArray(sum.key_forms) || typeof sum.next_up_en !== 'string') {
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            message: `Level ${lvlNum} summary recap is invalid: must contain 'recap_en' (string), 'key_forms' (array of strings), and 'next_up_en' (string).`
          });
        }
      }

      for (const item of items) {
        if (!item || typeof item.id !== 'string') {
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            message: `Found an item without a valid string ID in level ${lvlNum}`
          });
          continue;
        }

        if (this.itemMap.has(item.id)) {
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            itemId: item.id,
            message: `Duplicate item ID found: ${item.id}`
          });
        }
        this.itemMap.set(item.id, { data: item, level: lvlNum, file: levelsFilePath });
      }
    }

    return errors;
  }

  validateLevelFile(levelsFilePath) {
    const data = this.loadJSON(levelsFilePath);
    const levels = data.levels || [];
    const errors = [];

    let profile = this.profile;
    let langCode = profile ? (profile.iso_code || profile.language) : null;
    if (!langCode) {
      langCode = this.detectLanguage(data);
    }
    if (!langCode) {
      throw new Error(`Language could not be detected, and none is configured. Failing closed.`);
    }
    profile = this.getProfileForLanguage(langCode);

    for (const lvl of levels) {
      const lvlNum = lvl.level;
      const items = lvl.items || [];

      for (const item of items) {
        if (!item || typeof item.id !== 'string') continue;

        if (item.target) {
          try {
            this.validateScriptBoundaries(item.target, langCode);
          } catch (err) {
            errors.push({
              file: levelsFilePath,
              level: lvlNum,
              itemId: item.id,
              message: err.message
            });
          }
        }

        // Polymorphic schema validations based on Language Profile
        const genders = profile.permitted_genders || [];
        if (item.gender !== null && item.gender !== undefined) {
          if (!genders.includes(item.gender)) {
            errors.push({
              file: levelsFilePath,
              level: lvlNum,
              itemId: item.id,
              message: `Gender '${item.gender}' is not permitted in language '${profile.language}'. Allowed genders: [${genders.join(', ')}]`
            });
          }
        } else if (item.type === 'word' && genders.length > 0 && profile.language === 'hindi') {
          // If the profile mandates noun genders (e.g. Hindi), warn/error if missing
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            itemId: item.id,
            message: `Missing required gender field for Hindi word: '${item.target}'`
          });
        }

        // Script traits checks
        const isAbugida = profile.script_traits?.is_abugida;
        if (item.type === 'letter') {
          if (isAbugida) {
            // For Abugida scripts, fields like 'matra' and 'sound_family' must be defined (can be null but key must exist)
            if (!('matra' in item)) {
              errors.push({
                file: levelsFilePath,
                level: lvlNum,
                itemId: item.id,
                message: `Abugida script requires 'matra' field on letter items, but it was omitted.`
              });
            }
            if (!('sound_family' in item)) {
              errors.push({
                file: levelsFilePath,
                level: lvlNum,
                itemId: item.id,
                message: `Abugida script requires 'sound_family' field on letter items, but it was omitted.`
              });
            }
          }
          // Note: for non-Abugida scripts, the absence of 'matra' or 'sound_family' is perfectly valid and ignored.
        }

        // Validate basic fields of learning/practice/game cards
        if (!item.cards) {
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            itemId: item.id,
            message: `Item ${item.id} is missing 'cards' block.`
          });
          continue;
        }

        const cards = item.cards;
        if (!cards.learn || !cards.practice || !cards.game) {
          errors.push({
            file: levelsFilePath,
            level: lvlNum,
            itemId: item.id,
            message: `Item ${item.id} cards must contain 'learn', 'practice', and 'game' blocks.`
          });
        }

        // Categorization game validations (e.g., sorting game using categorization metadata)
        if (cards.game && (cards.game.format === 'sorting' || cards.game.engine === 'sorting')) {
          const game = cards.game;
          if (!game.categories || !Array.isArray(game.categories)) {
            errors.push({
              file: levelsFilePath,
              level: lvlNum,
              itemId: item.id,
              message: `Sorting game configuration in item ${item.id} is missing 'categories' array.`
            });
          }
          if (!game.items || !Array.isArray(game.items)) {
            errors.push({
              file: levelsFilePath,
              level: lvlNum,
              itemId: item.id,
              message: `Sorting game configuration in item ${item.id} is missing sorted 'items' array.`
            });
          } else {
            for (const gItem of game.items) {
              if (typeof gItem.text !== 'string' || typeof gItem.category !== 'string') {
                errors.push({
                  file: levelsFilePath,
                  level: lvlNum,
                  itemId: item.id,
                  message: `Sorting game item must contain 'text' and 'category' strings.`
                });
              } else if (game.categories && !game.categories.includes(gItem.category)) {
                errors.push({
                  file: levelsFilePath,
                  level: lvlNum,
                  itemId: item.id,
                  message: `Sorting game item category '${gItem.category}' is not listed in 'categories' [${game.categories.join(', ')}]`
                });
              }
            }
          }
        }
      }
    }

    return errors;
  }

  validateCheckpointFile(checkpointFilePath) {
    const data = this.loadJSON(checkpointFilePath);
    const checkpoints = data.checkpoints || [];
    const errors = [];

    for (const cp of checkpoints) {
      const cpNum = cp.checkpoint;
      const questions = cp.questions || [];

      if (!Array.isArray(questions)) {
        errors.push({
          file: checkpointFilePath,
          checkpoint: cpNum,
          message: `The 'questions' field in checkpoint ${cpNum} must be an array.`
        });
        continue;
      }

      for (const q of questions) {
        if (!q || typeof q.id !== 'string') {
          errors.push({
            file: checkpointFilePath,
            checkpoint: cpNum,
            message: `Checkpoint ${cpNum} has a question missing a valid string ID.`
          });
          continue;
        }

        // Referential Integrity check: All checkpoint questions must map back to source items
        const sourceIds = q.source_item_ids || [];
        if (!Array.isArray(sourceIds) || sourceIds.length === 0) {
          errors.push({
            file: checkpointFilePath,
            checkpoint: cpNum,
            questionId: q.id,
            message: `Question ${q.id} in checkpoint ${cpNum} must have non-empty 'source_item_ids' array.`
          });
        } else {
          for (const sId of sourceIds) {
            if (!this.itemMap.has(sId)) {
              errors.push({
                file: checkpointFilePath,
                checkpoint: cpNum,
                questionId: q.id,
                message: `Referential Integrity violation: Question ${q.id} references non-existent source level item '${sId}'`
              });
            }
          }
        }
      }
    }

    return errors;
  }

  validateMockFile(mockFilePath) {
    const data = this.loadJSON(mockFilePath);
    const errors = [];
    const mockExam = data.mock_exam || data; // Mock exams can have nested or direct mock_exam block
    const questions = mockExam.questions || [];

    if (!Array.isArray(questions)) {
      errors.push({
        file: mockFilePath,
        message: "Mock exam must have an array of 'questions'."
      });
      return errors;
    }

    for (const q of questions) {
      if (!q || typeof q.id !== 'string') {
        errors.push({
          file: mockFilePath,
          message: "Mock exam has a question missing a valid string ID."
        });
        continue;
      }

      // Referential Integrity check: All mock exam questions must map back to source items
      const sourceIds = q.source_item_ids || [];
      if (!Array.isArray(sourceIds) || sourceIds.length === 0) {
        errors.push({
          file: mockFilePath,
          questionId: q.id,
          message: `Question ${q.id} in mock exam must have non-empty 'source_item_ids' array.`
        });
      } else {
        for (const sId of sourceIds) {
          if (!this.itemMap.has(sId)) {
            errors.push({
              file: mockFilePath,
              questionId: q.id,
              message: `Referential Integrity violation: Mock exam question ${q.id} references non-existent source level item '${sId}'`
            });
          }
        }
      }
    }

    return errors;
  }

  validateSpineFile(spineFilePath) {
    const data = this.loadJSON(spineFilePath);
    const errors = [];
    const spineItems = data.spine || [];

    if (!Array.isArray(spineItems)) {
      errors.push({
        file: spineFilePath,
        message: "Spine file must contain an array of spine items under 'spine'."
      });
      return errors;
    }

    let profile = this.profile;
    let langCode = profile ? (profile.iso_code || profile.language) : null;
    if (!langCode) {
      langCode = this.detectLanguage(data);
    }

    for (const sItem of spineItems) {
      if (!sItem || typeof sItem.id !== 'string') {
        errors.push({
          file: spineFilePath,
          message: "Spine entry is missing a valid string ID."
        });
        continue;
      }

      if (sItem.target && langCode) {
        try {
          this.validateScriptBoundaries(sItem.target, langCode);
        } catch (err) {
          errors.push({
            file: spineFilePath,
            itemId: sItem.id,
            message: err.message
          });
        }
      }

      // Referential Integrity with level files
      if (!this.itemMap.has(sItem.id)) {
        // If it's a partial spine (like module 9 with levels missing), check if the level is marked as missing
        const isMissingLevel = data.levels_missing?.includes(sItem.level);
        if (!isMissingLevel) {
          errors.push({
            file: spineFilePath,
            itemId: sItem.id,
            message: `Referential Integrity violation: Spine item '${sItem.id}' references level ${sItem.level} but does not exist in any registered level files.`
          });
        }
        continue;
      }

      const registeredItem = this.itemMap.get(sItem.id).data;
      const registeredLvl = this.itemMap.get(sItem.id).level;

      // Validate corresponding attributes
      if (sItem.level !== registeredLvl) {
        errors.push({
          file: spineFilePath,
          itemId: sItem.id,
          message: `Spine item '${sItem.id}' level (${sItem.level}) does not match levels file level (${registeredLvl})`
        });
      }

      if (sItem.type && sItem.type !== registeredItem.type) {
        errors.push({
          file: spineFilePath,
          itemId: sItem.id,
          message: `Spine item '${sItem.id}' type (${sItem.type}) does not match levels file type (${registeredItem.type})`
        });
      }

      if (sItem.target && sItem.target !== registeredItem.target) {
        errors.push({
          file: spineFilePath,
          itemId: sItem.id,
          message: `Spine item '${sItem.id}' target (${sItem.target}) does not match levels file target (${registeredItem.target})`
        });
      }

      if (sItem.gender !== undefined && sItem.gender !== registeredItem.gender) {
        errors.push({
          file: spineFilePath,
          itemId: sItem.id,
          message: `Spine item '${sItem.id}' gender (${sItem.gender}) does not match levels file gender (${registeredItem.gender})`
        });
      }
    }

    return errors;
  }
}
