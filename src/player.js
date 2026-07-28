export class Player {
  constructor(gameConfig) {
    if (!gameConfig) {
      throw new Error("Game configuration is required to initialize Player.");
    }
    this.config = gameConfig;
    this.engine = gameConfig.engine || gameConfig.format || 'unknown';
    this.state = null;
    this.gameplayModifiers = this._parseGameplayTags(gameConfig.tags || []);
  }

  _parseGameplayTags(tags) {
    const modifiers = {};
    if (!Array.isArray(tags)) return modifiers;
    for (const tag of tags) {
      if (typeof tag === 'string') {
        const lowerTag = tag.toLowerCase().trim();
        // Look for gameplay modifiers:
        // "gameplay:difficulty:hard"
        // "gameplay:timer:30"
        // "gameplay:options_count:5"
        // "gameplay:theme:sepia"
        if (lowerTag.startsWith('gameplay:')) {
          const parts = tag.split(':');
          if (parts.length >= 2) {
            const key = parts[1].trim().toLowerCase();
            const valStr = parts.slice(2).join(':').trim();
            const valNum = parseFloat(valStr);
            modifiers[key] = !isNaN(valNum) ? valNum : valStr;
          }
        }
      }
    }
    return modifiers;
  }

  instantiate() {
    // Standardize custom formats to core engines
    let normalizedEngine = this.engine;
    if (normalizedEngine === 'gender_sort' || normalizedEngine === 'category_sort' || normalizedEngine === 'odd_sound_out') {
      normalizedEngine = 'sorting';
    } else if (normalizedEngine === 'collocation_match') {
      normalizedEngine = 'matching';
    }

    switch (normalizedEngine) {
      case 'sorting':
        this.state = this._initSortingEngine();
        break;
      case 'matching':
        this.state = this._initMatchingEngine();
        break;
      case 'matching_pairs':
        this.state = this._initMatchingPairsEngine();
        break;
      default:
        // Graceful fallback for any unknown/custom game format
        this.state = this._initGenericEngine();
        break;
    }

    // Apply parsed tag parameters to gameplay properties at runtime
    if (this.gameplayModifiers.difficulty) {
      this.state.difficulty = this.gameplayModifiers.difficulty;
    }
    if (this.gameplayModifiers.timer !== undefined) {
      this.state.timer = this.gameplayModifiers.timer;
    }
    if (this.gameplayModifiers.theme) {
      this.state.theme = this.gameplayModifiers.theme;
    }
    if (this.gameplayModifiers.options_count && Array.isArray(this.state.items)) {
      this.state.items = this.state.items.slice(0, this.gameplayModifiers.options_count);
    }

    return this.state;
  }

  _initSortingEngine() {
    const categories = this.config.categories || [];
    const items = this.config.items || [];

    // Fallback: If no explicit sorting categories/items exist, try to derive them from other standard fields
    let derivedCategories = [...categories];
    let derivedItems = [...items];

    if (derivedCategories.length === 0) {
      // e.g. for Hindi gender_sort we might derive categories based on options
      if (this.config.options) {
        derivedCategories = this.config.options;
      } else {
        derivedCategories = ['Category A', 'Category B'];
      }
    }

    if (derivedItems.length === 0) {
      if (this.config.question) {
        derivedItems = [{ text: this.config.question, category: derivedCategories[0] }];
      } else if (this.config.options) {
        derivedItems = this.config.options.map((opt, idx) => ({
          text: opt,
          category: derivedCategories[idx % derivedCategories.length]
        }));
      }
    }

    return {
      engine: 'sorting',
      title: this.config.question_en || this.config.prompt_en || 'Sort the items',
      categories: derivedCategories,
      items: derivedItems.map((item, idx) => ({
        id: `sort-item-${idx}`,
        text: typeof item === 'string' ? item : item.text,
        category: typeof item === 'string' ? derivedCategories[0] : item.category
      })),
      score: 0,
      completed: false
    };
  }

  _initMatchingEngine() {
    const leftItems = this.config.left || this.config.options || [];
    const rightItems = this.config.right || this.config.options_read_as || [];

    return {
      engine: 'matching',
      title: this.config.question_en || this.config.prompt_en || 'Match the pairs',
      pairs: leftItems.map((left, idx) => ({
        id: `match-pair-${idx}`,
        left: left,
        right: rightItems[idx] || ''
      })),
      score: 0,
      completed: false
    };
  }

  _initMatchingPairsEngine() {
    const items = this.config.items || this.config.options || [];

    return {
      engine: 'matching_pairs',
      title: this.config.question_en || this.config.prompt_en || 'Match identical pairs',
      cards: [...items, ...items].map((item, idx) => ({
        id: `card-${idx}`,
        value: typeof item === 'string' ? item : (item.text || item.hindi || ''),
        isFlipped: false,
        isMatched: false
      })),
      score: 0,
      completed: false
    };
  }

  _initGenericEngine() {
    return {
      engine: 'generic',
      title: this.config.question_en || this.config.prompt_en || 'Complete the task',
      config: this.config,
      score: 0,
      completed: false
    };
  }

  render() {
    if (!this.state) {
      this.instantiate();
    }

    // Return a structured view model of the active game engine state
    return {
      engine: this.state.engine,
      title: this.state.title,
      viewData: { ...this.state },
      html: this._generateHTML()
    };
  }

  _generateHTML() {
    // Generate a simple and safe mockup of HTML for rendering/testing the game player UI
    let content = '';
    const themeClass = this.state.theme ? ` theme-${this.state.theme}` : '';
    const timerHtml = this.state.timer !== undefined ? `<div class="game-timer">Time: ${this.state.timer}s</div>` : '';

    if (this.state.engine === 'sorting') {
      content = `
        <div class="sorting-game${themeClass}">
          ${timerHtml}
          <h2>${this.state.title}</h2>
          <div class="buckets">
            ${this.state.categories.map(cat => `<div class="bucket" data-category="${cat}">${cat}</div>`).join('')}
          </div>
          <div class="items">
            ${this.state.items.map(item => `<div class="draggable" data-id="${item.id}">${item.text}</div>`).join('')}
          </div>
        </div>
      `;
    } else if (this.state.engine === 'matching') {
      content = `
        <div class="matching-game${themeClass}">
          ${timerHtml}
          <h2>${this.state.title}</h2>
          <div class="left-col">
            ${this.state.pairs.map(pair => `<div class="match-left" data-id="${pair.id}">${pair.left}</div>`).join('')}
          </div>
          <div class="right-col">
            ${this.state.pairs.map(pair => `<div class="match-right" data-id="${pair.id}">${pair.right}</div>`).join('')}
          </div>
        </div>
      `;
    } else {
      content = `
        <div class="generic-game${themeClass}">
          ${timerHtml}
          <h2>${this.state.title}</h2>
        </div>
      `;
    }
    return content.trim();
  }

  submitSortAction(itemId, targetCategory) {
    if (this.state.engine !== 'sorting') {
      throw new Error("Action only valid for sorting engine");
    }
    const item = this.state.items.find(i => i.id === itemId);
    if (!item) return false;

    const isCorrect = item.category === targetCategory;
    if (isCorrect) {
      this.state.score += 10;
    }
    return isCorrect;
  }
}
