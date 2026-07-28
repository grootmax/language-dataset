export class SpacedRetrievalEngine {
  constructor() {}

  // Parse tag anchors on items to adjust review intervals dynamically
  parseAnchors(item) {
    const anchors = {};
    if (!item || !Array.isArray(item.tags)) return anchors;

    for (const tag of item.tags) {
      if (typeof tag === 'string') {
        const lowerTag = tag.toLowerCase().trim();
        // Look for anchor tags of form:
        // "anchor:multiplier:1.5" -> multiplier = 1.5
        // "anchor:interval:10" -> base_interval = 10
        // "anchor:weight:1.2" -> weight = 1.2
        // "anchor:review_interval:5" -> review_interval = 5
        // "anchor:review_interval_multiplier:2.0" -> multiplier = 2.0
        // "anchor:ease:2.8" -> ease = 2.8
        if (lowerTag.startsWith('anchor:')) {
          const parts = tag.split(':');
          if (parts.length >= 2) {
            const key = parts[1].trim().toLowerCase();
            const valStr = parts.slice(2).join(':').trim();
            const valNum = parseFloat(valStr);
            anchors[key] = !isNaN(valNum) ? valNum : valStr;
          }
        }
      }
    }
    return anchors;
  }

  // Dynamically schedule next review session based on current state and parsed tag anchors
  scheduleNextReview(item, currentState = {}, quality = 5) {
    const anchors = this.parseAnchors(item);
    
    // Default values for SM-2 like spaced retrieval
    let repetitions = currentState.repetitions || 0;
    let interval = currentState.interval || 1; // in days
    let easeFactor = currentState.easeFactor || 2.5;

    // Adjust easeFactor and interval based on user response quality (0-5)
    if (quality >= 3) {
      if (repetitions === 0) {
        interval = 1;
      } else if (repetitions === 1) {
        interval = 6;
      } else {
        interval = Math.round(interval * easeFactor);
      }
      repetitions++;
    } else {
      repetitions = 0;
      interval = 1;
    }

    // Apply User quality ease factor adjustments
    easeFactor = easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
    if (easeFactor < 1.3) easeFactor = 1.3;

    // Apply parsed custom tag anchors dynamically to adjust review intervals/ease
    // 1. interval multiplier anchor: "anchor:multiplier:1.5" or "anchor:review_interval_multiplier:1.5"
    const multiplier = anchors.multiplier || anchors.review_interval_multiplier || anchors.weight || 1.0;
    interval = Math.round(interval * multiplier);

    // 2. fixed base interval override: "anchor:interval:10" or "anchor:review_interval:10"
    const fixedInterval = anchors.interval || anchors.review_interval;
    if (fixedInterval !== undefined && typeof fixedInterval === 'number') {
      interval = fixedInterval;
    }

    // 3. custom ease factor adjustment: "anchor:ease:2.8" or "anchor:ease_factor:2.8"
    const fixedEase = anchors.ease || anchors.ease_factor;
    if (fixedEase !== undefined && typeof fixedEase === 'number') {
      easeFactor = fixedEase;
    }

    return {
      repetitions,
      interval,
      easeFactor,
      nextReviewDate: new Date(Date.now() + interval * 24 * 60 * 60 * 1000)
    };
  }
}
