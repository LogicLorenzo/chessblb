class ChessClock {
  /**
   * @param {number} initialSeconds  Starting time per player (in seconds)
   * @param {number} incrementSeconds  Seconds to add after each move
   * @param {(color: 'white'|'black', timeLeft: number)=>void} onTick  Called every second
   * @param {(flaggedColor: 'white'|'black')=>void} onFlag  Called when a player’s time runs out
   */
  constructor(initialSeconds, incrementSeconds = 0, onTick = ()=>{}, onFlag = ()=>{}) {
    this.initial  = initialSeconds;
    this.increment = incrementSeconds;
    this.times    = { white: initialSeconds, black: initialSeconds };
    this.onTick   = onTick;
    this.onFlag   = onFlag;

    this.current  = null;     // 'white' or 'black'
    this._timerId = null;
  }

  // Start (or resume) the clock for `color`
  start(color) {
    this.stop();              // clear any existing timer
    this.current = color;
    this._timerId = setInterval(() => {
      this.times[color]--;
      this.onTick(color, this.times[color]);
      if (this.times[color] <= 0) {
        this.stop();
        this.onFlag(color);
      }
    }, 1000);
  }

  // Switch sides (call this after a move)
  switch() {
    if (!this.current) return;
    // award increment
    this.times[this.current] += this.increment;
    // start the opponent
    const next = this.current === 'white' ? 'black' : 'white';
    this.start(next);
  }

  // Pause/stop the current timer
  stop() {
    if (this._timerId !== null) {
      clearInterval(this._timerId);
      this._timerId = null;
    }
  }


  // Reset both clocks to the initial time
  reset() {
    this.stop();
    this.times.white = this.times.black = this.initial;
    this.current = null;
  }

  // Get remaining time for a color
  timeLeft(color) {
    return this.times[color];
  }
}

function formatTime(sec) {
  const m = Math.floor(sec/60).toString().padStart(2,'0');
  const s = (sec % 60).toString().padStart(2,'0');
  return `${m}:${s}`;
}
